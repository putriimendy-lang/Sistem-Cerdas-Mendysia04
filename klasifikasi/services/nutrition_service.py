from pathlib import Path

import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


LABEL_KELAS = ["Rendah", "Sedang", "Tinggi"]
FITUR_NUTRISI = ["Carbohydrate", "Protein", "Fat"]


def build_food_catalog(data, mapping_path):
    makanan = data.copy()
    for kolom in ["Energy", *FITUR_NUTRISI]:
        makanan[kolom] = pd.to_numeric(makanan[kolom], errors="coerce")

    makanan = makanan.dropna(subset=["KODE", "Energy"])
    makanan["KODE"] = makanan["KODE"].astype(str)

    nama_per_kode = {}
    mapping_file = Path(mapping_path)
    if mapping_file.is_file():
        mapping = pd.read_csv(mapping_file, dtype={"KODE": str})
        kolom_wajib = {"KODE", "Nama Makanan"}
        if not kolom_wajib.issubset(mapping.columns):
            raise ValueError(
                "File pemetaan makanan harus memiliki kolom KODE dan Nama Makanan."
            )
        mapping = mapping.dropna(subset=["KODE", "Nama Makanan"])
        mapping["KODE"] = mapping["KODE"].astype(str).str.strip()
        mapping["Nama Makanan"] = mapping["Nama Makanan"].astype(str).str.strip()
        if mapping["KODE"].duplicated().any():
            raise ValueError("File pemetaan makanan memiliki KODE yang duplikat.")
        nama_per_kode = dict(zip(mapping["KODE"], mapping["Nama Makanan"]))

    makanan["nama_makanan"] = makanan["KODE"].map(nama_per_kode)
    nama_tersedia = makanan["nama_makanan"].notna().any()
    makanan["nama_makanan"] = makanan["nama_makanan"].fillna(makanan["KODE"])
    makanan["kategori"] = pd.qcut(
        makanan["Energy"],
        q=3,
        labels=LABEL_KELAS,
    )

    records = makanan.to_dict("records")
    for food in records:
        for column in ["Energy", *FITUR_NUTRISI]:
            if pd.isna(food[column]):
                food[column] = None

    return records, bool(nama_tersedia)


def recommend_lower_calorie_foods(food_code, foods, limit=5):
    pilihan = next((food for food in foods if food["KODE"] == food_code), None)
    if pilihan is None:
        return None, []

    if not all(pd.notna(pilihan[column]) for column in FITUR_NUTRISI):
        return pilihan, []

    alternatif = [
        food
        for food in foods
        if food["KODE"] != food_code
        and food["Energy"] < pilihan["Energy"]
        and all(pd.notna(food[column]) for column in FITUR_NUTRISI)
    ]
    if not alternatif:
        return pilihan, []

    makanan_dengan_nutrisi = [
        food
        for food in foods
        if all(pd.notna(food[column]) for column in FITUR_NUTRISI)
    ]
    fitur_semua = [
        [float(food[kolom]) for kolom in FITUR_NUTRISI]
        for food in makanan_dengan_nutrisi
    ]
    fitur_alternatif = [
        [float(food[kolom]) for kolom in FITUR_NUTRISI]
        for food in alternatif
    ]

    scaler = StandardScaler()
    scaler.fit(fitur_semua)
    fitur_pilihan = scaler.transform(
        [[float(pilihan[kolom]) for kolom in FITUR_NUTRISI]]
    )
    fitur_alternatif = scaler.transform(fitur_alternatif)

    jumlah = min(limit, len(alternatif))
    neighbors = NearestNeighbors(n_neighbors=jumlah)
    neighbors.fit(fitur_alternatif)
    jarak, indeks = neighbors.kneighbors(fitur_pilihan)

    rekomendasi = []
    for distance, index in zip(jarak[0], indeks[0]):
        item = dict(alternatif[index])
        item["similarity_distance"] = round(float(distance), 3)
        rekomendasi.append(item)

    return pilihan, rekomendasi
