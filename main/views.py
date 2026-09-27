from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.models import Education, Experience, Project
from main.forms import EducationForm, ProjectForm

OWNER_NAME = "Niccola Geraldo Winaryo Durand"
OWNER_NICKNAME = "NicoGWD"


def show_main(request):
    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "npm": "2506619070",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Mahasiswa Ilmu Komputer Universitas Indonesia yang tertarik "
            "pada pengembangan perangkat lunak dan pendidikan."
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def get_experience_json(request):
    """Mengembalikan seluruh data Experience dalam format JSON."""
    experience_json = serializers.serialize("json", Experience.objects.all())
    return HttpResponse(experience_json, content_type="application/json")


def show_projects(request):
    # Ambil data lewat endpoint JSON lalu deserialize menjadi objek model,
    # sehingga halaman menampilkan data yang sama dengan yang dikirim lewat JSON.
    json_response = get_projects_json(request)
    project_list = [
        entry.object
        for entry in serializers.deserialize(
            "json", json_response.content.decode("utf-8")
        )
    ]
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "title_query": title_query,
        "project_list": project_list,
    }
    return render(request, "projects.html", context)


def create_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": OWNER_NAME,
        "form": form,
    }
    return render(request, "projects_form.html", context)


def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:show_projects")

    return redirect("main:show_projects")


def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize("json", projects)
    return HttpResponse(projects_json, content_type="application/json")


def show_education(request):
    # Ambil data lewat endpoint JSON lalu deserialize menjadi objek model.
    json_response = get_education_json(request)
    education_list = [
        entry.object
        for entry in serializers.deserialize(
            "json", json_response.content.decode("utf-8")
        )
    ]

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "education_list": education_list,
    }
    return render(request, "education.html", context)


def create_education(request):
    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pendidikan baru berhasil ditambahkan!")
        return redirect("main:show_education")

    context = {
        "name": OWNER_NAME,
        "form": form,
    }
    return render(request, "education_form.html", context)


def update_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    form = EducationForm(request.POST or None, instance=education)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Data pendidikan berhasil diubah!")
        return redirect("main:show_education")

    context = {
        "name": OWNER_NAME,
        "form": form,
        "education": education,
        "is_update": True,
    }
    return render(request, "education_form.html", context)


def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        education.delete()
        messages.success(request, "Data pendidikan berhasil dihapus!")
        return redirect("main:show_education")

    return redirect("main:show_education")


def get_education_json(request):
    """Mengembalikan seluruh data Education dalam format JSON."""
    education_json = serializers.serialize(
        "json", Education.objects.all().order_by("start_year")
    )
    return HttpResponse(education_json, content_type="application/json")

def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Burhan",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("main:show_main")

    context = {
        "name": "Burhan",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    return redirect("main:show_main")