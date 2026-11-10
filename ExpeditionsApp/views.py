from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

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
    pk_url_kwarg = "expedition_id"


class ExpeditionCreateView(LoginRequiredMixin, CreateView):
    model = Expedition
    fields = (
        "ville_depart",
        "ville_arrivee",
        "poids_kg",
        "date_souhaitee",
        "description",
        "entreprise",
    )
    template_name = "expedition/form.html"
    success_url = reverse_lazy("expedition:lister")
    login_url = reverse_lazy("admin:login")


class ExpeditionUpdateView(LoginRequiredMixin, UpdateView):
    model = Expedition
    fields = ExpeditionCreateView.fields + ("statut",)
    template_name = "expedition/form.html"
    pk_url_kwarg = "expedition_id"
    success_url = reverse_lazy("expedition:lister")
    login_url = reverse_lazy("admin:login")


class ExpeditionDeleteView(LoginRequiredMixin, DeleteView):
    model = Expedition
    template_name = "expedition/delete.html"
    pk_url_kwarg = "expedition_id"
    success_url = reverse_lazy("expedition:lister")
    login_url = reverse_lazy("admin:login")
