from django.shortcuts import render

from main.models import Experience, Project


def show_main(request):
    context = {
        "name": "Niccola Geraldo Winaryo Durand",
        "nickname": "NicoGWD",
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
        "name": "Niccola Geraldo Winaryo Durand",
        "nickname": "NicoGWD",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def show_projects(request):
    context = {
        "name": "Niccola Geraldo Winaryo Durand",
        "nickname": "NicoGWD",
        "project_list": Project.objects.all(),
    }
    return render(request, "projects.html", context)