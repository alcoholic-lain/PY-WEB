from django.urls import reverse_lazy

from config.crud import (
    ResourceCreateView,
    ResourceDeleteView,
    ResourceDetailView,
    ResourceListView,
    ResourceUpdateView,
)
from .forms import EntrepriseForm
from .models import Entreprise


class EntrepriseListView(ResourceListView):
    model = Entreprise
    queryset = Entreprise.objects.order_by("raison_sociale")
    resource_name = "entreprise"
    page_title = "Entreprises"
    page_intro = "Gérez les entreprises chargeurs et transporteurs."
    list_url_name = "entreprise:lister"
    create_url_name = "entreprise:create"
    detail_url_name = "entreprise:detail"


class EntrepriseDetailView(ResourceDetailView):
    model = Entreprise
    queryset = Entreprise.objects.select_related("utilisateur")
    resource_name = "entreprise"
    page_title = "Détail de l'entreprise"
    list_url_name = "entreprise:lister"
    detail_fields = (
        ("raison_sociale", "Raison sociale"),
        ("matricule_fiscal", "Matricule fiscal"),
        ("type_entreprise", "Type"),
        ("adresse", "Adresse"),
        ("utilisateur", "Compte associé"),
    )
    update_url_name = "entreprise:update"
    delete_url_name = "entreprise:delete"


class EntrepriseCreateView(ResourceCreateView):
    model = Entreprise
    form_class = EntrepriseForm
    resource_name = "entreprise"
    page_title = "Créer une entreprise"
    page_intro = "Renseignez les informations de l'entreprise."
    form_intro = page_intro
    list_url_name = "entreprise:lister"
    cancel_url_name = list_url_name
    success_url = reverse_lazy("entreprise:lister")


class EntrepriseUpdateView(ResourceUpdateView):
    model = Entreprise
    form_class = EntrepriseForm
    resource_name = "entreprise"
    page_title = "Modifier une entreprise"
    page_intro = "Mettez à jour les informations de l'entreprise."
    form_intro = page_intro
    list_url_name = "entreprise:lister"
    cancel_url_name = list_url_name
    success_url = reverse_lazy("entreprise:lister")


class EntrepriseDeleteView(ResourceDeleteView):
    model = Entreprise
    resource_name = "entreprise"
    page_title = "Supprimer cette entreprise ?"
    page_intro = "Vous êtes sur le point de supprimer cette entreprise."
    list_url_name = "entreprise:lister"
    success_url = reverse_lazy("entreprise:lister")
    delete_warning = (
        "Cette action supprimera également les véhicules, expéditions et offres liés."
    )
