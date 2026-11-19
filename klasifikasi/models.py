from django.db import models

class RiwayatKlasifikasi(models.Model):
    """Satu baris = satu kali pengguna menekan tombol Klasifikasikan."""

    karbohidrat = models.FloatField()
    protein = models.FloatField()
    lemak = models.FloatField()
    kategori = models.CharField(max_length=10)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dibuat"]
        verbose_name = "Riwayat klasifikasi"
        verbose_name_plural = "Riwayat klasifikasi"

    def __str__(self):
        return f"{self.kategori} ({self.karbohidrat}/{self.protein}/{self.lemak})"


class CatatanMakan(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    food_code = models.CharField(max_length=20)
    portion_grams = models.FloatField()
    energy_kcal = models.FloatField()
    tanggal = models.DateField(db_index=True)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tanggal", "-dibuat"]
        verbose_name = "Catatan makan"
        verbose_name_plural = "Catatan makan"

    def __str__(self):
        return f"{self.food_code} ({self.tanggal})"


class DataMakananTKPI(models.Model):
    KODE = models.CharField(max_length=20, unique=True)
    Energy = models.FloatField(null=True, blank=True)
    Protein = models.FloatField(null=True, blank=True)
    Fat = models.FloatField(null=True, blank=True)
    Carbohydrate = models.FloatField(null=True, blank=True)
    Fiber = models.FloatField(null=True, blank=True)
    Calcium = models.FloatField(null=True, blank=True)
    Phosphorus = models.FloatField(null=True, blank=True)
    Iron = models.FloatField(null=True, blank=True)
    Sodium = models.FloatField(null=True, blank=True)
    Potassium = models.FloatField(null=True, blank=True)
    Copper = models.FloatField(null=True, blank=True)
    Zinc = models.FloatField(null=True, blank=True)
    Retinol = models.FloatField(null=True, blank=True)
    Beta_Carotene = models.FloatField(null=True, blank=True)
    Total_Carotenoids = models.FloatField(null=True, blank=True)
    Thiamine = models.FloatField(null=True, blank=True)
    Riboflavin = models.FloatField(null=True, blank=True)
    Niacin = models.FloatField(null=True, blank=True)
    Vitamin_C = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["KODE"]
        verbose_name = "Data makanan TKPI"
        verbose_name_plural = "Data makanan TKPI"

    def __str__(self):
        return f"{self.KODE} - {self.Energy} kcal"
