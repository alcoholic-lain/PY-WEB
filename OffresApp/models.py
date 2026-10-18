from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from EntreprisesApp.models import Entreprise
from ExpeditionsApp.models import Expedition
from VehiculesApp.models import Vehicule


class Offre(models.Model):
    class Statut(models.TextChoices):
        PROPOSEE = "proposee", "Proposée"
        ACCEPTEE = "acceptee", "Acceptée"
        REFUSEE = "refusee", "Refusée"
        RETIREE = "retiree", "Retirée"

    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"), "Le prix doit être supérieur à 0.")],
    )
    delai_jours = models.PositiveIntegerField(
        validators=[MinValueValidator(1, "Le délai doit être d'au moins 1 jour.")]
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PROPOSEE)
    date_proposition = models.DateField(auto_now_add=True)
    expedition = models.ForeignKey(
        Expedition, on_delete=models.CASCADE, related_name="offres"
    )
    transporteur = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name="offres",
        limit_choices_to={"type_entreprise": Entreprise.Type.TRANSPORTEUR},
    )
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.PROTECT, related_name="offres"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(prix__gt=0), name="offre_prix_gt_0"
            ),
            models.CheckConstraint(
                condition=models.Q(delai_jours__gte=1), name="offre_delai_jours_gte_1"
            ),
            # Filet de sécurité en base pour la règle 4
            models.UniqueConstraint(
                fields=["expedition", "transporteur"],
                condition=models.Q(statut="proposee"),
                name="offre_unique_proposee_par_transporteur",
                violation_error_message=(
                    "Ce transporteur a déjà une offre active sur cette expédition."
                ),
            ),
            models.UniqueConstraint(
                fields=["expedition"],
                condition=models.Q(statut="acceptee"),
                name="offre_unique_acceptee_par_expedition",
                violation_error_message="Cette expédition a déjà une offre acceptée.",
            ),
        ]

    # ------------------------------------------------------------------
    # Règles métier (section IV)
    # ------------------------------------------------------------------
    def _statut_precedent(self):
        if self._state.adding:
            return None
        return (
            Offre.objects.filter(pk=self.pk).values_list("statut", flat=True).first()
        )

    def clean(self):
        # Les champs obligatoires manquants sont déjà signalés par clean_fields()
        if not (self.expedition_id and self.transporteur_id and self.vehicule_id):
            return

        erreurs = {}

        def ajouter(champ, message):
            erreurs.setdefault(champ, []).append(message)

        transporteur = Entreprise.objects.get(pk=self.transporteur_id)
        vehicule = Vehicule.objects.get(pk=self.vehicule_id)
        exp = Expedition.objects.get(pk=self.expedition_id)
        creation = self._state.adding

        # R1 : seule une entreprise transporteur peut créer une offre
        if transporteur.type_entreprise != Entreprise.Type.TRANSPORTEUR:
            ajouter("transporteur", "Seule une entreprise transporteur peut faire une offre.")

        # R2 : le véhicule appartient au transporteur de l'offre
        if vehicule.entreprise_id != self.transporteur_id:
            ajouter("vehicule", "Ce véhicule n'appartient pas au transporteur de l'offre.")

        # R3 : nouvelles offres uniquement sur une expédition publiée
        if creation and exp.statut != Expedition.Statut.PUBLIEE:
            ajouter("expedition", "Cette expédition n'accepte plus de nouvelles offres (statut non publié).")

        # R4 : pas deux offres 'proposee' du même transporteur sur la même expédition
        if (
            self.statut == self.Statut.PROPOSEE
            and Offre.objects.filter(
                expedition_id=self.expedition_id,
                transporteur_id=self.transporteur_id,
                statut=self.Statut.PROPOSEE,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            ajouter("transporteur", "Ce transporteur a déjà une offre active sur cette expédition.")

        # R6 : véhicule indisponible refusé sur une nouvelle offre
        if creation and not vehicule.disponible:
            ajouter("vehicule", "Ce véhicule n'est pas disponible.")

        # R7 : compatibilité type de véhicule / poids de l'expédition
        poids_max = Vehicule.POIDS_MAX_KG.get(vehicule.type_vehicule, 0)
        if exp.poids_kg > poids_max:
            ajouter(
                "vehicule",
                f"Un véhicule de type « {vehicule.get_type_vehicule_display()} » "
                f"ne peut pas transporter plus de {poids_max} kg.",
            )
        if exp.poids_kg > vehicule.capacite_kg:
            ajouter(
                "vehicule",
                f"La capacité du véhicule ({vehicule.capacite_kg} kg) est inférieure "
                f"au poids de l'expédition ({exp.poids_kg} kg).",
            )

        # R5 (garde) : on n'accepte qu'une offre sur une expédition encore publiée
        if (
            self.statut == self.Statut.ACCEPTEE
            and self._statut_precedent() != self.Statut.ACCEPTEE
            and exp.statut != Expedition.Statut.PUBLIEE
        ):
            ajouter("statut", "Impossible d'accepter : l'expédition n'est plus au statut publiée.")

        if erreurs:
            raise ValidationError(erreurs)

    def save(self, *args, **kwargs):
        with transaction.atomic():  # tout ou rien, cascade comprise
            self.full_clean()
            super().save(*args, **kwargs)
            if self.statut == self.Statut.ACCEPTEE:
                self._cascade_acceptation()

    def _cascade_acceptation(self):
        """R5 : expédition -> attribuee ; autres offres 'proposee' -> refusee."""
        exp = Expedition.objects.get(pk=self.expedition_id)
        if exp.statut != Expedition.Statut.ATTRIBUEE:
            exp.statut = Expedition.Statut.ATTRIBUEE
            exp.save()
        Offre.objects.filter(
            expedition=exp, statut=self.Statut.PROPOSEE
        ).exclude(pk=self.pk).update(
            statut=self.Statut.REFUSEE, updated_at=timezone.now()
        )

    def __str__(self):
        return f"Offre {self.prix} DT / {self.delai_jours} j ({self.statut})"
