from django.forms import ModelForm, TextInput, Textarea, URLInput, Select, NumberInput

from main.models import Education, Project

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
        ]

        labels = {
            "title": "Nama Proyek",
            "description": "Deskripsi Proyek",
            "tech_stack": "Teknologi yang Digunakan",
            "project_url": "URL Proyek",
            "project_image_url": "URL Gambar Proyek",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan Proyekmu",
                    "rows": 3,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Django, Python, HTML, CSS",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "https://github.com/kakBurhan/burhanquestv4",
                }
            ),
            "project_image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }

class EducationForm(ModelForm):
    class Meta:
        model = Education
        fields = [
            "institution",
            "degree",
            "major",
            "description",
            "start_year",
            "end_year",
            "gpa",
        ]

        labels = {
            "institution": "Institusi",
            "degree": "Jenjang",
            "major": "Jurusan",
            "description": "Deskripsi",
            "start_year": "Tahun Mulai",
            "end_year": "Tahun Selesai",
            "gpa": "GPA",
        }

        widgets = {
            "institution": TextInput(
                attrs={
                    "placeholder": "Universitas Indonesia",
                    "maxlength": 255,
                }
            ),
            "degree": Select(
                attrs={
                    "placeholder": "Pilih jenjang pendidikan",
                }
            ),
            "major": TextInput(
                attrs={
                    "placeholder": "Ilmu Komputer",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan pengalaman pendidikanmu",
                    "rows": 3,
                }
            ),
            "start_year": NumberInput(
                attrs={
                    "placeholder": "2022",
                    "min": 1900,
                    "max": 2100,
                }
            ),
            "end_year": NumberInput(
                attrs={
                    "placeholder": "Kosongkan jika masih berjalan",
                    "min": 1900,
                    "max": 2100,
                }
            ),
            "gpa": NumberInput(
                attrs={
                    "placeholder": "3.75",
                    "min": 0,
                    "max": 4,
                    "step": "0.01",
                }
            ),
        }