import json
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Education, Experience, Project


class AuthenticationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="regular_user",
            password="Strong-test-password-928!",
        )

    def test_register_creates_user_and_shows_success_message(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "new_user",
                "password1": "Strong-test-password-928!",
                "password2": "Strong-test-password-928!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("main:login"))
        created_user = User.objects.get(username="new_user")
        self.assertTrue(created_user.check_password("Strong-test-password-928!"))
        self.assertContains(response, "Akun berhasil dibuat. Silakan login.")
        self.assertContains(response, "Register")
        self.assertNotContains(response, "nav-user")

    def test_auth_pages_show_portfolio_owner_brand_and_titles(self):
        register_response = self.client.get(reverse("main:register"))
        login_response = self.client.get(reverse("main:login"))

        self.assertContains(
            register_response, "Register - Niccola Geraldo Winaryo Durand"
        )
        self.assertContains(register_response, "NicoGWD")
        self.assertContains(login_response, "Login - Niccola Geraldo Winaryo Durand")
        self.assertContains(login_response, "NicoGWD")

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "new_user",
                "password1": "Strong-test-password-928!",
                "password2": "Different-test-password-928!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_register_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "regular_user",
                "password1": "Strong-test-password-928!",
                "password2": "Strong-test-password-928!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(User.objects.filter(username="regular_user").count(), 1)

    def test_login_rejects_invalid_password(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "regular_user", "password": "incorrect"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("nav-user", response.content.decode())

    def test_login_session_and_last_login_cookie_survive_navigation(self):
        response = self.client.post(
            reverse("main:login"),
            {
                "username": "regular_user",
                "password": "Strong-test-password-928!",
            },
        )

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertIn("sessionid", response.cookies)
        self.assertIn("last_login", response.cookies)
        last_login = response.cookies["last_login"].value
        self.assertTrue(last_login)

        for url_name in ("show_main", "show_experience", "show_projects"):
            page = self.client.get(reverse(f"main:{url_name}"))
            self.assertContains(page, "regular_user", html=False)
            if url_name == "show_main":
                self.assertContains(page, last_login)

    def test_logout_clears_session_and_last_login_cookie(self):
        self.client.login(
            username="regular_user", password="Strong-test-password-928!"
        )
        self.client.cookies["last_login"] = "2026-09-28 12:00:00"

        response = self.client.get(reverse("main:logout"))

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertEqual(response.cookies["last_login"].value, "")
        profile = self.client.get(reverse("main:show_main"))
        self.assertContains(profile, "Login")
        self.assertContains(profile, "Register")
        self.assertNotContains(profile, "regular_user")

    def test_auth_forms_use_csrf_and_reject_post_without_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.get(reverse("main:register"))

        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        rejected = csrf_client.post(
            reverse("main:register"),
            {
                "username": "new_user",
                "password1": "Strong-test-password-928!",
                "password2": "Strong-test-password-928!",
            },
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertFalse(User.objects.filter(username="new_user").exists())


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
        self.owner = User.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="Strong-owner-password-928!",
        )
        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="Strong-test-password-928!",
        )
        self.editor = User.objects.create_user(
            username="project_editor",
            password="Strong-editor-password-928!",
        )
        self.editor.groups.add(Group.objects.create(name="Editor"))
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

    def test_project_controls_follow_role_permissions(self):
        projects_url = reverse("main:show_projects")
        add_url = reverse("main:create_project")
        update_url = reverse("main:update_project", args=[self.project.id])
        delete_url = reverse("main:delete_project", args=[self.project.id])

        response = self.client.get(projects_url)
        self.assertNotContains(response, add_url)
        self.assertNotContains(response, update_url)
        self.assertNotContains(response, delete_url)
        self.assertContains(response, "Star")

        self.client.force_login(self.regular_user)
        response = self.client.get(projects_url)
        self.assertNotContains(response, add_url)
        self.assertNotContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.editor)
        response = self.client.get(projects_url)
        self.assertNotContains(response, add_url)
        self.assertContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.owner)
        response = self.client.get(projects_url)
        self.assertContains(response, add_url)
        self.assertContains(response, update_url)
        self.assertContains(response, delete_url)

    def test_project_create_and_delete_are_owner_only(self):
        add_url = reverse("main:create_project")
        delete_url = reverse("main:delete_project", args=[self.project.id])
        project_data = {
            "title": "New test project",
            "description": "Created by the owner.",
            "tech_stack": "Django",
            "project_url": "",
            "project_image_url": "",
        }

        anonymous_response = self.client.post(delete_url)
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

        self.client.force_login(self.regular_user)
        self.assertEqual(self.client.get(add_url).status_code, 403)
        self.assertEqual(self.client.post(add_url, project_data).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())
        self.assertFalse(Project.objects.filter(title="New test project").exists())

        self.client.force_login(self.owner)
        created = self.client.post(add_url, project_data)
        self.assertEqual(created.status_code, 302)
        new_project = Project.objects.get(title="New test project")

        updated = self.client.post(
            reverse("main:update_project", args=[new_project.id]),
            {
                **project_data,
                "title": "Owner updated project",
            },
        )
        self.assertEqual(updated.status_code, 302)
        new_project.refresh_from_db()
        self.assertEqual(new_project.title, "Owner updated project")

        deleted = self.client.post(delete_url)
        self.assertEqual(deleted.status_code, 302)
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())
        self.assertTrue(Project.objects.filter(pk=new_project.id).exists())

    def test_editor_can_update_projects_but_cannot_create_or_delete(self):
        update_url = reverse("main:update_project", args=[self.project.id])
        create_url = reverse("main:create_project")
        delete_url = reverse("main:delete_project", args=[self.project.id])
        updated_data = {
            "title": "Updated project title",
            "description": "Updated by the editor.",
            "tech_stack": "Django",
            "project_url": "",
            "project_image_url": "",
        }

        self.assertEqual(self.client.get(update_url).status_code, 302)
        self.client.force_login(self.regular_user)
        self.assertEqual(self.client.get(update_url).status_code, 403)
        self.assertEqual(self.client.post(update_url, updated_data).status_code, 403)

        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(update_url).status_code, 200)
        self.assertEqual(self.client.post(update_url, updated_data).status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Updated project title")
        self.assertEqual(self.client.get(create_url).status_code, 403)
        self.assertEqual(self.client.post(create_url, updated_data).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_logged_in_users_can_toggle_stars(self):
        star_url = reverse("main:toggle_star", args=[self.project.id])

        response = self.client.post(star_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.project.starred_by.exists())

        self.client.force_login(self.regular_user)
        self.assertEqual(self.client.get(star_url).status_code, 405)
        response = self.client.post(star_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project.starred_by.filter(pk=self.regular_user.pk).exists())

        self.client.post(star_url)
        self.assertFalse(self.project.starred_by.filter(pk=self.regular_user.pk).exists())

    def test_project_json_uses_starrer_natural_keys(self):
        self.project.starred_by.add(self.regular_user)

        response = self.client.get(reverse("main:get_projects_json"))

        data = json.loads(response.content)
        self.assertIn(["regular_user"], data[0]["fields"]["starred_by"])
        self.assertNotIn("password", data[0]["fields"])

    def test_project_mutation_forms_require_csrf_tokens(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        add_url = reverse("main:create_project")
        response = csrf_client.get(add_url)

        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        rejected_add = csrf_client.post(
            add_url,
            {
                "title": "CSRF project",
                "description": "Must not be created without a token.",
                "tech_stack": "Django",
                "project_url": "",
                "project_image_url": "",
            },
        )
        self.assertEqual(rejected_add.status_code, 403)
        self.assertFalse(Project.objects.filter(title="CSRF project").exists())

        csrf_client.force_login(self.regular_user)
        response = csrf_client.get(reverse("main:show_projects"))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        rejected_star = csrf_client.post(
            reverse("main:toggle_star", args=[self.project.id])
        )
        self.assertEqual(rejected_star.status_code, 403)
        self.assertFalse(self.project.starred_by.exists())


class EducationTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="education_owner",
            email="education-owner@example.com",
            password="Strong-owner-password-928!",
        )
        self.regular_user = User.objects.create_user(
            username="education_user",
            password="Strong-test-password-928!",
        )
        self.editor = User.objects.create_user(
            username="education_editor",
            password="Strong-editor-password-928!",
        )
        self.editor.groups.add(Group.objects.create(name="Editor"))
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
        self.assertNotContains(response, reverse("main:create_education"))
        self.assertNotContains(
            response, reverse("main:update_education", args=[self.education.id])
        )

    def test_education_controls_follow_role_permissions(self):
        education_url = reverse("main:show_education")
        create_url = reverse("main:create_education")
        update_url = reverse("main:update_education", args=[self.education.id])
        delete_url = reverse("main:delete_education", args=[self.education.id])

        self.client.force_login(self.regular_user)
        response = self.client.get(education_url)
        self.assertNotContains(response, create_url)
        self.assertNotContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.editor)
        response = self.client.get(education_url)
        self.assertNotContains(response, create_url)
        self.assertContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.owner)
        response = self.client.get(education_url)
        self.assertContains(response, create_url)
        self.assertContains(response, update_url)
        self.assertContains(response, delete_url)

    def test_empty_education_page(self):
        Education.objects.all().delete()
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, "Belum ada pendidikan yang ditambahkan.")

    def test_create_education_form_page(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:create_education"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_form.html")

    def test_create_education(self):
        self.client.force_login(self.owner)
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
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("main:update_education", args=[self.education.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_form.html")
        self.assertContains(response, self.education.institution)
        self.assertContains(response, self.education.major)

    def test_update_education(self):
        self.client.force_login(self.owner)
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
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("main:delete_education", args=[self.education.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Education.objects.filter(pk=self.education.id).exists())

    def test_education_mutations_reject_anonymous_and_regular_users(self):
        create_url = reverse("main:create_education")
        update_url = reverse("main:update_education", args=[self.education.id])
        delete_url = reverse("main:delete_education", args=[self.education.id])
        data = {
            "institution": "New School",
            "degree": "sma",
            "major": "Science",
            "description": "Test education.",
            "start_year": 2020,
            "end_year": 2023,
            "gpa": "",
        }

        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Education.objects.filter(pk=self.education.id).exists())
        self.assertFalse(Education.objects.filter(institution="New School").exists())

        self.client.force_login(self.regular_user)
        self.assertEqual(self.client.get(create_url).status_code, 403)
        self.assertEqual(self.client.post(create_url, data).status_code, 403)
        self.assertEqual(self.client.get(update_url).status_code, 403)
        self.assertEqual(self.client.post(update_url, data).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Education.objects.filter(pk=self.education.id).exists())
        self.assertFalse(Education.objects.filter(institution="New School").exists())

    def test_editor_can_update_education_but_cannot_create_or_delete(self):
        create_url = reverse("main:create_education")
        update_url = reverse("main:update_education", args=[self.education.id])
        delete_url = reverse("main:delete_education", args=[self.education.id])
        update_data = {
            "institution": self.education.institution,
            "degree": "sarjana",
            "major": "Sistem Informasi",
            "description": "Updated by an editor.",
            "start_year": 2025,
            "end_year": "",
            "gpa": "3.90",
        }

        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(update_url).status_code, 200)
        self.assertEqual(self.client.post(update_url, update_data).status_code, 302)
        self.education.refresh_from_db()
        self.assertEqual(self.education.major, "Sistem Informasi")
        self.assertEqual(self.client.get(create_url).status_code, 403)
        self.assertEqual(self.client.post(create_url, update_data).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Education.objects.filter(pk=self.education.id).exists())

    def test_education_json_endpoint(self):
        response = self.client.get(reverse("main:get_education_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = json.loads(response.content)
        self.assertEqual(data[0]["fields"]["institution"], self.education.institution)
        self.assertEqual(data[0]["fields"]["degree"], self.education.degree)


class ExperienceTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="experience_owner",
            email="experience-owner@example.com",
            password="Strong-owner-password-928!",
        )
        self.regular_user = User.objects.create_user(
            username="experience_user",
            password="Strong-test-password-928!",
        )
        self.editor = User.objects.create_user(
            username="experience_editor",
            password="Strong-editor-password-928!",
        )
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.experience = Experience.objects.create(
            title="Research Assistant",
            description="Assisted with a research project.",
            category="research",
        )

    def test_experience_controls_follow_role_permissions(self):
        experience_url = reverse("main:show_experience")
        create_url = reverse("main:create_experience")
        update_url = reverse("main:update_experience", args=[self.experience.id])
        delete_url = reverse("main:delete_experience", args=[self.experience.id])

        response = self.client.get(experience_url)
        self.assertNotContains(response, create_url)
        self.assertNotContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.regular_user)
        response = self.client.get(experience_url)
        self.assertNotContains(response, create_url)
        self.assertNotContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.editor)
        response = self.client.get(experience_url)
        self.assertNotContains(response, create_url)
        self.assertContains(response, update_url)
        self.assertNotContains(response, delete_url)

        self.client.force_login(self.owner)
        response = self.client.get(experience_url)
        self.assertContains(response, create_url)
        self.assertContains(response, update_url)
        self.assertContains(response, delete_url)

    def test_editor_can_update_experience_but_cannot_create_or_delete(self):
        create_url = reverse("main:create_experience")
        update_url = reverse("main:update_experience", args=[self.experience.id])
        delete_url = reverse("main:delete_experience", args=[self.experience.id])
        update_data = {
            "title": "Updated Research Assistant",
            "description": "Updated by the editor.",
            "category": "research",
            "thumbnail": "",
            "ended_at": "",
        }

        self.assertEqual(self.client.get(update_url).status_code, 302)
        self.client.force_login(self.regular_user)
        self.assertEqual(self.client.get(update_url).status_code, 403)
        self.assertEqual(self.client.post(update_url, update_data).status_code, 403)

        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(update_url).status_code, 200)
        self.assertEqual(self.client.post(update_url, update_data).status_code, 302)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Updated Research Assistant")
        self.assertEqual(self.client.get(create_url).status_code, 403)
        self.assertEqual(self.client.post(create_url, update_data).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_owner_can_create_update_and_delete_experience(self):
        create_url = reverse("main:create_experience")
        update_url = reverse("main:update_experience", args=[self.experience.id])
        delete_url = reverse("main:delete_experience", args=[self.experience.id])
        self.client.force_login(self.owner)

        created = self.client.post(
            create_url,
            {
                "title": "Teaching Assistant",
                "description": "Helped students.",
                "category": "volunteer",
                "thumbnail": "",
                "ended_at": "",
            },
        )
        self.assertEqual(created.status_code, 302)
        self.assertTrue(Experience.objects.filter(title="Teaching Assistant").exists())

        updated = self.client.post(
            update_url,
            {
                "title": "Owner Updated Experience",
                "description": "Updated by the owner.",
                "category": "research",
                "thumbnail": "",
                "ended_at": "",
            },
        )
        self.assertEqual(updated.status_code, 302)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Owner Updated Experience")

        deleted = self.client.post(delete_url)
        self.assertEqual(deleted.status_code, 302)
        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())

    def test_experience_mutations_require_csrf_and_delete_requires_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        create_url = reverse("main:create_experience")
        response = client.get(create_url)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

        rejected = client.post(
            create_url,
            {
                "title": "CSRF blocked",
                "description": "Should not be created.",
                "category": "research",
                "thumbnail": "",
                "ended_at": "",
            },
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertFalse(Experience.objects.filter(title="CSRF blocked").exists())
        self.assertEqual(
            client.get(
                reverse("main:delete_experience", args=[self.experience.id])
            ).status_code,
            405,
        )
