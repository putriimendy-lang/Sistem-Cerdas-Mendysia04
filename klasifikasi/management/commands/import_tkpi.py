import pandas as pd
from django.core.management.base import BaseCommand
from klasifikasi.models import DataMakananTKPI
from pathlib import Path


class Command(BaseCommand):
    help = "Mengimpor dataset TKPI 2017 ke database"

    def handle(self, *args, **options):
        base_dir = Path.cwd()
        file_dataset = base_dir / "dataset" / "tkpi_2017_bersih.csv"

        if not file_dataset.exists():
            self.stdout.write(self.style.ERROR("File dataset tidak ditemukan."))
            return

        df = pd.read_csv(file_dataset)

        kolom = [
            "Energy", "Protein", "Fat", "Carbohydrate", "Fiber",
            "Calcium", "Phosphorus", "Iron", "Sodium", "Potassium",
            "Copper", "Zinc", "Retinol", "Beta_Carotene",
            "Total_Carotenoids", "Thiamine", "Riboflavin",
            "Niacin", "Vitamin_C"
        ]

        data = []

        for _, baris in df.iterrows():
            nilai = {
                nama_kolom: (
                    None if pd.isna(baris[nama_kolom])
                    else float(baris[nama_kolom])
                )
                for nama_kolom in kolom
            }

            data.append(
                DataMakananTKPI(
                    KODE=str(baris["KODE"]),
                    **nilai
                )
            )

        DataMakananTKPI.objects.all().delete()
        DataMakananTKPI.objects.bulk_create(data, batch_size=200)

        self.stdout.write(
            self.style.SUCCESS(
                f"Berhasil mengimpor {len(data)} data makanan TKPI."
            )
        )