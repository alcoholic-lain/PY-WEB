from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from ExpeditionsApp.models import Expedition
from EntreprisesApp.models import Entreprise, Utilisateur
from OffresApp.models import Offre


class AdminIntegrityDashboardTests(TestCase):
    def test_dashboard_requires_admin_access(self):
        response = self.client.get(reverse("admin:health_check"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_dashboard_displays_integrity_checks(self):
        user = get_user_model()(
            username="admin",
            email="admin@gmail.com",
            is_staff=True,
            is_superuser=True,
        )
        user.set_password("test-password")
        user.save()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de bord de contrôle d'intégrité")
        self.assertContains(response, "Offres orphelines")


class SeedDemoCommandTests(TestCase):
    def test_seed_creates_demo_records_without_login_passwords(self):
        call_command("seed_demo", stdout=StringIO())

        self.assertEqual(get_user_model().objects.filter(username__startswith="demo_").count(), 3)
        self.assertEqual(Expedition.objects.count(), 2)
        self.assertEqual(Offre.objects.count(), 4)
        demo_user = get_user_model().objects.get(username="demo_chargeur")
        self.assertFalse(demo_user.has_usable_password())

    def test_seed_requires_explicit_reset_for_existing_demo_data(self):
        call_command("seed_demo", stdout=StringIO())

        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=StringIO())

        call_command("seed_demo", reset=True, stdout=StringIO())
        self.assertEqual(get_user_model().objects.filter(username__startswith="demo_").count(), 3)
        self.assertEqual(Expedition.objects.count(), 2)
        self.assertEqual(Offre.objects.count(), 4)


class EntrepriseCRUDTests(TestCase):
    def setUp(self):
        self.owner = Utilisateur.objects.create_user(
            username="company_owner",
            email="company_owner@gmail.com",
            password="test-password",
        )
        self.company = Entreprise.objects.create(
            raison_sociale="Transport Test",
            matricule_fiscal="1234567AAM001",
            type_entreprise=Entreprise.Type.TRANSPORTEUR,
            adresse="12 avenue Habib Bourguiba, Tunis 1000",
            utilisateur=self.owner,
        )
        self.available_user = Utilisateur.objects.create_user(
            username="available_owner",
            email="available_owner@gmail.com",
            password="test-password",
        )
        self.client.force_login(self.owner)

    def test_company_list_and_detail(self):
        self.assertContains(
            self.client.get(reverse("entreprise:lister")),
            self.company.raison_sociale,
        )
        response = self.client.get(
            reverse("entreprise:detail", args=[self.company.pk])
        )
        self.assertContains(response, self.company.matricule_fiscal)

    def test_company_create_update_and_delete(self):
        response = self.client.post(
            reverse("entreprise:create"),
            {
                "raison_sociale": "Nouveau transport",
                "matricule_fiscal": "2345678AAM002",
                "type_entreprise": Entreprise.Type.TRANSPORTEUR,
                "adresse": "24 rue de la Paix, Sfax 3000",
                "utilisateur": self.available_user.pk,
            },
        )
        self.assertRedirects(response, reverse("entreprise:lister"))
        company = Entreprise.objects.get(raison_sociale="Nouveau transport")

        response = self.client.post(
            reverse("entreprise:update", args=[company.pk]),
            {
                "raison_sociale": "Transport actualisé",
                "matricule_fiscal": company.matricule_fiscal,
                "type_entreprise": company.type_entreprise,
                "adresse": "24 rue de la Paix, Sfax 3000",
                "utilisateur": self.available_user.pk,
            },
        )
        self.assertRedirects(response, reverse("entreprise:lister"))
        company.refresh_from_db()
        self.assertEqual(company.raison_sociale, "Transport actualisé")

        response = self.client.post(reverse("entreprise:delete", args=[company.pk]))
        self.assertRedirects(response, reverse("entreprise:lister"))
        self.assertFalse(Entreprise.objects.filter(pk=company.pk).exists())
        self.assertTrue(Utilisateur.objects.filter(pk=self.available_user.pk).exists())

    def test_company_form_only_offers_unassigned_accounts(self):
        response = self.client.get(reverse("entreprise:create"))

        self.assertContains(response, self.available_user.username)
        self.assertNotContains(response, self.owner.username)

    def test_company_mutations_require_login(self):
        self.client.logout()

        response = self.client.get(reverse("entreprise:create"))

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('entreprise:create')}",
        )
