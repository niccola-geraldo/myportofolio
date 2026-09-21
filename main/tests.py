import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Education, Experience, Project


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Staff of Media Bureau BEM Fasilkom UI",
            description="Made designs with Figma.",
            category="volunteer",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Staff of Media Bureau BEM Fasilkom UI")
        self.assertEqual(self.experience.category, "volunteer")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Volunteer")
        self.assertContains(response, "Ongoing")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "No experiences added yet.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Finished")
        self.assertNotContains(response, "Ongoing")

    def test_experience_json_endpoint(self):
        response = self.client.get(reverse("main:get_experience_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = json.loads(response.content)
        self.assertEqual(data[0]["fields"]["title"], self.experience.title)


class ProjectTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Universitas Indonesia Depok",
            description="A Roblox experience recreating the UI Depok campus.",
            tech_stack="Roblox Studio, Blender",
            project_url="https://www.roblox.com/games/131740669743214/Universitas-Indonesia-Depok",
        )

    def test_projects_url_is_accessible(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects.html")

    def test_projects_page_shows_model_data(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, self.project.title)
        self.assertContains(response, self.project.description)
        self.assertContains(response, self.project.tech_stack)
        self.assertContains(response, self.project.project_url)

    def test_empty_projects_page(self):
        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, "Belum ada proyek yang ditambahkan.")

    def test_projects_search_filter(self):
        matching = self.client.get(reverse("main:show_projects"), {"title": "Depok"})
        self.assertContains(matching, self.project.title)

        not_matching = self.client.get(reverse("main:show_projects"), {"title": "zzz"})
        self.assertNotContains(not_matching, self.project.title)
        self.assertContains(not_matching, "Tidak ada proyek dengan nama tersebut.")

    def test_projects_json_endpoint(self):
        response = self.client.get(reverse("main:get_projects_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = json.loads(response.content)
        self.assertEqual(data[0]["fields"]["title"], self.project.title)


class EducationTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="sarjana",
            major="Ilmu Komputer",
            description="Sedang menempuh pendidikan S1.",
            start_year=2025,
            gpa=3.75,
        )

    def test_education_url_is_accessible(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education.html")

    def test_education_page_shows_model_data(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, self.education.institution)
        self.assertContains(response, self.education.major)
        self.assertContains(response, "Sarjana (S1)")
        self.assertContains(response, "Ongoing")
        self.assertContains(response, "3.75")

    def test_empty_education_page(self):
        Education.objects.all().delete()
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, "Belum ada pendidikan yang ditambahkan.")

    def test_create_education_form_page(self):
        response = self.client.get(reverse("main:create_education"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_form.html")

    def test_create_education(self):
        response = self.client.post(
            reverse("main:create_education"),
            {
                "institution": "SMA Negeri 1 Jakarta",
                "degree": "sma",
                "major": "IPA",
                "description": "Sekolah menengah atas.",
                "start_year": 2022,
                "end_year": 2025,
                "gpa": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        education = Education.objects.get(institution="SMA Negeri 1 Jakarta")
        self.assertEqual(education.degree, "sma")
        self.assertEqual(education.major, "IPA")
        self.assertEqual(education.start_year, 2022)
        self.assertEqual(education.end_year, 2025)
        self.assertIsNone(education.gpa)
        self.assertFalse(education.is_ongoing)

    def test_update_education_page_shows_existing_data(self):
        response = self.client.get(
            reverse("main:update_education", args=[self.education.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_form.html")
        self.assertContains(response, self.education.institution)
        self.assertContains(response, self.education.major)

    def test_update_education(self):
        response = self.client.post(
            reverse("main:update_education", args=[self.education.id]),
            {
                "institution": "Universitas Indonesia",
                "degree": "sarjana",
                "major": "Sistem Informasi",
                "description": "Pindah program studi.",
                "start_year": 2025,
                "end_year": "",
                "gpa": 3.90,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.education.refresh_from_db()
        self.assertEqual(self.education.major, "Sistem Informasi")
        self.assertEqual(self.education.description, "Pindah program studi.")
        self.assertEqual(self.education.gpa, Decimal("3.90"))
        self.assertTrue(self.education.is_ongoing)

    def test_delete_education(self):
        response = self.client.post(
            reverse("main:delete_education", args=[self.education.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Education.objects.filter(pk=self.education.id).exists())

    def test_education_json_endpoint(self):
        response = self.client.get(reverse("main:get_education_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = json.loads(response.content)
        self.assertEqual(data[0]["fields"]["institution"], self.education.institution)
        self.assertEqual(data[0]["fields"]["degree"], self.education.degree)
