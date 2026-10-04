from django.core.exceptions import ValidationError
from django.db import models


class Offre(models.Model):
    class Statut(models.TextChoices):
        PROPOSEE = "proposee", "Proposée"
        ACCEPTEE = "acceptee", "Acceptée"
        REFUSEE = "refusee", "Refusée"
        RETIREE = "retiree", "Retirée"

    prix = models.DecimalField(max_digits=10, decimal_places=2)          # fix 1
    delai_jours = models.PositiveIntegerField()                          # fix 2
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.PROPOSEE
    )
    date_proposition = models.DateField(auto_now_add=True)               # fix 3
    expedition = models.ForeignKey(
        "ExpeditionsApp.Expedition",
        on_delete=models.CASCADE,
        related_name="offres",
    )
    transporteur = models.ForeignKey(
        "EntreprisesApp.Entreprise",
        on_delete=models.CASCADE,
        related_name="offres",
        limit_choices_to={"type_entreprise": "transporteur"},
    )
    vehicule = models.ForeignKey(                                        # fix 4
        "VehiculesApp.Vehicule",
        on_delete=models.PROTECT,
        related_name="offres",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # The vehicle must belong to the offering carrier
        if self.vehicule_id and self.transporteur_id:
            if self.vehicule.entreprise_id != self.transporteur_id:
                raise ValidationError(
                    "Ce véhicule n'appartient pas à ce transporteur."
                )

    def __str__(self):
        return f"Offre {self.prix} DT / {self.delai_jours} j ({self.statut})"