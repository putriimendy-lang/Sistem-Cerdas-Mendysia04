import math
import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

from .models import CatatanMakan, RiwayatKlasifikasi
from .services.ai_service import tanya_ai
from .services.nutrition_service import build_food_catalog, recommend_lower_calorie_foods


# ========================================
# 1. PENGATURAN LOKASI MODEL DAN DATASET
# ========================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml_model" / "decision_tree_model_tkpi.joblib"
DATASET_PATH = BASE_DIR / "dataset" / "tkpi_2017_bersih.csv"
FOOD_NAME_MAPPING_PATH = BASE_DIR / "dataset" / "tkpi_nama_makanan.csv"

LABEL_KELAS = ["Rendah", "Sedang", "Tinggi"]


# ========================================
# 2. MEMUAT MODEL DAN DATASET (SEKALI SAJA)
# ========================================

model_data = joblib.load(MODEL_PATH)

model = model_data["model"]
fitur = model_data["features"]

DF = pd.read_csv(DATASET_PATH)


def _urutkan_input(karbohidrat, protein, lemak):
    """
    Susun input sesuai urutan kolom `fitur` milik model,
    apa pun urutannya, supaya nilai tidak tertukar.
    """
    nilai = []
    for kolom in fitur:
        nama = str(kolom).lower()
        if "carb" in nama or "karbo" in nama:
            nilai.append(karbohidrat)
        elif "prot" in nama:
            nilai.append(protein)
        elif "fat" in nama or "lemak" in nama:
            nilai.append(lemak)
        else:
            return [karbohidrat, protein, lemak]
    return nilai


# ========================================
# 3. EVALUASI MODEL (DIHITUNG SEKALI, DI-CACHE)
# ========================================

@lru_cache(maxsize=1)
def hitung_evaluasi():
    df = DF.copy()

    df["Energy"] = pd.to_numeric(df["Energy"], errors="coerce")
    df = df.dropna(subset=["Energy"])

    X = df[fitur].apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median())

    y = pd.qcut(df["Energy"], q=3, labels=LABEL_KELAS)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    prediksi = model.predict(X_test)

    akurasi = round(accuracy_score(y_test, prediksi) * 100, 2)

    laporan = classification_report(
        y_test,
        prediksi,
        labels=LABEL_KELAS,
        output_dict=True,
        zero_division=0,
    )

    hasil_per_kelas = []
    for kelas in LABEL_KELAS:
        hasil_per_kelas.append({
            "nama": kelas,
            "precision": round(laporan[kelas]["precision"] * 100, 2),
            "recall": round(laporan[kelas]["recall"] * 100, 2),
            "f1_score": round(laporan[kelas]["f1-score"] * 100, 2),
            "support": int(laporan[kelas]["support"]),
        })

    matriks = confusion_matrix(y_test, prediksi, labels=LABEL_KELAS)

    return {
        "akurasi": akurasi,
        "total_data_latih": len(X_train),
        "total_data_uji": len(X_test),
        "hasil_per_kelas": hasil_per_kelas,
        "label_kelas": LABEL_KELAS,
        "matriks_konfusi": matriks.tolist(),
    }


# ========================================
# 4. HALAMAN BERANDA
# ========================================

def beranda(request):
    context = {
        "total_data": len(DF),
        "akurasi": hitung_evaluasi()["akurasi"],
    }
    return render(request, "beranda.html", context)


def about(request):
    return render(request, "about.html", {"total_data": len(DF)})


# ========================================
# 5. HALAMAN KLASIFIKASI KALORI
# ========================================

def klasifikasi(request):
    hasil = None
    error = None
    input_user = {}

    if request.method == "POST":
        try:
            karbohidrat = float(request.POST.get("karbohidrat", ""))
            protein = float(request.POST.get("protein", ""))
            lemak = float(request.POST.get("lemak", ""))
        except (ValueError, TypeError):
            error = "Isi semua kolom dengan angka yang valid."
        else:
            if not all(math.isfinite(n) for n in (karbohidrat, protein, lemak)):
                error = "Nilai nutrisi tidak valid."
            elif min(karbohidrat, protein, lemak) < 0:
                error = "Nilai nutrisi tidak boleh negatif."
            else:
                data_baru = pd.DataFrame(
                    [_urutkan_input(karbohidrat, protein, lemak)],
                    columns=fitur,
                )

                hasil = str(model.predict(data_baru)[0])
                estimasi_kalori = round(
                    (4 * karbohidrat) + (4 * protein) + (9 * lemak),
                    2,
                )

                RiwayatKlasifikasi.objects.create(
                    karbohidrat=karbohidrat,
                    protein=protein,
                    lemak=lemak,
                    kategori=hasil,
                )

                input_user = {
                    "karbohidrat": karbohidrat,
                    "protein": protein,
                    "lemak": lemak,
                }

    return render(
        request,
        "klasifikasi.html",
        {
            "hasil": hasil,
            "error": error,
            "input": input_user,
            "estimasi_kalori": estimasi_kalori if hasil else None,
            "riwayat": RiwayatKlasifikasi.objects.all()[:10],
        },
    )


