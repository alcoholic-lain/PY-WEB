
## Entrée 2026-10-06 (5) — Part 2 : contraintes et règles métier
- Outil IA utilisé : Claude
- Prompt : « continue plz » avec le PDF de la Part 2 joint (contraintes de champs, section III ; règles métier, section IV).
- Sortie obtenue (résumé) : Nouvelle version des 4 `models.py` : formats `AAuserNN` et `EXP-AA-NNNNN` générés dans `save()`, validateur gmail.com, regex du matricule fiscal, adresse ≥ 20 caractères, validateurs > 0 / ≥ 1, `CheckConstraint` en base, règles métier 1 à 7 dans `clean()` / `save()`, cascade à l'acceptation, et `OffresApp/tests.py` (19 tests).
- Écarts identifiés vs cahier des charges :
  - La Part 1 générait `user_id` via `default=` ; le nouveau format exige un compteur annuel (donc une requête). Gardé en `default=`, cela recréerait le bug de l'entrée (3) : la génération est déplacée dans `save()`.
  - La regex du matricule autorise la lettre `E` pour le code TVA, alors que le texte de l'énoncé ne liste que A, B, D, N, P. J'ai conservé la regex fournie telle quelle.
  - La règle 7 donne des capacités « indicatives » : interprétées comme des plafonds de poids par gabarit (camionnette 1500 kg, fourgon 3500, camion porteur 19000, semi-remorque 26000), sans plancher.
- Correction apportée et justification :
  - Validateurs de champs (`MinValueValidator`, `RegexValidator`, `MinLengthValidator`) + `CheckConstraint` en base pour prix, délai, poids et capacité : double protection (formulaires et base).
  - Les validateurs ne tournent que dans `full_clean()` : `save()` appelle donc `full_clean()` pour que les règles s'appliquent aussi hors formulaires (limite : `bulk_create` et `update()` les contournent).
  - Règles 3 et 6 appliquées seulement à la création (`_state.adding`), sinon l'acceptation d'une offre (expédition déjà « attribuée ») serait bloquée.
  - Règle 4 : contrôle dans `clean()` + `UniqueConstraint` partielle (statut = proposee) comme filet de sécurité en base.
  - Règle 5 : cascade dans `save()` sous `transaction.atomic()` ; acceptation refusée si l'expédition n'est plus « publiée », ce qui garantit une seule offre acceptée par expédition.
  - Normalisation du matricule (sans séparateurs, majuscules) pour que deux formats du même matricule soient détectés comme doublons.
  - Vérification : 19 tests passent (`uv run manage.py test OffresApp`).
