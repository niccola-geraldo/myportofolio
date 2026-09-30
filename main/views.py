from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.models import Education, Experience, Project
from main.forms import EducationForm, ExperienceForm, ProjectForm

import datetime

OWNER_NAME = "Niccola Geraldo Winaryo Durand"
OWNER_NICKNAME = "NicoGWD"


def _is_editor(user):
    return user.groups.filter(name="Editor").exists()


def _require_superuser(request):
    if not request.user.is_superuser:
        raise PermissionDenied


def _require_editor_or_owner(request):
    if not (request.user.is_superuser or _is_editor(request.user)):
        raise PermissionDenied


def show_main(request):
    last_login = request.COOKIES.get('last_login', 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "npm": "2506619070",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Mahasiswa Ilmu Komputer Universitas Indonesia yang tertarik "
            "pada pengembangan perangkat lunak dan pendidikan."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "experience_list": Experience.objects.all(),
        "is_editor": _is_editor(request.user),
    }
    return render(request, "experience.html", context)


def get_experience_json(request):
    """Mengembalikan seluruh data Experience dalam format JSON."""
    experience_json = serializers.serialize("json", Experience.objects.all())
    return HttpResponse(experience_json, content_type="application/json")


@login_required(login_url="main:login")
def create_experience(request):
    _require_superuser(request)
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengalaman baru berhasil ditambahkan!")
        return redirect("main:show_experience")

    return render(
        request,
        "experience_form.html",
        {
            "name": OWNER_NAME,
            "nickname": OWNER_NICKNAME,
            "form": form,
            "is_update": False,
        },
    )


@login_required(login_url="main:login")
def update_experience(request, experience_id):
    _require_editor_or_owner(request)
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Data pengalaman berhasil diubah!")
        return redirect("main:show_experience")

    return render(
        request,
        "experience_form.html",
        {
            "name": OWNER_NAME,
            "nickname": OWNER_NICKNAME,
            "form": form,
            "experience": experience,
            "is_update": True,
        },
    )


@login_required(login_url="main:login")
@require_POST
def delete_experience(request, experience_id):
    _require_superuser(request)
    experience = get_object_or_404(Experience, pk=experience_id)
    experience.delete()
    messages.success(request, "Pengalaman berhasil dihapus!")
    return redirect("main:show_experience")


def show_projects(request):
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "title_query": title_query,
        "is_editor": _is_editor(request.user),
    }
    if request.user.is_superuser:
        context["form"] = ProjectForm()

    return render(request, "projects.html", context)


@login_required(login_url="main:login")
def create_project(request):
    _require_superuser(request)
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "form": form,
    }
    return render(request, "projects_form.html", context)


@login_required(login_url="main:login")
def update_project(request, project_id):
    _require_editor_or_owner(request)
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Data proyek berhasil diubah!")
        return redirect("main:show_projects")

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "form": form,
        "project": project,
        "is_update": True,
    }
    return render(request, "projects_form.html", context)


@login_required(login_url="main:login")
@require_POST
def delete_project(request, project_id):
    _require_superuser(request)
    project = get_object_or_404(Project, pk=project_id)
    project.delete()
    messages.success(request, "Project berhasil dihapus!")
    return redirect("main:show_projects")


def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.prefetch_related("starred_by")

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    data = []
    for project in projects:
        starrers = list(project.starred_by.all())
        data.append(
            {
                "pk": str(project.pk),
                "fields": {
                    "title": project.title,
                    "description": project.description,
                    "tech_stack": project.tech_stack,
                    "project_url": project.project_url,
                    "project_image_url": project.project_image_url,
                    "star_count": len(starrers),
                    "is_starred": request.user.is_authenticated
                    and any(user.pk == request.user.pk for user in starrers),
                    "starred_by_names": ", ".join(
                        user.username for user in starrers
                    ),
                },
            }
        )

    return JsonResponse(data, safe=False)


@require_POST
def create_project_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menambahkan proyek."},
            status=403,
        )

    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save()
        return JsonResponse(
            {"message": "Proyek berhasil ditambahkan.", "pk": str(project.pk)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@login_required(login_url="main:login")
@require_POST
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.user in project.starred_by.all():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)

    return redirect("main:show_projects")


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
        "is_editor": _is_editor(request.user),
    }
    return render(request, "education.html", context)


@login_required(login_url="main:login")
def create_education(request):
    _require_superuser(request)
    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pendidikan baru berhasil ditambahkan!")
        return redirect("main:show_education")

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "form": form,
    }
    return render(request, "education_form.html", context)


@login_required(login_url="main:login")
def update_education(request, education_id):
    _require_editor_or_owner(request)
    education = get_object_or_404(Education, pk=education_id)
    form = EducationForm(request.POST or None, instance=education)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Data pendidikan berhasil diubah!")
        return redirect("main:show_education")

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "form": form,
        "education": education,
        "is_update": True,
    }
    return render(request, "education_form.html", context)


@login_required(login_url="main:login")
@require_POST
def delete_education(request, education_id):
    _require_superuser(request)
    education = get_object_or_404(Education, pk=education_id)
    education.delete()
    messages.success(request, "Data pendidikan berhasil dihapus!")
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
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "form": form,
    }
    return render(request, "register.html", context)


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": OWNER_NAME,
        "nickname": OWNER_NICKNAME,
        "form": form,
    }
    return render(request, "login.html", context)


def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response
