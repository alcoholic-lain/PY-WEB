from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from EntreprisesApp.models import Entreprise, Utilisateur
from ExpeditionsApp.models import Expedition


class ExpeditionPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = Utilisateur.objects.create_user(
            username="shipper",
            email="shipper@gmail.com",
            password="test-password",
        )
        company = Entreprise.objects.create(
            raison_sociale="Chargeur de test",
            matricule_fiscal="1234567AAM001",
            type_entreprise=Entreprise.Type.CHARGEUR,
            adresse="12 Avenue Habib Bourguiba, Tunis 1000",
            utilisateur=user,
        )
        cls.expedition = Expedition.objects.create(
            ville_depart="Tunis",
            ville_arrivee="Sfax",
            poids_kg=Decimal("1200.00"),
            date_souhaitee=date(2026, 12, 1),
            entreprise=company,
        )

    def test_list_shows_expedition_link(self):
        response = self.client.get(reverse("expedition:lister"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.expedition.reference)
        self.assertContains(
            response,
            reverse("expedition:detail", args=[self.expedition.pk]),
        )

    def test_detail_shows_expedition(self):
        response = self.client.get(
            reverse("expedition:detail", args=[self.expedition.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tunis")
        self.assertContains(response, "Sfax")

    def test_missing_expedition_returns_not_found(self):
        response = self.client.get(reverse("expedition:detail", args=[999]))

        self.assertEqual(response.status_code, 404)

    def test_home_and_greeting_pages_load(self):
        self.assertEqual(self.client.get(reverse("expedition:home")).status_code, 200)
        self.assertContains(
            self.client.get(reverse("expedition:afficher", args=["TransConnect"])),
            "TransConnect",
        )
