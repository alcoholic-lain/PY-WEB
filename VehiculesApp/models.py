from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from EntreprisesApp.models import Entreprise


class Vehicule(models.Model):
    class TypeVehicule(models.TextChoices):
        CAMIONNETTE = "camionnette", "Camionnette / utilitaire léger"
        FOURGON = "fourgon", "Fourgon"
        CAMION_PORTEUR = "camion_porteur", "Camion porteur"
        SEMI_REMORQUE = "semi_remorque", "Semi-remorque"

    # Charge maximale (kg) par gabarit, d'après la capacité indicative de l'énoncé
    POIDS_MAX_KG = {
        TypeVehicule.CAMIONNETTE: 1500,       # jusqu'à ~1,5 t
        TypeVehicule.FOURGON: 3500,           # ~3,5 t
        TypeVehicule.CAMION_PORTEUR: 19000,   # ~3,5 à 19 t
        TypeVehicule.SEMI_REMORQUE: 26000,    # ~19 à 26 t
    }

    immatriculation = models.CharField(max_length=20, unique=True)
    type_vehicule = models.CharField(max_length=20, choices=TypeVehicule.choices)
    capacite_kg = models.PositiveIntegerField(
        validators=[MinValueValidator(1, "La capacité ne peut pas être nulle.")]
    )
    disponible = models.BooleanField(default=True)
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name="vehicules",
        limit_choices_to={"type_entreprise": Entreprise.Type.TRANSPORTEUR},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacite_kg__gt=0),
                name="vehicule_capacite_kg_gt_0",
            )
        ]

    def clean(self):
        if self.entreprise_id and Entreprise.objects.filter(
            pk=self.entreprise_id
        ).exclude(type_entreprise=Entreprise.Type.TRANSPORTEUR).exists():
            raise ValidationError(
                {"entreprise": "Un véhicule doit appartenir à une entreprise transporteur."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.immatriculation} ({self.get_type_vehicule_display()})"