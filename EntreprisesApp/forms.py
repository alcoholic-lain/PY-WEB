from django import forms
from django.db.models import Q

from .models import Entreprise, Utilisateur


class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = (
            "raison_sociale",
            "matricule_fiscal",
            "type_entreprise",
            "adresse",
            "utilisateur",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = Utilisateur.objects.filter(entreprise__isnull=True)
        if self.instance.pk:
            users = Utilisateur.objects.filter(
                Q(entreprise__isnull=True) | Q(pk=self.instance.utilisateur_id)
            )
        self.fields["utilisateur"].queryset = users.order_by("username")
