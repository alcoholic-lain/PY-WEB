from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from ExpeditionsApp.models import Expedition
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
