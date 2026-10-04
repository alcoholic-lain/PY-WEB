# AI_LOG.md — TransConnect (Part 1)

## Entrée 2026-10-04 (1) — Mise en place du projet
- Outil IA utilisé : Claude
- Prompt : « Donne-moi les commandes avec uv pour terminer et pousser ce projet sur GitHub » (avec le PDF du workshop joint), puis aide pour nettoyer un `uv init` raté sous PowerShell.
- Sortie obtenue (résumé) : Séquence `uv init --bare`, `uv add django`, `django-admin startproject config .`, `startapp` pour les 4 applications, configuration de `settings.py` (`INSTALLED_APPS`, `AUTH_USER_MODEL`, nom de la base), puis commandes Git.
- Écarts identifiés vs cahier des charges : Les commandes proposées étaient en syntaxe bash (`printf`, heredoc `<< 'EOF'`) alors que l'environnement est PowerShell sous Windows ; `uv init` avait aussi créé une structure `src/` incompatible avec Django.
- Correction apportée et justification : Suppression de la structure `src/` et réinitialisation avec `uv init --bare`. Remplacement de `printf` et du heredoc par des here-strings PowerShell avec `Set-Content -Encoding utf8` (l'opérateur `>` écrit en UTF-16 sous Windows PowerShell 5.1 et Git ne lit pas correctement le fichier).

## Entrée 2026-10-04 (2) — Génération des 5 modèles
- Outil IA utilisé : Claude
- Prompt : « ok step 4 ? » (écriture des modèles à partir du diagramme de classe et du tableau de contraintes du PDF).
- Sortie obtenue (résumé) : Un `models.py` par application : `Utilisateur` (hérite de `AbstractUser`, PK `user_id` CharField(8), manager personnalisé) et `Entreprise` dans EntreprisesApp ; `Vehicule` ; `Expedition` (référence auto-générée `EXP-XXXXXXXX`) ; `Offre`.
- Écarts identifiés vs cahier des charges : Aucun écart de structure par rapport au diagramme (relations 1—1, 1—*, FK conformes). Choix à justifier (AA3) : `DecimalField` pour prix et poids, `TextChoices` pour les statuts, `type_vehicule` en CharField avec `choices`, `limit_choices_to` pour restreindre les types d'entreprise (contrôle au niveau formulaire/admin uniquement, pas en base).
- Correction apportée et justification : Aucune à ce stade, voir l'entrée suivante pour le bug détecté à l'exécution.

## Entrée 2026-10-04 (3) — Bug de `generate_user_id`
- Outil IA utilisé : Claude
- Prompt : collage de la trace d'erreur de `uv run python manage.py showmigrations`.
- Sortie obtenue (résumé) : `OperationalError: no such table: EntreprisesApp_utilisateur`.
- Écarts identifiés vs cahier des charges : La fonction `generate_user_id`, générée par l'IA, interrogeait la base (`Utilisateur.objects.filter(...).exists()`) pour garantir l'unicité. Or `default=` est appelé lorsque Django instancie le modèle, y compris pendant les vérifications de démarrage (`check_user_model`), avant même que la table n'existe : impossible de lancer `makemigrations` ou `migrate`.
- Correction apportée et justification : Suppression de la requête ; la fonction génère simplement 8 caractères aléatoires (A-Z, 0-9) avec `secrets.choice`. L'unicité reste garantie par la contrainte de clé primaire (36^8 valeurs possibles, et une collision lèverait une `IntegrityError` au lieu d'écraser une ligne).

## Entrée 2026-10-04 (4) — Chasse aux bugs de l'entité Offre (section IV)
- Outil IA utilisé : Claude
- Prompt : analyse du premier jet de `Offre` fourni dans l'énoncé, comparé au tableau de contraintes.
- Sortie obtenue (résumé) : Version corrigée de `Offre` intégrée dans `OffresApp/models.py`.
- Écarts identifiés vs cahier des charges :
  1. `prix` était un `CharField(max_length=10)` : impossible de trier ou calculer. Le cahier des charges demande un `DecimalField`.
  2. `delai_jours` était un `IntegerField` : accepte des valeurs négatives. Le cahier des charges demande un `PositiveIntegerField`.
  3. `date_proposition` utilisait `auto_now=True` : la date était écrasée à chaque sauvegarde. Le cahier des charges demande `auto_now_add=True`.
  4. `vehicule` avait `null=True` et `on_delete=CASCADE` : une offre doit toujours être liée à un véhicule, et supprimer un véhicule ne doit pas supprimer silencieusement ses offres.
  - Défauts secondaires : `STATUT_CHOICES` non défini, `created_at` et `updated_at` absents, `save()` surchargé sans effet.
- Correction apportée et justification :
  1. `DecimalField(max_digits=10, decimal_places=2)` : précision exacte pour les montants.
  2. `PositiveIntegerField` : un délai ne peut pas être négatif.
  3. `DateField(auto_now_add=True)` : la date de proposition est fixée à la création uniquement.
  4. `null=True` retiré et `on_delete=PROTECT` : le véhicule est obligatoire et ne peut pas être supprimé tant qu'il a des offres.
  - Ajout d'une classe `Statut(TextChoices)`, de `created_at` / `updated_at`, d'une méthode `clean()` vérifiant que le véhicule appartient bien au transporteur, et suppression du `save()` inutile.




# test : 
```
PS C:\Users\lain\Desktop\ESPRIT-AI\PY-DJ\REPO> uv run manage.py check
System check identified no issues (0 silenced).
PS C:\Users\lain\Desktop\ESPRIT-AI\PY-DJ\REPO> 
```