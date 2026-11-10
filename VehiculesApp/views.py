from django.urls import reverse_lazy

from config.crud import (
    ResourceCreateView,
    ResourceDeleteView,
    ResourceDetailView,
    ResourceListView,
    ResourceUpdateView,
)
from .models import Vehicule


class VehiculeListView(ResourceListView):
    model = Vehicule
    queryset = Vehicule.objects.select_related("entreprise").order_by("immatriculation")
    resource_name = "véhicule"
    page_title = "Véhicules"
    page_intro = "Consultez et gérez les véhicules des transporteurs."
    list_url_name = "vehicule:lister"
    create_url_name = "vehicule:create"
    detail_url_name = "vehicule:detail"


class VehiculeDetailView(ResourceDetailView):
    model = Vehicule
    queryset = Vehicule.objects.select_related("entreprise")
    resource_name = "véhicule"
    page_title = "Détail du véhicule"
    list_url_name = "vehicule:lister"
    detail_fields = (
        ("immatriculation", "Immatriculation"),
        ("type_vehicule", "Type"),
        ("capacite_kg", "Capacité (kg)"),
        ("disponible", "Disponible"),
        ("entreprise", "Transporteur"),
    )
    update_url_name = "vehicule:update"
    delete_url_name = "vehicule:delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        available = not self.object.offres.exists()
        context["can_update"] = available
        context["can_delete"] = available
        return context


class VehiculeCreateView(ResourceCreateView):
    model = Vehicule
    fields = ("immatriculation", "type_vehicule", "capacite_kg", "disponible", "entreprise")
    resource_name = "véhicule"
    page_title = "Créer un véhicule"
    page_intro = "Renseignez les caractéristiques du véhicule."
    form_intro = page_intro
    list_url_name = "vehicule:lister"
    cancel_url_name = list_url_name
    success_url = reverse_lazy("vehicule:lister")


class VehiculeUpdateView(ResourceUpdateView):
    model = Vehicule
    fields = ("immatriculation", "type_vehicule", "capacite_kg", "disponible", "entreprise")
    queryset = Vehicule.objects.filter(offres__isnull=True)
    resource_name = "véhicule"
    page_title = "Modifier un véhicule"
    page_intro = "Mettez à jour les caractéristiques du véhicule."
    form_intro = page_intro
    list_url_name = "vehicule:lister"
    cancel_url_name = list_url_name
    success_url = reverse_lazy("vehicule:lister")


class VehiculeDeleteView(ResourceDeleteView):
    model = Vehicule
    queryset = Vehicule.objects.filter(offres__isnull=True)
    resource_name = "véhicule"
    page_title = "Supprimer ce véhicule ?"
    page_intro = "Vous êtes sur le point de supprimer ce véhicule."
    list_url_name = "vehicule:lister"
    success_url = reverse_lazy("vehicule:lister")
    delete_warning = "Un véhicule lié à une offre ne peut pas être supprimé."