# ========================================
# 6. HALAMAN VISUALISASI DATA (2 GRAFIK)
# ========================================

def visualisasi(request):
    data_energi = pd.to_numeric(DF["Energy"], errors="coerce").dropna()
    kolom_makronutrien = {
        "Karbohidrat": "Carbohydrate",
        "Protein": "Protein",
        "Lemak": "Fat",
    }
    rata_rata_makronutrien = []
    for kolom in kolom_makronutrien.values():
        nilai = pd.to_numeric(DF[kolom], errors="coerce").dropna()
        rata_rata_makronutrien.append(
            round(float(nilai.mean()), 2) if not nilai.empty else 0
        )

    if data_energi.empty:
        context = {
            "total_data": len(DF),
            "rata_rata_kalori": 0,
            "label_kategori": LABEL_KELAS,
            "rata_rata_kategori": [0, 0, 0],
            "label_makronutrien": list(kolom_makronutrien),
            "rata_rata_makronutrien": rata_rata_makronutrien,
            "label_histogram": [],
            "jumlah_histogram": [],
        }
        return render(request, "visualisasi.html", context)

    # A. KATEGORI KALORI
    kategori = pd.qcut(data_energi, q=3, labels=LABEL_KELAS)
    rata_rata_kategori = [
        round(float(data_energi[kategori == kelas].mean()), 2)
        for kelas in LABEL_KELAS
    ]

    # B. HISTOGRAM SEBARAN ENERGI
    interval_histogram = pd.cut(data_energi, bins=10, include_lowest=True)
    jumlah_histogram = interval_histogram.value_counts().sort_index()

    label_histogram = [
        f"{interval.left:.0f} - {interval.right:.0f}"
        for interval in jumlah_histogram.index
    ]
    nilai_histogram = [int(n) for n in jumlah_histogram.values]

    context = {
        "total_data": len(DF),
        "rata_rata_kalori": round(data_energi.mean(), 2),
        "label_kategori": LABEL_KELAS,
        "rata_rata_kategori": rata_rata_kategori,
        "label_makronutrien": list(kolom_makronutrien),
        "rata_rata_makronutrien": rata_rata_makronutrien,
        "label_histogram": label_histogram,
        "jumlah_histogram": nilai_histogram,
    }

    return render(request, "visualisasi.html", context)


# ========================================
# 7. HALAMAN EVALUASI MODEL
# ========================================

def evaluasi_model(request):
    return render(request, "evaluasi_model.html", hitung_evaluasi())


# ========================================
# 8. HALAMAN ASISTEN AI (GAYA CHAT)
# ========================================

def _inline(teks):
    """Ubah **tebal** dan *miring* menjadi tag HTML (teks sudah di-escape)."""
    teks = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", teks)
    teks = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", teks)
    return teks


def format_jawaban(teks):
    """
    Ubah jawaban AI (markdown sederhana) menjadi HTML rapi.
    Teks di-escape dulu, jadi aman dari injeksi HTML/script.
    """
    hasil = []
    list_aktif = None

    def tutup_list():
        nonlocal list_aktif
        if list_aktif:
            hasil.append(f"</{list_aktif}>")
            list_aktif = None

    for baris in escape(str(teks)).splitlines():
        baris = baris.strip()

        if not baris:
            tutup_list()
            continue

        m_judul = re.match(r"^#{1,6}\s+(.*)", baris)
        m_ul = re.match(r"^[-*•]\s+(.*)", baris)
        m_ol = re.match(r"^\d+[.)]\s+(.*)", baris)

        if m_judul:
            tutup_list()
            hasil.append(f"<h4>{_inline(m_judul.group(1))}</h4>")
        elif m_ul:
            if list_aktif != "ul":
                tutup_list()
                hasil.append("<ul>")
                list_aktif = "ul"
            hasil.append(f"<li>{_inline(m_ul.group(1))}</li>")
        elif m_ol:
            if list_aktif != "ol":
                tutup_list()
                hasil.append("<ol>")
                list_aktif = "ol"
            hasil.append(f"<li>{_inline(m_ol.group(1))}</li>")
        else:
            tutup_list()
            hasil.append(f"<p>{_inline(baris)}</p>")

    tutup_list()
    return mark_safe("".join(hasil))


