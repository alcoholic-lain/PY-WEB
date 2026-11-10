from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView

from .models import Expedition


def home(request):
    return HttpResponse("Bienvenue sur TransConnect.")


def afficher(request, name):
    return render(request, "expedition/afficher.html", {"name": name})


def lister(request):
    expeditions = Expedition.objects.order_by("-created_at")
    return render(request, "expedition/lister.html", {"expeditions": expeditions})


class ExpeditionDetailView(DetailView):
    model = Expedition
    template_name = "expedition/detail.html"
    context_object_name = "expedition"
    pk_url_kwarg = "expedition_id"
