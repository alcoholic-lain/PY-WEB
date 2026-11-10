from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
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
        cls.company = company
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

    def test_create_and_delete_require_login(self):
        create_response = self.client.get(reverse("expedition:create"))
        update_response = self.client.get(
            reverse("expedition:update", args=[self.expedition.pk])
        )
        delete_response = self.client.get(
            reverse("expedition:delete", args=[self.expedition.pk])
        )

        self.assertRedirects(
            create_response,
            f"{reverse('admin:login')}?next={reverse('expedition:create')}",
        )
        self.assertRedirects(
            update_response,
            f"{reverse('admin:login')}?next="
            f"{reverse('expedition:update', args=[self.expedition.pk])}",
        )
        self.assertRedirects(
            delete_response,
            f"{reverse('admin:login')}?next="
            f"{reverse('expedition:delete', args=[self.expedition.pk])}",
        )

    def test_authenticated_user_can_create_expedition(self):
        user = get_user_model().objects.create_user(
            username="creator",
            email="creator@gmail.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("expedition:create"),
            {
                "ville_depart": "Sousse",
                "ville_arrivee": "Gabes",
                "poids_kg": "450.00",
                "date_souhaitee": "2026-12-10",
                "description": "Nouvelle expédition",
                "entreprise": self.company.pk,
            },
        )

        self.assertRedirects(response, reverse("expedition:lister"))
        self.assertTrue(
            Expedition.objects.filter(
                ville_depart="Sousse",
                entreprise=self.company,
            ).exists()
        )

    def test_authenticated_user_can_update_expedition_and_status(self):
        user = get_user_model().objects.create_user(
            username="editor",
            email="editor@gmail.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("expedition:update", args=[self.expedition.pk]),
            {
                "ville_depart": "Monastir",
                "ville_arrivee": "Sfax",
                "poids_kg": "1200.00",
                "date_souhaitee": "2026-12-01",
                "description": "Expédition modifiée",
                "entreprise": self.company.pk,
                "statut": Expedition.Statut.EN_COURS,
            },
        )

        self.assertRedirects(response, reverse("expedition:lister"))
        self.expedition.refresh_from_db()
        self.assertEqual(self.expedition.ville_depart, "Monastir")
        self.assertEqual(self.expedition.statut, Expedition.Statut.EN_COURS)

    def test_authenticated_user_can_delete_expedition(self):
        user = get_user_model().objects.create_user(
            username="deleter",
            email="deleter@gmail.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("expedition:delete", args=[self.expedition.pk])
        )

        self.assertRedirects(response, reverse("expedition:lister"))
        self.assertFalse(Expedition.objects.filter(pk=self.expedition.pk).exists())

    def test_home_and_greeting_pages_load(self):
        self.assertEqual(self.client.get(reverse("expedition:home")).status_code, 200)
        self.assertContains(
            self.client.get(reverse("expedition:afficher", args=["TransConnect"])),
            "TransConnect",
        )
