from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from EntreprisesApp.models import Entreprise
from ExpeditionsApp.models import Expedition
from OffresApp.models import Offre
from VehiculesApp.models import Vehicule

admin.site.site_header = "TransConnect — Administration"
admin.site.site_title = "TransConnect"
admin.site.index_title = "Administration"


def health_check_view(request):
    orphaned_offers = Offre.objects.filter(
        statut__in=[Offre.Statut.PROPOSEE, Offre.Statut.ACCEPTEE]
    ).exclude(
        expedition__statut__in=[
            Expedition.Statut.PUBLIEE,
            Expedition.Statut.ATTRIBUEE,
        ]
    )
    blocked_expeditions = Expedition.objects.filter(
        statut=Expedition.Statut.PUBLIEE,
        created_at__lt=timezone.now() - timedelta(days=7),
    )
    carriers_without_vehicles = (
        Entreprise.objects.filter(type_entreprise=Entreprise.Type.TRANSPORTEUR)
        .annotate(vehicle_count=Count("vehicules"))
        .filter(vehicle_count=0)
    )
    available_assigned_vehicles = Vehicule.objects.filter(
        disponible=True,
        offres__statut=Offre.Statut.ACCEPTEE,
    ).distinct()
    duplicate_proposals = (
        Offre.objects.filter(statut=Offre.Statut.PROPOSEE)
        .values("transporteur__raison_sociale", "expedition__reference")
        .annotate(offer_count=Count("pk"))
        .filter(offer_count__gt=1)
    )

    checks = [
        {
            "title": "Offres orphelines",
            "count": orphaned_offers.count(),
            "items": [
                f"Offre #{offer.pk} — {offer.expedition.reference} — {offer.statut}"
                for offer in orphaned_offers.select_related("expedition")[:20]
            ],
        },
        {
            "title": "Expéditions bloquées",
            "count": blocked_expeditions.count(),
            "items": [
                f"{expedition.reference} — créée le {expedition.created_at:%d/%m/%Y}"
                for expedition in blocked_expeditions[:20]
            ],
        },
        {
            "title": "Transporteurs sans flotte",
            "count": carriers_without_vehicles.count(),
            "items": [
                company.raison_sociale for company in carriers_without_vehicles[:20]
            ],
        },
        {
            "title": "Véhicules disponibles mais affectés",
            "count": available_assigned_vehicles.count(),
            "items": [
                f"{vehicle.immatriculation}"
                for vehicle in available_assigned_vehicles[:20]
            ],
        },
        {
            "title": "Doublons de proposition",
            "count": duplicate_proposals.count(),
            "items": [
                f"{item['transporteur__raison_sociale']} — "
                f"{item['expedition__reference']} — {item['offer_count']} propositions"
                for item in duplicate_proposals[:20]
            ],
        },
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Contrôle d'intégrité",
        "checks": checks,
    }
    return TemplateResponse(request, "admin/health_check.html", context)


_original_admin_get_urls = admin.site.get_urls


def _admin_get_urls():
    custom_urls = [
        path(
            "health-check/",
            admin.site.admin_view(health_check_view),
            name="health_check",
        ),
    ]
    return custom_urls + _original_admin_get_urls()


admin.site.get_urls = _admin_get_urls
