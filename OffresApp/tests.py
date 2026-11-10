from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from EntreprisesApp.models import Entreprise, Utilisateur
from ExpeditionsApp.models import Expedition
from OffresApp.models import Offre
from VehiculesApp.models import Vehicule

ADRESSE = "12 avenue Habib Bourguiba, Tunis 1000"


def make_user(name, role="chargeur", email=None):
    return Utilisateur.objects.create_user(
        username=name, email=email or f"{name}@gmail.com", password="pw12345!", role=role
    )


def make_entreprise(name, type_, matricule):
    return Entreprise.objects.create(
        raison_sociale=name,
        matricule_fiscal=matricule,
        type_entreprise=type_,
        adresse=ADRESSE,
        utilisateur=make_user(name, role=type_),
    )


class BaseCase(TestCase):
    def setUp(self):
        self.chargeur = make_entreprise("chg", "chargeur", "1234567AAM000")
        self.t1 = make_entreprise("tr1", "transporteur", "1234568AAM000")
        self.t2 = make_entreprise("tr2", "transporteur", "1234569AAM000")
        self.v1 = Vehicule.objects.create(
            immatriculation="111 TUN 1", type_vehicule="camion_porteur",
            capacite_kg=10000, entreprise=self.t1)
        self.v2 = Vehicule.objects.create(
            immatriculation="222 TUN 2", type_vehicule="camion_porteur",
            capacite_kg=10000, entreprise=self.t2)
        self.exp = Expedition.objects.create(
            ville_depart="Tunis", ville_arrivee="Sfax", poids_kg=Decimal("2000"),
            date_souhaitee=date(2026, 12, 1), entreprise=self.chargeur)

    def offre(self, **kw):
        data = dict(prix=Decimal("500"), delai_jours=2, expedition=self.exp,
                    transporteur=self.t1, vehicule=self.v1)
        data.update(kw)
        return Offre(**data)


class IdentifiantsEtValidateurs(BaseCase):
    def test_user_id_format_et_compteur(self):
        yy = timezone.now().strftime("%y")
        ids = sorted(Utilisateur.objects.values_list("user_id", flat=True))
        self.assertEqual(ids[0], f"{yy}user00")
        self.assertEqual(ids[1], f"{yy}user01")
        self.assertEqual(len(ids[0]), 8)

    def test_email_gmail_uniquement(self):
        with self.assertRaises(ValidationError):
            make_user("bad", email="bad@yahoo.fr")

    def test_email_gmail_doit_avoir_un_format_valide(self):
        with self.assertRaises(ValidationError):
            make_user("bad_format", email="bad@@gmail.com")

    def test_reference_expedition(self):
        yy = timezone.now().strftime("%y")
        self.assertEqual(self.exp.reference, f"EXP-{yy}-00001")

    def test_matricule_normalise_et_unique(self):
        with self.assertRaises(ValidationError):  # même matricule, autre format
            make_entreprise("dup", "chargeur", "1234567/a/a/m/000")

    def test_adresse_trop_courte(self):
        with self.assertRaises(ValidationError):
            Entreprise.objects.create(
                raison_sociale="x", matricule_fiscal="7654321AAM000",
                type_entreprise="chargeur", adresse="trop court",
                utilisateur=make_user("short"))

    def test_poids_et_capacite_nuls(self):
        with self.assertRaises(ValidationError):
            Expedition.objects.create(
                ville_depart="a", ville_arrivee="b", poids_kg=0,
                date_souhaitee=date(2026, 12, 1), entreprise=self.chargeur)
        with self.assertRaises(ValidationError):
            Vehicule.objects.create(
                immatriculation="X", type_vehicule="fourgon", capacite_kg=0,
                entreprise=self.t1)

    def test_prix_et_delai(self):
        with self.assertRaises(ValidationError):
            self.offre(prix=Decimal("0")).save()
        with self.assertRaises(ValidationError):
            self.offre(delai_jours=0).save()

    def test_vehicule_chez_chargeur_refuse(self):
        with self.assertRaises(ValidationError):
            Vehicule.objects.create(
                immatriculation="Y", type_vehicule="fourgon", capacite_kg=100,
                entreprise=self.chargeur)

    def test_vehicule_refuse_apres_changement_du_type_entreprise(self):
        Entreprise.objects.filter(pk=self.t1.pk).update(type_entreprise="chargeur")
        with self.assertRaises(ValidationError):
            Vehicule.objects.create(
                immatriculation="STALE", type_vehicule="fourgon", capacite_kg=100,
                entreprise=self.t1)

    def test_expedition_chez_transporteur_refusee(self):
        with self.assertRaises(ValidationError):
            Expedition.objects.create(
                ville_depart="a", ville_arrivee="b", poids_kg=10,
                date_souhaitee=date(2026, 12, 1), entreprise=self.t1)

    def test_expedition_refuse_apres_changement_du_type_entreprise(self):
        Entreprise.objects.filter(pk=self.chargeur.pk).update(
            type_entreprise="transporteur"
        )
        with self.assertRaises(ValidationError):
            Expedition.objects.create(
                ville_depart="a", ville_arrivee="b", poids_kg=10,
                date_souhaitee=date(2026, 12, 1), entreprise=self.chargeur)


