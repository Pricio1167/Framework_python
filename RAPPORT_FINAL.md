# Rapport de livraison PHARMAGEST conforme au cahier des charges

Version locale vérifiée le 18 novembre 2026. Le projet a été comparé au fichier
Cahier des charges projet pharmacie.docx, lu intégralement avec ses huit tableaux
et ses six images indicatives. Les écarts fonctionnels identifiés ont été
implémentés. Ce rapport distingue les essais locaux réussis des conditions
externes de mise en exploitation.

## 1. Fonctionnalités réellement livrées

Les fonctionnalités de prompt.md sont conservées : rôles et permissions,
interface française Bootstrap, dashboard réel, médicaments, catégories,
fournisseurs, clients, achats, réceptions, stocks, ventes, paiements, retours,
remboursements, PDF, sauvegardes et préparation du déploiement.

Compléments issus du cahier des charges Word :

- Photos de médicaments importées, vérifiées selon leur contenu réel, leur
  extension, leur taille de 5 Mo maximum et leurs dimensions de 16 millions de
  pixels maximum ; affichage dans les listes et fiches.
- Recherche par nom ou code-barres, filtre catégorie, détail, archivage et
  suppression uniquement lorsque l’historique n’en dépend pas.
- Changement du mot de passe, récupération avec jeton Django expirant en une
  heure et invalidé après usage, gestion des erreurs d’envoi et audit sans
  mot de passe en clair.
- Cinquième groupe Responsable de gestion en consultation ; groupes existants
  et permissions personnalisées conservés.
- Fiches clients et fournisseurs avec historiques autorisés et paginés, montants
  des commandes et réceptions et désactivation sans effacement de l’historique.
- Totaux des achats/réceptions, confirmation transactionnelle, annulation motivée
  avant réception validée et instantanés des documents d’approvisionnement.
- Bons de commande, bons de réception, rapport des achats et liste PDF des lots
  proches de la péremption, en plus des six documents déjà disponibles.
- Caisse avec recherche/scanner clavier, sélection d’un lot ou FEFO automatique,
  réservation des lots explicitement demandés et identification du lot retourné.
- Contrôle professionnel enregistré avant validation lorsqu’un médicament est
  configuré comme nécessitant une prescription. Aucun diagnostic ni aucune
  autorisation réglementaire automatique n’est déduit du catalogue.
- Paiements CARTE/MOBILE en attente jusqu’à vérification autorisée du statut
  réel, référence unique, auteur/date de vérification et refus traçable.
  Les montants en attente ne sont pas encaissés, remboursables ou imprimables
  comme reçus. Un règlement réel vérifié après un retour reste rapprochable,
  puis remboursable dans la limite du trop-perçu.
- Dashboard avec médicaments actifs et périodes de ventes/achats ; distinction
  du chiffre d’affaires brut/net, des encaissements et des dépenses d’achat.
- Guide d’utilisation et dossier MCD, MLD, classes, séquence et cas d’utilisation,
  avec schéma de 21 modèles exporté sans données métier.
- Commande auditer_integrite en lecture seule, sans réparation implicite.

La grille détaillée des modules A à K, règles RG01 à RG12, critères de recette
et limites est dans verification/CONFORMITE_CAHIER_DES_CHARGES.md.

## 2. Fichiers créés et modifiés

Ajouts principaux de cette intervention :

- medicaments/validators.py et sa migration 0002.
- achats/operations.py, achats/documents.py et la migration 0003.
- ventes/finance.py et la migration 0008 ; extension des modèles, formulaires,
  paiements, retours, opérations, validation FEFO, vues et documents existants.
- utilisateurs/auth_views.py et management/commands/auditer_integrite.py ;
  actualisation des rôles et audit des comptes.
- dashboard/fiches.py, dashboard/test_cahier_charges.py et les nouveaux templates
  de fiches, pagination historique et période du dashboard.
- Templates de changement/réinitialisation du mot de passe et vérification des
  paiements, champs d’import de photos et filtres de catégorie.
- Scripts exporter_conception.py, extension des données fictives de revue et du
  contrôle WSGI aux nouvelles pages.
- docs/GUIDE_UTILISATION.md, docs/conception/, la grille de conformité et le
  résultat d’audit verification/audit_integrite.json.

Mises à jour transversales : config/settings.py, config/urls.py, dashboard/gestion.py,
catalogue.py, views.py, rapports/services.py, views.py, urls.py, pdf.py, les templates,
le CSS, achats/admin.py, compose.yaml, .env.example, .dockerignore et README.md.
Les fichiers des interventions précédentes restent présents. Le document Word
original n’a pas été modifié par l’intervention. Aucun commit Git n’a été créé.

## 3. Migrations et données

Trois nouvelles migrations additives ont été générées puis appliquées :

- achats/0003_commandeachat_instantane_document_and_more.
- medicaments/0002_medicament_prescription_requise_and_more.
- ventes/0008_alter_paiement_options_ligneretour_lot_origine_and_more.

Les migrations antérieures sont inchangées et restent appliquées. Une sauvegarde
SQLite vérifiée a précédé ces modifications :
backups/pharmagest-20261117-195433-129972.sqlite3.

