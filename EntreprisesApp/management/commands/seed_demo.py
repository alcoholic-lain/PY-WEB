from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from EntreprisesApp.models import Entreprise, Utilisateur
from ExpeditionsApp.models import Expedition
from OffresApp.models import Offre
from VehiculesApp.models import Vehicule

DEMO_USERNAMES = (
    "demo_chargeur",
    "demo_transporteur_nord",
    "demo_transporteur_sud",
)


class Command(BaseCommand):
    help = "Create sample TransConnect companies, vehicles, expeditions, and offers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo accounts and their related data before seeding.",
        )

    def handle(self, *args, **options):
        existing_demo_users = Utilisateur.objects.filter(username__in=DEMO_USERNAMES)
        if existing_demo_users.exists() and not options["reset"]:
            raise CommandError(
                "Demo accounts already exist. Pass --reset to delete and recreate "
                "those accounts and their related data."
            )

        with transaction.atomic():
            if options["reset"]:
                deleted = self._delete_existing_demo_data(existing_demo_users)
                if deleted:
                    self.stdout.write(f"Deleted {deleted} existing demo record(s).")
            self._create_demo_data()

        self.stdout.write(self.style.SUCCESS("Demo data created successfully."))

    def _delete_existing_demo_data(self, demo_users):
        demo_companies = Entreprise.objects.filter(utilisateur__in=demo_users)
        demo_expeditions = Expedition.objects.filter(entreprise__in=demo_companies)
        demo_vehicles = Vehicule.objects.filter(entreprise__in=demo_companies)

        Offre.objects.filter(
            Q(transporteur__in=demo_companies)
            | Q(expedition__in=demo_expeditions)
            | Q(vehicule__in=demo_vehicles)
        ).delete()
        demo_expeditions.delete()
        demo_vehicles.delete()
        demo_companies.delete()
        deleted, _ = demo_users.delete()
        return deleted

    def _create_user(self, username, email, role):
        return Utilisateur.objects.create_user(
            username=username,
            email=email,
            password=None,
            role=role,
        )

    def _create_company(self, *, username, email, role, name, tax_id, address):
        user = self._create_user(username, email, role)
        return Entreprise.objects.create(
            raison_sociale=name,
            matricule_fiscal=tax_id,
            type_entreprise=role,
            adresse=address,
            utilisateur=user,
        )

    def _create_demo_data(self):
        shipper = self._create_company(
            username=DEMO_USERNAMES[0],
            email="demo.chargeur@gmail.com",
            role=Entreprise.Type.CHARGEUR,
            name="Chargeur Demo SARL",
            tax_id="1111111AAM001",
            address="12 Avenue Habib Bourguiba, 1000 Tunis, Tunisie",
        )
        carriers = [
            self._create_company(
                username=username,
                email=email,
                role=Entreprise.Type.TRANSPORTEUR,
                name=name,
                tax_id=tax_id,
                address=address,
            )
            for username, email, name, tax_id, address in (
                (
                    DEMO_USERNAMES[1],
                    "demo.transporteur.nord@gmail.com",
                    "Transport Demo Nord",
                    "2222222AAM002",
                    "45 Route de Bizerte, 2000 Ariana, Tunisie",
                ),
                (
                    DEMO_USERNAMES[2],
                    "demo.transporteur.sud@gmail.com",
                    "Transport Demo Sud",
                    "3333333AAM003",
                    "78 Route de Gabès, 3000 Sfax, Tunisie",
                ),
            )
        ]
        vehicles = [
            Vehicule.objects.create(
                immatriculation=registration,
                type_vehicule=Vehicule.TypeVehicule.CAMIONNETTE,
                capacite_kg=1500,
                disponible=True,
                entreprise=carrier,
            )
            for carrier, registration in zip(carriers, ("DEMO-TR-NORD", "DEMO-TR-SUD"))
        ]

        for index, (origin, destination, weight, days, prices) in enumerate(
            (
                ("Tunis", "Sfax", Decimal("1200.00"), 7, (800, 950)),
                ("Sousse", "Gabès", Decimal("800.00"), 10, (600, 680)),
            )
        ):
            expedition = Expedition.objects.create(
                ville_depart=origin,
                ville_arrivee=destination,
                poids_kg=weight,
                date_souhaitee=timezone.now().date() + timedelta(days=days),
                description="Expédition de démonstration TransConnect.",
                entreprise=shipper,
            )
            for carrier, vehicle, price, delay in zip(
                carriers, vehicles, prices, (3, 5)
            ):
                Offre.objects.create(
                    expedition=expedition,
                    transporteur=carrier,
                    vehicule=vehicle,
                    prix=Decimal(price),
                    delai_jours=delay + index,
                )
            if index == 1:
                expedition.statut = Expedition.Statut.EN_COURS
                expedition.save()
