from django.db import models


class Vehicule(models.Model):
    class TypeVehicule(models.TextChoices):
        CAMIONNETTE = "camionnette", "Camionnette"
        FOURGON = "fourgon", "Fourgon"
        CAMION_PORTEUR = "camion_porteur", "Camion porteur"
        SEMI_REMORQUE = "semi_remorque", "Semi-remorque"

    immatriculation = models.CharField(max_length=20, unique=True)
    type_vehicule = models.CharField(max_length=20, choices=TypeVehicule.choices)
    capacite_kg = models.PositiveIntegerField()
    disponible = models.BooleanField(default=True)
    entreprise = models.ForeignKey(
        "EntreprisesApp.Entreprise",
        on_delete=models.CASCADE,
        related_name="vehicules",
        limit_choices_to={"type_entreprise": "transporteur"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.immatriculation} ({self.get_type_vehicule_display()})"