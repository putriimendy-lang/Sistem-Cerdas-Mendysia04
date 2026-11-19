from django.urls import path
from . import views

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("klasifikasi/", views.klasifikasi, name="klasifikasi"),
    path("visualisasi/", views.visualisasi, name="visualisasi"),
    path("evaluasi/", views.evaluasi_model, name="evaluasi_model"),
    path("asisten-ai/", views.asisten_ai, name="asisten_ai"),
    path("riwayat/", views.riwayat, name="riwayat"),
    path("about/", views.about, name="about"),
    path("makanan/", views.daftar_makanan, name="daftar_makanan"),
    path("catatan-makan/", views.catatan_makan, name="catatan_makan"),
    path("kebutuhan-kalori/", views.kebutuhan_kalori, name="kebutuhan_kalori"),
]