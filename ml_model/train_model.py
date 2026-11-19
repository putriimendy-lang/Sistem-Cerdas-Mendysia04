
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# Menentukan lokasi folder proyek
BASE_DIR = Path(__file__).resolve().parent.parent

# Membaca dataset TKPI yang sudah dibersihkan
DATASET_PATH = BASE_DIR / "dataset" / "tkpi_2017_bersih.csv"

df = pd.read_csv(DATASET_PATH)

# Menentukan fitur dan target
fitur = [
    "Carbohydrate",
    "Protein",
    "Fat"
]

target = "Energy"

# Mengambil kolom yang dibutuhkan
df = df[fitur + [target]].copy()

# Memastikan tidak ada data kosong
df = df.dropna()

# Mengubah nilai kalori menjadi tiga kategori
df["Kategori Kalori"] = pd.qcut(
    df[target],
    q=3,
    labels=["Rendah", "Sedang", "Tinggi"]
)

# Memisahkan fitur dan target
X = df[fitur]
y = df["Kategori Kalori"]

# Membagi data menjadi data latih dan data uji
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Membuat model Decision Tree
model = DecisionTreeClassifier(
    max_depth=3,
    random_state=42
)

# Melatih model
model.fit(X_train, y_train)

# Melakukan prediksi
y_pred = model.predict(X_test)

# Menghitung akurasi
akurasi = accuracy_score(y_test, y_pred)

# Menampilkan hasil evaluasi
print("=" * 50)
print("HASIL PELATIHAN MODEL DECISION TREE TKPI")
print("=" * 50)

print("Jumlah seluruh data :", len(df))
print("Jumlah data latih   :", len(X_train))
print("Jumlah data uji     :", len(X_test))

print("\nAkurasi Model:", round(akurasi * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Menyimpan model baru
MODEL_DIR = BASE_DIR / "ml_model"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "decision_tree_model_tkpi.joblib"

joblib.dump(
    {
        "model": model,
        "features": fitur,
        "categories": list(model.classes_),
        "accuracy": akurasi
    },
    MODEL_PATH
)

print("\nModel TKPI berhasil disimpan!")
print("Lokasi:", MODEL_PATH)