class ReglesMetier(BaseCase):
    def test_r1_chargeur_ne_peut_pas_offrir(self):
        v = Vehicule.objects.create(
            immatriculation="Z", type_vehicule="fourgon", capacite_kg=100,
            entreprise=self.t1)
        with self.assertRaises(ValidationError):
            self.offre(transporteur=self.chargeur, vehicule=v).save()

    def test_r2_vehicule_autre_entreprise(self):
        with self.assertRaises(ValidationError):
            self.offre(vehicule=self.v2).save()

    def test_r3_expedition_non_publiee(self):
        self.exp.statut = "en_cours"
        self.exp.save()
        with self.assertRaises(ValidationError):
            self.offre().save()

    def test_r3_refuse_expedition_modifiee_en_base(self):
        Expedition.objects.filter(pk=self.exp.pk).update(statut="attribuee")
        with self.assertRaises(ValidationError):
            self.offre().save()

    def test_r4_deux_offres_proposees(self):
        self.offre().save()
        with self.assertRaises(ValidationError):
            self.offre().save()

    def test_r4_ok_si_premiere_retiree(self):
        o = self.offre()
        o.save()
        o.statut = "retiree"
        o.save()
        self.offre().save()  # autorisé

    def test_r5_cascade_acceptation(self):
        o1 = self.offre()
        o1.save()
        o2 = self.offre(transporteur=self.t2, vehicule=self.v2)
        o2.save()
        o1.statut = "acceptee"
        o1.save()
        self.exp.refresh_from_db()
        o1.refresh_from_db()
        o2.refresh_from_db()
        self.assertEqual(self.exp.statut, "attribuee")
        self.assertEqual(o1.statut, "acceptee")
        self.assertEqual(o2.statut, "refusee")

    def test_r5_resauvegarde_offre_acceptee(self):
        o1 = self.offre()
        o1.save()
        o1.statut = "acceptee"
        o1.save()
        o1.save()  # ne doit pas lever d'erreur

    def test_r5_une_seule_offre_peut_etre_acceptee(self):
        o1 = self.offre()
        o1.save()
        o1.statut = "acceptee"
        o1.save()

        o2 = self.offre(transporteur=self.t2, vehicule=self.v2)
        o2.statut = "acceptee"
        with self.assertRaises(ValidationError):
            o2.save()

    def test_r6_vehicule_indisponible(self):
        self.v1.disponible = False
        self.v1.save()
        with self.assertRaises(ValidationError):
            self.offre().save()

    def test_r6_refuse_vehicule_rendu_indisponible_en_base(self):
        Vehicule.objects.filter(pk=self.v1.pk).update(disponible=False)
        with self.assertRaises(ValidationError):
            self.offre().save()

    def test_r7_poids_vs_type(self):
        petit = Vehicule.objects.create(
            immatriculation="P", type_vehicule="camionnette", capacite_kg=1500,
            entreprise=self.t1)
        with self.assertRaises(ValidationError):  # 2000 kg > 1500 kg
            self.offre(vehicule=petit).save()

    def test_r7_poids_vs_capacite(self):
        faible = Vehicule.objects.create(
            immatriculation="F", type_vehicule="camion_porteur", capacite_kg=1000,
            entreprise=self.t1)
        with self.assertRaises(ValidationError):
            self.offre(vehicule=faible).save()


class OffreCRUDTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.t1.utilisateur)

    def test_offer_list_and_detail(self):
        offer = self.offre()
        offer.save()
        self.assertContains(self.client.get(reverse("offre:lister")), str(offer.prix))
        self.assertContains(
            self.client.get(reverse("offre:detail", args=[offer.pk])),
            self.exp.reference,
        )

    def test_offer_create_update_and_delete(self):
        response = self.client.post(
            reverse("offre:create"),
            {
                "prix": "650.00",
                "delai_jours": 3,
                "expedition": self.exp.pk,
                "transporteur": self.t1.pk,
                "vehicule": self.v1.pk,
            },
        )
        self.assertRedirects(response, reverse("offre:lister"))
        offer = Offre.objects.get(transporteur=self.t1, expedition=self.exp)

        response = self.client.post(
            reverse("offre:update", args=[offer.pk]),
            {
                "prix": "700.00",
                "delai_jours": 4,
                "expedition": self.exp.pk,
                "transporteur": self.t1.pk,
                "vehicule": self.v1.pk,
                "statut": Offre.Statut.RETIREE,
            },
        )
        self.assertRedirects(response, reverse("offre:lister"))
        offer.refresh_from_db()
        self.assertEqual(offer.prix, Decimal("700.00"))
        self.assertEqual(offer.statut, Offre.Statut.RETIREE)

        response = self.client.post(reverse("offre:delete", args=[offer.pk]))
        self.assertRedirects(response, reverse("offre:lister"))
        self.assertFalse(Offre.objects.filter(pk=offer.pk).exists())

    def test_accepted_offer_cannot_be_updated_or_deleted(self):
        offer = self.offre()
        offer.save()
        offer.statut = Offre.Statut.ACCEPTEE
        offer.save()

        self.assertEqual(
            self.client.get(reverse("offre:update", args=[offer.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("offre:delete", args=[offer.pk])).status_code,
            404,
        )
        self.assertNotContains(
            self.client.get(reverse("offre:detail", args=[offer.pk])),
            "Modifier",
        )

    def test_vehicle_with_offer_cannot_be_updated_or_deleted(self):
        offer = self.offre()
        offer.save()

        self.assertEqual(
            self.client.get(reverse("vehicule:update", args=[self.v1.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("vehicule:delete", args=[self.v1.pk])).status_code,
            404,
        )
