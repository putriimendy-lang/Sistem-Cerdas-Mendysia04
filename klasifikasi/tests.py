from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from . import views
from .models import CatatanMakan
from .services.nutrition_service import build_food_catalog


class FoodFeatureTests(TestCase):
    def setUp(self):
        self.foods, _ = build_food_catalog(
            views.DF,
            views.FOOD_NAME_MAPPING_PATH,
        )

    def test_food_list_searches_by_tkpi_code(self):
        code = self.foods[0]["KODE"]

        response = self.client.get(reverse("daftar_makanan"), {"q": code})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["jumlah_makanan"], 1)
        self.assertContains(response, code)

    def test_food_list_searches_by_mapped_food_name(self):
        food = self.foods[0]

        response = self.client.get(
            reverse("daftar_makanan"),
            {"q": food["nama_makanan"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["jumlah_makanan"], 1)
        self.assertContains(response, food["nama_makanan"])

    def test_food_list_paginates_dataset_rows(self):
        response = self.client.get(reverse("daftar_makanan"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["makanan"]), 8)
        self.assertGreater(response.context["jumlah_makanan"], 8)
        self.assertTrue(response.context["halaman"].has_next())
        self.assertContains(response, "Berikutnya")

    def test_food_list_hides_diary_navigation_and_actions(self):
        response = self.client.get(reverse("daftar_makanan"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "/catatan-makan/")
        self.assertNotContains(response, "Catatan Harian")

    def test_about_page_is_available_from_sidebar(self):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tentang KaloriMakanan")
        self.assertContains(response, ">About</span>", html=False)

    def test_food_with_missing_macros_remains_visible_without_recommendations(self):
        food = next(
            item
            for item in self.foods
            if item["Protein"] is None or item["Fat"] is None
        )

        response = self.client.get(
            reverse("daftar_makanan"),
            {"q": food["KODE"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["jumlah_makanan"], 1)
        self.assertContains(response, food["nama_makanan"])
        self.assertContains(response, "-")

        recommendation_response = self.client.get(
            reverse("daftar_makanan"),
            {"rekomendasi": food["KODE"]},
        )
        self.assertEqual(recommendation_response.status_code, 200)
        self.assertEqual(recommendation_response.context["rekomendasi"], [])

    def test_food_list_filters_by_calorie_category(self):
        category = str(self.foods[0]["kategori"])

        response = self.client.get(
            reverse("daftar_makanan"),
            {"kategori": category},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["makanan"])
        self.assertTrue(
            all(str(item["kategori"]) == category for item in response.context["makanan"])
        )

    def test_recommendations_have_lower_energy_and_at_most_five_results(self):
        pilihan = max(self.foods, key=lambda item: item["Energy"])

        response = self.client.get(
            reverse("daftar_makanan"),
            {"rekomendasi": pilihan["KODE"]},
        )

        alternatives = response.context["rekomendasi"]
        self.assertEqual(len(alternatives), 5)
        self.assertTrue(
            all(item["Energy"] < pilihan["Energy"] for item in alternatives)
        )

    def test_diary_adds_portion_calories_and_is_session_scoped(self):
        food = self.foods[0]
        portion = 150
        response = self.client.post(
            reverse("catatan_makan"),
            {
                "action": "add",
                "tanggal": "2026-11-19",
                "food_code": food["KODE"],
                "portion_grams": str(portion),
            },
        )

        self.assertEqual(response.status_code, 302)
        entry = CatatanMakan.objects.get()
        self.assertEqual(entry.session_key, self.client.session.session_key)
        self.assertAlmostEqual(
            entry.energy_kcal,
            round(float(food["Energy"]) * portion / 100, 2),
        )

        other_client = self.client_class()
        other_response = other_client.get(reverse("catatan_makan"))
        self.assertEqual(other_response.context["entri"], [])

    def test_diary_rejects_non_positive_portions(self):
        response = self.client.post(
            reverse("catatan_makan"),
            {
                "action": "add",
                "tanggal": "2026-11-19",
                "food_code": self.foods[0]["KODE"],
                "portion_grams": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Porsi harus lebih dari 0")
        self.assertEqual(CatatanMakan.objects.count(), 0)

    def test_classification_page_labels_recent_history_and_links_to_full_history(self):
        response = self.client.get(reverse("klasifikasi"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Riwayat Terbaru")
        self.assertContains(response, reverse("riwayat"))
        self.assertContains(response, "Lihat semua riwayat")

    def test_visualization_uses_distinct_charts_and_dataset_values(self):
        response = self.client.get(reverse("visualisasi"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rata-rata Energi per Kategori")
        averages = response.context["rata_rata_kategori"]
        self.assertEqual(len(averages), 3)
        self.assertLess(averages[0], averages[1])
        self.assertLess(averages[1], averages[2])
        self.assertContains(response, 'type: "line"')
        self.assertContains(response, "Komposisi Makronutrien")
        self.assertContains(response, 'type: "doughnut"')
        self.assertContains(response, 'id="macroChart"')
        macro_averages = response.context["rata_rata_makronutrien"]
        self.assertEqual(len(macro_averages), 3)
        self.assertTrue(all(value > 0 for value in macro_averages))

    def test_calorie_calculator_uses_mifflin_st_jeor_and_saves_target(self):
        response = self.client.post(
            reverse("kebutuhan_kalori"),
            {
                "jenis_kelamin": "pria",
                "usia": "30",
                "berat": "70",
                "tinggi": "175",
                "aktivitas": "moderate",
            },
        )

        expected = round(
            ((10 * 70) + (6.25 * 175) - (5 * 30) + 5) * 1.55
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["hasil"]["kebutuhan"], expected)
        self.assertEqual(
            self.client.session["daily_calorie_target"],
            expected,
        )

    def test_classification_shows_macro_calorie_estimate(self):
        with patch.object(views.model, "predict", return_value=["Sedang"]):
            response = self.client.post(
                reverse("klasifikasi"),
                {
                    "karbohidrat": "20",
                    "protein": "10",
                    "lemak": "5",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["estimasi_kalori"], 165)
        self.assertContains(response, "165 kkal")
