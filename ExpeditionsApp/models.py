from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from EntreprisesApp.models import Entreprise


def generate_reference():
    """Format EXP-AA-NNNNN : AA = 2 derniers chiffres de l'année de création,
    NNNNN = compteur 00001-99999 remis à zéro chaque année.
    Appelée depuis save() (elle interroge la base)."""
    prefix = f"EXP-{timezone.now().strftime('%y')}-"
    derniere = (
        Expedition.objects.filter(reference__startswith=prefix)
        .order_by("-reference")
        .values_list("reference", flat=True)
        .first()
    )
    n = int(derniere[len(prefix):]) + 1 if derniere else 1
    if n > 99999:
        raise ValidationError("Limite atteinte : 99999 expéditions maximum par an.")
    return f"{prefix}{n:05d}"


class Expedition(models.Model):
    class Statut(models.TextChoices):
        PUBLIEE = "publiee", "Publiée"
        ATTRIBUEE = "attribuee", "Attribuée"
        EN_COURS = "en_cours", "En cours"
        LIVREE = "livree", "Livrée"
        ANNULEE = "annulee", "Annulée"

    reference = models.CharField(max_length=12, unique=True, editable=False, blank=True)
    ville_depart = models.CharField(max_length=100)
    ville_arrivee = models.CharField(max_length=100)
    poids_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"), "Le poids ne peut pas être nul.")],
    )
    date_souhaitee = models.DateField()
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PUBLIEE)
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name="expeditions",
        limit_choices_to={"type_entreprise": Entreprise.Type.CHARGEUR},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(poids_kg__gt=0),
                name="expedition_poids_kg_gt_0",
            )
        ]

    def clean(self):
        if self.entreprise_id and Entreprise.objects.filter(
            pk=self.entreprise_id
        ).exclude(type_entreprise=Entreprise.Type.CHARGEUR).exists():
            raise ValidationError(
                {"entreprise": "Une expédition doit être publiée par une entreprise chargeur."}
            )

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference}: {self.ville_depart} → {self.ville_arrivee}"