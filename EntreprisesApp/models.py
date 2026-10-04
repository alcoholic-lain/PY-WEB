import secrets
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


def generate_user_id():
    """Generate a random 8-char id (A-Z, 0-9) for Utilisateur.user_id."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class UtilisateurManager(UserManager):
    """Default UserManager already handles create_user; we only make
    sure superusers get the 'admin' role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Utilisateur.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        CHARGEUR = "chargeur", "Chargeur"
        TRANSPORTEUR = "transporteur", "Transporteur"
        ADMIN = "admin", "Administrateur"

    # Custom PK replacing the default `id`
    user_id = models.CharField(
        max_length=8, primary_key=True, default=generate_user_id, editable=False
    )
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CHARGEUR
    )  # set by the signup view depending on the registration form
    telephone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UtilisateurManager()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class Entreprise(models.Model):
    class Type(models.TextChoices):
        CHARGEUR = "chargeur", "Chargeur"
        TRANSPORTEUR = "transporteur", "Transporteur"

    raison_sociale = models.CharField(max_length=150)
    matricule_fiscal = models.CharField(max_length=17, unique=True)
    type_entreprise = models.CharField(max_length=20, choices=Type.choices)
    adresse = models.TextField()
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="entreprise",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.raison_sociale} ({self.type_entreprise})"