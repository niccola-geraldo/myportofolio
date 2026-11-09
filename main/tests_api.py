import uuid
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Education, Project


class ProjectAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.visitor = User.objects.create_user(username="visitor", password="test-password")
        self.project = Project.objects.create(
            title="Portfolio", description="My website", tech_stack="Django",
        )
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "title": "New project", "description": "A useful app", "tech_stack": "Python",
            "project_url": "https://example.com/", "project_image_url": "",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.project.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"title": "PORT"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"title": "not-found"})
        self.assertEqual(response.data, [])

    def test_missing_project(self):
        url = reverse("api:project-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(pk=response.data["id"]).exists())

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"project_url": "javascript:alert(1)"}, "project_url"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Project.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, "My website")
        response = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.visitor.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])

    def test_editor_can_update_but_cannot_create_or_delete(self):
        self.visitor.groups.add(Group.objects.create(name="Editor"))
        self.client.force_authenticate(user=self.visitor)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Changed")
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            403,
        )
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        # The Browsable API form renders a real CSRF token into the response.
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EducationAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(
            username="education-owner",
            password="test-password",
            email="education-owner@example.com",
        )
        cls.visitor = User.objects.create_user(
            username="education-visitor", password="test-password",
        )
        cls.editor = User.objects.create_user(username="education-editor")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="sarjana",
            major="Ilmu Komputer",
            description="Sedang menempuh pendidikan S1.",
            start_year=2024,
        )

    def setUp(self):
        self.list_url = reverse("api:education-list")
        self.detail_url = reverse("api:education-detail", args=[self.education.pk])
        self.star_url = reverse("api:education-star", args=[self.education.pk])
        self.payload = {
            "institution": "Universitas Baru",
            "degree": "sarjana",
            "major": "Informatika",
            "description": "Program sarjana.",
            "start_year": 2022,
            "end_year": 2025,
            "gpa": "3.90",
        }

    def test_public_list_and_detail_return_flat_records(self):
        expected = {
            "id": str(self.education.pk),
            "institution": "Universitas Indonesia",
            "degree": "sarjana",
            "degree_display": "Sarjana (S1)",
            "major": "Ilmu Komputer",
            "description": "Sedang menempuh pendidikan S1.",
            "start_year": 2024,
            "end_year": None,
            "gpa": None,
            "is_ongoing": True,
            "star_count": 0,
            "is_starred": False,
        }
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [expected])
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_search_uses_institution_and_preserves_order(self):
        earlier = Education.objects.create(**self.payload)
        tied = Education.objects.create(**{**self.payload, "start_year": 2024})

        response = self.client.get(self.list_url, {"institution": "  vERSITAS "})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = [str(earlier.pk), *sorted((str(self.education.pk), str(tied.pk)))]
        self.assertEqual([row["id"] for row in response.data], expected)

        response = self.client.get(self.list_url, {"institution": "Ilmu Komputer"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_missing_education_detail_and_star_return_404(self):
        missing_id = uuid.uuid4()
        detail = reverse("api:education-detail", args=[missing_id])
        star = reverse("api:education-star", args=[missing_id])
        self.assertEqual(self.client.get(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.client.force_authenticate(user=self.visitor)
        self.assertEqual(self.client.post(star).status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_and_regular_users_cannot_write_records(self):
        original = list(Education.objects.values())
        for user in (None, self.visitor):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                responses = (
                    self.client.post(self.list_url, self.payload, format="json"),
                    self.client.put(self.detail_url, self.payload, format="json"),
                    self.client.patch(self.detail_url, {"major": "Baru"}, format="json"),
                    self.client.delete(self.detail_url),
                )
                for response in responses:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(list(Education.objects.values()), original)

    def test_editor_can_patch_and_put_but_cannot_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"major": "Sistem Informasi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.major, "Sistem Informasi")
        self.assertEqual(self.education.institution, "Universitas Indonesia")

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, self.payload["institution"])
        self.assertEqual(self.education.end_year, self.payload["end_year"])
        self.assertEqual(self.education.gpa, Decimal(self.payload["gpa"]))

        original = list(Education.objects.values())
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(list(Education.objects.values()), original)

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        education = Education.objects.get(pk=response.data["id"])
        self.assertEqual(education.institution, self.payload["institution"])
        self.assertFalse(response.data["is_ongoing"])
        detail = reverse("api:education-detail", args=[education.pk])

        response = self.client.put(detail, {"major": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        education.refresh_from_db()
        self.assertEqual(education.major, self.payload["major"])

        response = self.client.patch(detail, {"end_year": None, "gpa": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        education.refresh_from_db()
        self.assertIsNone(education.end_year)
        self.assertIsNone(education.gpa)
        self.assertTrue(response.data["is_ongoing"])

        response = self.client.delete(detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Education.objects.filter(pk=education.pk).exists())

    def test_validation_rejects_invalid_fields_without_creating_a_record(self):
        self.client.force_authenticate(user=self.owner)
        invalid_values = {
            "institution": " <span></span> ",
            "major": "<img src=x onerror=alert(1)>",
            "description": "  ",
            "degree": "invalid",
            "start_year": -1,
            "gpa": "3.999",
        }
        response = self.client.post(self.list_url, {**self.payload, **invalid_values}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data), set(invalid_values))
        self.assertEqual(Education.objects.count(), 1)

    def test_text_is_cleaned_and_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        forged_id = str(uuid.uuid4())
        payload = {
            **self.payload,
            "id": forged_id,
            "institution": " <b>Universitas Baru</b> ",
            "major": " <b>Informatika</b> ",
            "description": " <p>Program sarjana.</p> ",
            "degree_display": "Forged degree",
            "is_ongoing": True,
            "star_count": 99,
            "is_starred": True,
            "starred_by": [self.visitor.pk],
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], forged_id)
        self.assertEqual(response.data["degree_display"], "Sarjana (S1)")
        self.assertFalse(response.data["is_ongoing"])
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertNotIn("starred_by", response.data)
        education = Education.objects.get(pk=response.data["id"])
        self.assertEqual(education.institution, self.payload["institution"])
        self.assertEqual(education.major, self.payload["major"])
        self.assertEqual(education.description, self.payload["description"])
        self.assertFalse(education.starred_by.exists())

    def test_star_is_publicly_counted_but_toggles_only_for_the_signed_in_user(self):
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(self.education.starred_by.exists())

        for count, user in enumerate((self.visitor, self.editor, self.owner), start=1):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                response = self.client.post(self.star_url, {"user": self.owner.pk}, format="json")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["id"], str(self.education.pk))
                self.assertTrue(response.data["is_starred"])
                self.assertEqual(response.data["star_count"], count)
                self.assertTrue(self.education.starred_by.filter(pk=user.pk).exists())

        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.data["star_count"], 3)
        self.assertFalse(response.data["is_starred"])

        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 2)
        self.assertCountEqual(
            self.education.starred_by.values_list("pk", flat=True),
            [self.editor.pk, self.owner.pk],
        )

    def test_session_star_requires_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=self.visitor.username, password="test-password"))
        response = client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(self.education.starred_by.exists())

        page = client.get(reverse("main:show_education"))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(self.star_url, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.education.starred_by.filter(pk=self.visitor.pk).exists())
