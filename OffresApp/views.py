from django.urls import reverse_lazy

from config.crud import (
    ResourceCreateView,
    ResourceDeleteView,
    ResourceDetailView,
    ResourceListView,
    ResourceUpdateView,
)
from .models import Offre


class OffreListView(ResourceListView):
    model = Offre
    queryset = Offre.objects.select_related(
        "expedition", "transporteur", "vehicule"
    ).order_by("-date_proposition", "-pk")
    resource_name = "offre"
    page_title = "Offres"
    page_intro = "Consultez les propositions des transporteurs."
    list_url_name = "offre:lister"
    create_url_name = "offre:create"
    detail_url_name = "offre:detail"


class OffreDetailView(ResourceDetailView):
    model = Offre
    queryset = Offre.objects.select_related(
        "expedition", "transporteur", "vehicule"
    )
    resource_name = "offre"
    page_title = "Détail de l'offre"
    list_url_name = "offre:lister"
    detail_fields = (
        ("expedition", "Expédition"),
        ("transporteur", "Transporteur"),
        ("vehicule", "Véhicule"),
        ("prix", "Prix"),
        ("delai_jours", "Délai (jours)"),
        ("statut", "Statut"),
        ("date_proposition", "Date de proposition"),
    )
    update_url_name = "offre:update"
    delete_url_name = "offre:delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modifiable = self.object.statut != Offre.Statut.ACCEPTEE
        context["can_update"] = modifiable
        context["can_delete"] = modifiable
        return context


class OffreCreateView(ResourceCreateView):
    model = Offre
    fields = ("prix", "delai_jours", "expedition", "transporteur", "vehicule")
    resource_name = "offre"
    page_title = "Créer une offre"
    page_intro = "Proposez un tarif et un délai pour une expédition publiée."
    form_intro = page_intro
    list_url_name = "offre:lister"
    cancel_url_name = list_url_name
    success_url = reverse_lazy("offre:lister")


class OffreUpdateView(ResourceUpdateView):
    model = Offre
    fields = ("prix", "delai_jours", "expedition", "transporteur", "vehicule", "statut")
    queryset = Offre.objects.exclude(statut=Offre.Statut.ACCEPTEE)
    resource_name = "offre"
    page_title = "Modifier une offre"
    page_intro = "Mettez à jour la proposition ou son statut."
    form_intro = page_intro
    list_url_name = "offre:lister"
    cancel_url_name = list_url_name
    success_url = reverse_lazy("offre:lister")


class OffreDeleteView(ResourceDeleteView):
    model = Offre
    queryset = Offre.objects.exclude(statut=Offre.Statut.ACCEPTEE)
    resource_name = "offre"
    page_title = "Supprimer cette offre ?"
    page_intro = "Vous êtes sur le point de supprimer cette offre."
    list_url_name = "offre:lister"
    success_url = reverse_lazy("offre:lister")
    delete_warning = "Une offre acceptée ne peut pas être modifiée ou supprimée."
