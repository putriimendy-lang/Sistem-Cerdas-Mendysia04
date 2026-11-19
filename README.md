# Klasifikasi Tingkat Kalori Makanan (KaloriMakanan)

## Deskripsi Proyek
**KaloriMakanan** adalah aplikasi web berbasis **Django** untuk mengklasifikasikan tingkat kalori makanan ke dalam kategori **Rendah**, **Sedang**, dan **Tinggi** menggunakan algoritma **Decision Tree**. Selain klasifikasi berbasis input kandungan gizi (Karbohidrat, Protein, dan Lemak), aplikasi ini juga menyediakan katalog makanan, kalkulator kebutuhan kalori, visualisasi data, evaluasi model, asisten AI, serta pencatatan riwayat klasifikasi.

### Fitur & Menu Utama
- **Beranda:** Halaman utama berisi ringkasan informasi dan navigasi aplikasi.
- **Klasifikasi Kalori:** Form input nilai gizi (Karbohidrat, Protein, Lemak) untuk memprediksi kategori kalori makanan menggunakan model *Decision Tree*.
- **Daftar Makanan:** Daftar bahan pangan beserta rincian kandungan gizinya dari dataset TKPI 2017.
- **Kebutuhan Kalori:** Kalkulator untuk menghitung estimasi kebutuhan kalori harian pengguna.
- **Visualisasi Data:** Penyajian grafik dan statistik distribusi data gizi pada dataset TKPI 2017.
- **Evaluasi Model:** Menampilkan hasil evaluasi performa model klasifikasi *Decision Tree*.
- **Asisten AI:** Fitur konsultasi interaktif berbasis AI seputar makanan dan gizi.
- **Riwayat:** Pencatatan riwayat hasil klasifikasi kalori yang tersimpan di database (`RiwayatKlasifikasi`).
- **About:** Informasi mengenai aplikasi dan pengembang.

### Teknologi yang Digunakan
- **Backend:** Python, Django
- **Machine Learning & Data:** Scikit-learn (Decision Tree), Pandas
- **Database:** SQLite (`db.sqlite3`)
- **Frontend:** HTML, CSS

---

## Dataset

### Deskripsi Dataset
Dataset yang digunakan berasal dari **Tabel Komposisi Pangan Indonesia (TKPI) 2017** yang mencakup **1.146 jenis bahan pangan** beserta kandungan zat gizinya per 100 gram Berat Dapat Dimakan (BDD).
- `TKPI 2017.xlsx`: Data mentah TKPI 2017 (1.146 baris, 26 kolom).
- `tkpi_2017_bersih.csv`: Data nutrisi hasil pembersihan untuk pemodelan dan visualisasi (1.146 baris, 20 kolom).
- `tkpi_nama_makanan.csv`: Daftar pemetaan kode bahan pangan (`KODE`) dan nama makanan (`Nama Makanan`).

### Sumber Dataset
- **Sumber Primer:** Kementerian Kesehatan Republik Indonesia (Direktorat Jenderal Kesehatan Masyarakat), *Tabel Komposisi Pangan Indonesia (TKPI) 2017*.
- **Tautan Resmi:**
  - Repository Kemenkes RI: https://repository.kemkes.go.id/book/777
  - Portal Data Komposisi Pangan Indonesia (Panganku.org): https://www.panganku.org/id-ID/semua_nutrisi

### Lisensi Dataset
Publikasi resmi **Kementerian Kesehatan Republik Indonesia** (data publik pemerintah). Dalam proyek ini, dataset digunakan khusus untuk keperluan **akademik, penelitian, dan pembelajaran non-komersial** dengan mencantumkan atribusi kepada penerbit asli.

---

## Cara Menjalankan Aplikasi

### Prasyarat
- Python 3.x terpasang di perangkat.

### Langkah-Langkah (Windows)
1. **Buka terminal dan masuk ke folder utama proyek** (folder yang berisi `manage.py`):
   ```bash
   cd p14_kalorimakanan
   ```

2. **Buat dan aktifkan virtual environment (`venv`):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install seluruh library yang dibutuhkan:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Siapkan konfigurasi lokal** di file `.env` pada folder proyek. File ini tidak boleh diunggah ke GitHub.
   Buat secret key dengan perintah:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Tambahkan hasilnya ke `.env`, beserta pengaturan berikut:
   ```text
   DJANGO_SECRET_KEY=hasil-secret-key
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
   ```
   Untuk menggunakan Asisten AI, tambahkan juga `GROQ_API_KEY` ke file yang sama.

5. **Jalankan migrasi database:**
   ```bash
   python manage.py migrate
   ```

6. **Jalankan server lokal Django:**
   ```bash
   python manage.py runserver
   ```

7. **Akses aplikasi melalui browser:**
   Buka alamat `http://127.0.0.1:8000/`

Untuk deployment, atur `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY`, dan `DJANGO_ALLOWED_HOSTS` melalui environment server.

---

## Disusun Oleh
- **Nama:** Mendysia Anggita Putri
- **NIM:** 253307004
- **Keterangan:** Proyek ini dikerjakan secara individu (mencakup pengolahan dataset, pemodelan *Decision Tree*, pengembangan web Django, pengujian, dan dokumentasi).