SARAN_PERTANYAAN = [
    "Apa perbedaan kalori rendah, sedang, dan tinggi?",
    "Mengapa lemak punya kalori paling besar?",
    "Bagaimana cara menghitung kalori dari karbohidrat, protein, dan lemak?",
    "Makanan apa yang rendah kalori tapi mengenyangkan?",
    "Berapa kebutuhan kalori harian orang dewasa?",
]


def asisten_ai(request):
    chat = request.session.get("chat", [])

    if request.method == "POST":
        if request.POST.get("aksi") == "hapus":
            request.session["chat"] = []
            return redirect("asisten_ai")

        pertanyaan = request.POST.get("pertanyaan", "").strip()[:500]

        if pertanyaan:
            try:
                jawaban = str(tanya_ai(pertanyaan))
            except Exception:
                jawaban = (
                    "Maaf, asisten AI sedang tidak tersedia. "
                    "Silakan coba lagi nanti."
                )

            chat.append({"role": "user", "text": pertanyaan})
            chat.append({"role": "ai", "text": jawaban})
            request.session["chat"] = chat[-20:]

        return redirect("asisten_ai")

    return render(
        request,
        "asisten_ai.html",
        {
            "chat": [
                {
                    "role": p["role"],
                    "text": p["text"],
                    "html": format_jawaban(p["text"]) if p["role"] == "ai" else "",
                }
                for p in chat
            ],
            "saran": SARAN_PERTANYAAN,
        },
    )


# ========================================
# 9. HALAMAN RIWAYAT
# ========================================

def riwayat(request):
    riwayat_klasifikasi = Paginator(
        RiwayatKlasifikasi.objects.all(),
        10,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "riwayat.html",
        {"riwayat": riwayat_klasifikasi},
    )


def daftar_makanan(request):
    semua_makanan, nama_tersedia = build_food_catalog(DF, FOOD_NAME_MAPPING_PATH)
    makanan = semua_makanan
    pencarian = request.GET.get("q", "").strip()
    kategori = request.GET.get("kategori", "").strip()

    if pencarian:
        pencarian_lower = pencarian.casefold()
        makanan = [
            item
            for item in makanan
            if pencarian_lower in item["KODE"].casefold()
            or pencarian_lower in item["nama_makanan"].casefold()
        ]
    if kategori in LABEL_KELAS:
        makanan = [item for item in makanan if item["kategori"] == kategori]
    else:
        kategori = ""

    jumlah_makanan = len(makanan)
    kode_rekomendasi = request.GET.get("rekomendasi", "").strip()
    makanan_pilihan, rekomendasi = recommend_lower_calorie_foods(
        kode_rekomendasi,
        semua_makanan,
    ) if kode_rekomendasi else (None, [])
    halaman = Paginator(makanan, 8).get_page(request.GET.get("page"))

    return render(
        request,
        "daftar_makanan.html",
        {
            "makanan": halaman,
            "halaman": halaman,
            "pencarian": pencarian,
            "kategori_terpilih": kategori,
            "nama_tersedia": nama_tersedia,
            "makanan_pilihan": makanan_pilihan,
            "rekomendasi": rekomendasi,
            "kode_rekomendasi": kode_rekomendasi,
            "jumlah_makanan": jumlah_makanan,
            "kategori_kalori": LABEL_KELAS,
        },
    )


def _session_key(request):
    if request.session.session_key is None:
        request.session.create()
    return request.session.session_key


