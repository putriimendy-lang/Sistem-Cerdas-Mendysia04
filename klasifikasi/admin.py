from django.contrib import admin
from .models import CatatanMakan, RiwayatKlasifikasi, DataMakananTKPI


@admin.register(RiwayatKlasifikasi)
class RiwayatAdmin(admin.ModelAdmin):
    list_display = ("dibuat", "karbohidrat", "protein", "lemak", "kategori")
    list_filter = ("kategori",)


@admin.register(DataMakananTKPI)
class DataMakananTKPIAdmin(admin.ModelAdmin):
    list_display = ("KODE", "Energy", "Protein", "Fat", "Carbohydrate")
    search_fields = ("KODE",)
    list_per_page = 25


@admin.register(CatatanMakan)
class CatatanMakanAdmin(admin.ModelAdmin):
    list_display = ("tanggal", "food_code", "portion_grams", "energy_kcal", "dibuat")
    list_filter = ("tanggal",)
    search_fields = ("food_code",)
    list_per_page = 25