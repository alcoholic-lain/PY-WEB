from django.test import TestCase
from django.urls import reverse

from EntreprisesApp.models import Entreprise, Utilisateur
from VehiculesApp.models import Vehicule


class VehiculeCRUDTests(TestCase):
    def setUp(self):
        self.owner = Utilisateur.objects.create_user(
            username="carrier_owner",
            email="carrier_owner@gmail.com",
            password="test-password",
        )
        self.carrier = Entreprise.objects.create(
            raison_sociale="Transporteur Test",
            matricule_fiscal="1234567AAM001",
            type_entreprise=Entreprise.Type.TRANSPORTEUR,
            adresse="12 avenue Habib Bourguiba, Tunis 1000",
            utilisateur=self.owner,
        )
        self.vehicle = Vehicule.objects.create(
            immatriculation="111 TUN 1",
            type_vehicule=Vehicule.TypeVehicule.CAMION_PORTEUR,
            capacite_kg=10000,
            entreprise=self.carrier,
        )
        self.client.force_login(self.owner)

    def test_vehicle_list_and_detail(self):
        self.assertContains(
            self.client.get(reverse("vehicule:lister")),
            self.vehicle.immatriculation,
        )
        self.assertContains(
            self.client.get(reverse("vehicule:detail", args=[self.vehicle.pk])),
            self.carrier.raison_sociale,
        )

    def test_vehicle_create_update_and_delete(self):
        response = self.client.post(
            reverse("vehicule:create"),
            {
                "immatriculation": "222 TUN 2",
                "type_vehicule": Vehicule.TypeVehicule.FOURGON,
                "capacite_kg": 3000,
                "disponible": "on",
                "entreprise": self.carrier.pk,
            },
        )
        self.assertRedirects(response, reverse("vehicule:lister"))
        vehicle = Vehicule.objects.get(immatriculation="222 TUN 2")

        response = self.client.post(
            reverse("vehicule:update", args=[vehicle.pk]),
            {
                "immatriculation": "333 TUN 3",
                "type_vehicule": Vehicule.TypeVehicule.FOURGON,
                "capacite_kg": 3000,
                "disponible": "on",
                "entreprise": self.carrier.pk,
            },
        )
        self.assertRedirects(response, reverse("vehicule:lister"))
        self.assertTrue(Vehicule.objects.filter(immatriculation="333 TUN 3").exists())

        response = self.client.post(
            reverse("vehicule:delete", args=[vehicle.pk])
        )
        self.assertRedirects(response, reverse("vehicule:lister"))
        self.assertFalse(Vehicule.objects.filter(pk=vehicle.pk).exists())

    def test_vehicle_create_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("vehicule:create"))

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('vehicule:create')}",
        )