def _parse_tanggal(value):
    if not value:
        return timezone.localdate()
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def catatan_makan(request):
    session_key = _session_key(request)
    tanggal = _parse_tanggal(
        request.POST.get("tanggal") if request.method == "POST"
        else request.GET.get("tanggal")
    )
    error = None

    if tanggal is None:
        tanggal = timezone.localdate()
        error = "Tanggal tidak valid."

    makanan, nama_tersedia = build_food_catalog(DF, FOOD_NAME_MAPPING_PATH)
    makanan_per_kode = {item["KODE"]: item for item in makanan}

    if request.method == "POST" and error is None:
        action = request.POST.get("action")
        if action == "delete":
            try:
                entry_id = int(request.POST.get("entry_id", ""))
            except (TypeError, ValueError):
                error = "Catatan yang dipilih tidak valid."
            else:
                terhapus, _ = CatatanMakan.objects.filter(
                    pk=entry_id,
                    session_key=session_key,
                    tanggal=tanggal,
                ).delete()
                if terhapus:
                    return redirect(
                        f"{reverse('catatan_makan')}?tanggal={tanggal.isoformat()}"
                    )
                error = "Catatan tidak ditemukan pada sesi dan tanggal tersebut."

        if action != "delete":
            kode = request.POST.get("food_code", "").strip()
            item = makanan_per_kode.get(kode)
            try:
                porsi = float(request.POST.get("portion_grams", ""))
            except (TypeError, ValueError):
                porsi = 0

            if item is None:
                error = "Pilih makanan yang tersedia."
            elif not math.isfinite(porsi) or not 0 < porsi <= 5000:
                error = "Porsi harus lebih dari 0 dan tidak lebih dari 5000 gram."
            else:
                energi = float(item["Energy"]) * porsi / 100
                CatatanMakan.objects.create(
                    session_key=session_key,
                    food_code=kode,
                    portion_grams=porsi,
                    energy_kcal=round(energi, 2),
                    tanggal=tanggal,
                )
                return redirect(
                    f"{reverse('catatan_makan')}?tanggal={tanggal.isoformat()}"
                )

    entri = list(
        CatatanMakan.objects.filter(
            session_key=session_key,
            tanggal=tanggal,
        )
    )
    total_kalori = round(sum(item.energy_kcal for item in entri), 2)
    for item in entri:
        data_makanan = makanan_per_kode.get(item.food_code)
        item.nama_makanan = (
            data_makanan["nama_makanan"] if data_makanan else item.food_code
        )

    hari_ini = timezone.localdate()
    hari_mulai = hari_ini - timedelta(days=6)
    entri_7_hari = CatatanMakan.objects.filter(
        session_key=session_key,
        tanggal__range=(hari_mulai, hari_ini),
    )
    total_per_hari = {hari: 0.0 for hari in (
        hari_mulai + timedelta(days=offset) for offset in range(7)
    )}
    for item in entri_7_hari:
        total_per_hari[item.tanggal] += item.energy_kcal

    target_kalori = request.session.get("daily_calorie_target")
    kalori_tersisa = (
        round(float(target_kalori) - total_kalori, 2)
        if target_kalori is not None
        else None
    )

    return render(
        request,
        "catatan_makan.html",
        {
            "makanan": makanan,
            "nama_tersedia": nama_tersedia,
            "tanggal": tanggal.isoformat(),
            "entri": entri,
            "total_kalori": total_kalori,
            "target_kalori": target_kalori,
            "kalori_tersisa": kalori_tersisa,
            "error": error,
            "kode_awal": (
                request.POST.get("food_code", "")
                if request.method == "POST"
                else request.GET.get("food", "")
            ),
            "label_harian": [hari.strftime("%d %b") for hari in total_per_hari],
            "kalori_harian": [
                round(nilai, 2) for nilai in total_per_hari.values()
            ],
        },
    )


TINGKAT_AKTIVITAS = {
    "sedentary": ("Minim aktivitas", 1.2),
    "light": ("Aktivitas ringan (1–3 hari/minggu)", 1.375),
    "moderate": ("Aktivitas sedang (3–5 hari/minggu)", 1.55),
    "active": ("Aktif (6–7 hari/minggu)", 1.725),
    "very_active": ("Sangat aktif", 1.9),
}


def kebutuhan_kalori(request):
    hasil = None
    error = None
    nilai_form = {}

    if request.method == "POST":
        nilai_form = {
            "jenis_kelamin": request.POST.get("jenis_kelamin", ""),
            "usia": request.POST.get("usia", ""),
            "berat": request.POST.get("berat", ""),
            "tinggi": request.POST.get("tinggi", ""),
            "aktivitas": request.POST.get("aktivitas", ""),
        }
        try:
            usia = int(nilai_form["usia"])
            berat = float(nilai_form["berat"])
            tinggi = float(nilai_form["tinggi"])
        except (TypeError, ValueError):
            error = "Isi usia, berat, dan tinggi dengan angka yang valid."
        else:
            aktivitas = TINGKAT_AKTIVITAS.get(nilai_form["aktivitas"])
            if nilai_form["jenis_kelamin"] not in {"pria", "wanita"}:
                error = "Pilih jenis kelamin."
            elif aktivitas is None:
                error = "Pilih tingkat aktivitas yang tersedia."
            elif not all(math.isfinite(value) for value in (berat, tinggi)):
                error = "Berat dan tinggi harus berupa angka yang valid."
            elif not 15 <= usia <= 120 or not 20 <= berat <= 400 or not 100 <= tinggi <= 250:
                error = "Periksa kembali usia, berat, dan tinggi yang dimasukkan."
            else:
                penyesuaian = 5 if nilai_form["jenis_kelamin"] == "pria" else -161
                bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) + penyesuaian
                kebutuhan = round(bmr * aktivitas[1])
                hasil = {
                    "bmr": round(bmr),
                    "kebutuhan": kebutuhan,
                    "aktivitas_label": aktivitas[0],
                }
                request.session["daily_calorie_target"] = kebutuhan

    return render(
        request,
        "kebutuhan_kalori.html",
        {
            "hasil": hasil,
            "error": error,
            "nilai_form": nilai_form,
            "tingkat_aktivitas": TINGKAT_AKTIVITAS,
        },
    )