La base de travail reste SQLite. Aucune opération métier historique n’a été
réécrite ou supprimée. Les paiements historiques conservent leur état, sans preuve
inventée. Les comptes réels et leurs mots de passe n’ont pas été changés.
Les migrations et restaurations PostgreSQL ont utilisé des clusters distincts,
protégés par mot de passe sur des ports locaux temporaires, arrêtés à la fin.

## 4. Vérifications réellement exécutées

| Contrôle | Résultat |
| --- | --- |
| Suite SQLite | 117 tests découverts : 110 réussis, 7 ignorés car spécifiques PostgreSQL ; aucun échec, 91,939 s |
| Suite PostgreSQL 18 | 117 tests réussis, aucun ignoré, 101,532 s |
| Contrôles ciblés complémentaires | 5 tests de paiements et 12 tests de rapports réussis |
| Concurrence | Ventes, double validation, paiements, rejeu idempotent, retours, réceptions sur le même lot et référence électronique unique |
| Transfert d’une copie SQLite | 32 objets exportés en UTF-8, importés et comparés intégralement dans PostgreSQL |
| Restauration SQLite | integrity_check et comparaison intégrale iterdump réussis |
| Restauration PostgreSQL | pg_dump custom, pg_restore vers une seconde base et comparaison réussis |
| Audit des données réelles | Lecture seule, zéro erreur et zéro avertissement |
| WSGI de production | 18 pages authentifiées vérifiées via HTTP local, cookies Secure, HSTS et nosniff |
| PDF | 10 documents fictifs rendus en PNG et inspectés |
| Django check | Aucun problème |
| Migrations check/dry-run | Aucun changement détecté |
| Django check --deploy | Aucun problème avec DEBUG=false |
| Fichiers statiques | 138 fichiers présents dans la collecte |
| Docker Compose | Configuration validée, aucun service externe démarré |

Les réponses 400, 403, 404 et 405 des tests négatifs sont attendues. Les 43 tests
historiques sont conservés ; aucun test n’a été supprimé. Un ancien test de retrait
de ligne a reçu un lot vendable dans sa préparation, car les sélecteurs de caisse
excluent désormais les médicaments sans lot délivrable.

Le bilan machine est dans verification/resultats.json. Les journaux PostgreSQL
sont dans tmp/verification-pg-kqr_eu04/. Les exports contiennent des données de
la copie et restent exclus de Git et de l’image Docker.

## 5. Démarrage et utilisation

Depuis C:\projet_django\Framework_python :

```powershell
.venv/Scripts/python.exe manage.py runserver
```

Ouvrir http://127.0.0.1:8000/connexion/.
Les serveurs de contrôle temporaires ont été arrêtés.

Le README fournit l’installation et la configuration. Le guide d’utilisation
est dans docs/GUIDE_UTILISATION.md. Les clients et fournisseurs sont des fiches
commerciales ; le cahier des charges ne prévoit pas de portail public pour eux.

## 6. Comptes et rôles

Utiliser un compte existant autorisé, ou créer le premier superutilisateur :

```powershell
.venv/Scripts/python.exe manage.py createsuperuser
```

Aucun mot de passe par défaut n’est fourni. Les cinq groupes sont Administrateur,
Pharmacien, Gestionnaire de stock, Caissier et Responsable de gestion. Les droits
peuvent se cumuler uniquement par attribution autorisée. Le statut is_staff est
nécessaire pour l’administration Django, pas pour les écrans métier.
Le compte de revue et les données fictives existent exclusivement dans tmp/revue/.

## 7. Points non vérifiés sur infrastructure réelle

Le navigateur intégré reste indisponible. Les parcours sont couverts par Django
et HTTP WSGI, mais la revue visuelle réelle sur ordinateur, tablette et téléphone
n’est pas déclarée réussie. Les PDF sont inspectés séparément par leurs rendus.

Le SMTP réel et le statut d’un prestataire de paiement externe nécessitent des
informations et accès réels. La récupération est testée avec une boîte mémoire ;
en développement, les e-mails sont écrits dans tmp/emails/ sans envoi réseau.
La vérification de paiement est manuelle, autorisée et tracée ; aucun connecteur
bancaire automatique n’est revendiqué.

Les anciens documents sans instantané ne sont pas reconstitués fictivement.
Les PDF ne sont pas annoncés comme des archives fiscales certifiées ou signées.

## 8. Paramètres et validations externes restant à fournir

- Renseigner les informations réelles de la pharmacie et ses mentions validées.
- Faire valider les règles de prescription, délivrance, retours, remboursements,
  données personnelles et conservation des documents pour le territoire exploité.
- Activer une politique de remise en stock uniquement après validation responsable.
- Fournir la configuration SMTP, l’expéditeur réel, le domaine et l’hébergement.
- Organiser les sauvegardes protégées hors serveur, y compris media/, et la
  surveillance de l’infrastructure réellement déployée.

Ces informations ne sont pas inventées. Elles correspondent aux conditions
d’exploitation réelle précisées par le cahier des charges.

## 9. Préparation au déploiement

Le développement local est livré avec les contrôles techniques décrits. Docker
Compose prépare PostgreSQL, Waitress, les statiques/médias et Caddy pour un domaine
réel avec HTTPS. Le serveur WSGI et les procédures de migration/restauration sont
vérifiés dans les limites indiquées. Aucun hébergement externe ni certificat pour
un vrai domaine n’a été provisionné. Les instructions sont dans deploy/README.md.
