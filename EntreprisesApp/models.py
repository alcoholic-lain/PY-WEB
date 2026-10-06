import re

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone

# Regex officielle du matricule fiscal tunisien (fournie dans l'énoncé)
MATRICULE_REGEX = (
    r"^\d{7}[/ -]?[A-Za-z][/ -]?[ABDNPEabdnpe][/ -]?[MPCNEmpcne][/ -]?\d{3}$"
)


def validate_gmail(value):
    """Seuls les emails du domaine gmail.com sont acceptés."""
    if not value.lower().endswith("@gmail.com"):
        raise ValidationError(
            "Seules les adresses du domaine gmail.com sont acceptées.",
            code="email_domain",
        )


def generate_user_id():
    """Format AAuserNN : AA = 2 derniers chiffres de l'année, NN = compteur
    00-99 remis à zéro chaque année (ex. 26user00, 26user01, ...).

    Appelée depuis save() et PAS via default= : elle interroge la base, et
    Django instancie le modèle pendant ses vérifications de démarrage, avant
    même que la table existe.
    """
    prefix = f"{timezone.now().strftime('%y')}user"
    dernier = (
        Utilisateur.objects.filter(user_id__startswith=prefix)
        .order_by("-user_id")
        .values_list("user_id", flat=True)
        .first()
    )
    n = int(dernier[-2:]) + 1 if dernier else 0
    if n > 99:
        raise ValidationError(
            "Limite atteinte : 100 inscriptions maximum par an (compteur 00-99)."
        )
    return f"{prefix}{n:02d}"


class UtilisateurManager(UserManager):
    """UserManager par défaut + rôle 'admin' pour les superusers."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Utilisateur.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        CHARGEUR = "chargeur", "Chargeur"
        TRANSPORTEUR = "transporteur", "Transporteur"
        ADMIN = "admin", "Administrateur"

    # PK personnalisée, générée dans save() (voir generate_user_id)
    user_id = models.CharField(
        max_length=8, primary_key=True, editable=False, blank=True
    )
    email = models.EmailField(unique=True, validators=[validate_gmail])
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CHARGEUR)
    telephone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UtilisateurManager()

    def save(self, *args, **kwargs):
        validate_gmail(self.email)  # aussi garanti hors formulaires
        if not self.user_id:
            self.user_id = generate_user_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class Entreprise(models.Model):
    class Type(models.TextChoices):
        CHARGEUR = "chargeur", "Chargeur"
        TRANSPORTEUR = "transporteur", "Transporteur"

    raison_sociale = models.CharField(max_length=150)
    # max_length=17 : 13 caractères + jusqu'à 4 séparateurs
    matricule_fiscal = models.CharField(
        max_length=17,
        unique=True,
        validators=[
            RegexValidator(
                MATRICULE_REGEX,
                message="Format attendu : 1234567AAM000 (séparateurs / - ou espace acceptés).",
            )
        ],
    )
    type_entreprise = models.CharField(max_length=20, choices=Type.choices)
    adresse = models.TextField(
        validators=[MinLengthValidator(20, "L'adresse doit contenir au moins 20 caractères.")]
    )
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="entreprise",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Normalisation : sans séparateurs et en majuscules, pour que
        # 1234567/A/A/M/000 et 1234567aam000 soient détectés comme doublons.
        if self.matricule_fiscal:
            self.matricule_fiscal = re.sub(r"[/ -]", "", self.matricule_fiscal).upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.raison_sociale} ({self.type_entreprise})"
