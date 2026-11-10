from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Expedition


def home(request):
    return HttpResponse("Bienvenue sur TransConnect.")


def afficher(request, name):
    return render(request, "expedition/afficher.html", {"name": name})


def lister(request):
    expeditions = Expedition.objects.order_by("-created_at")
    return render(request, "expedition/lister.html", {"expeditions": expeditions})


def detail(request, expedition_id):
    expedition = get_object_or_404(Expedition, pk=expedition_id)
    return render(request, "expedition/detail.html", {"expedition": expedition})
