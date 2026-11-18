# PROMPT CODEX — FINALISATION COMPLÈTE DU PROJET PHARMAGEST

## 1. TON RÔLE

Tu es un développeur senior Full Stack spécialisé en Python, Django, PostgreSQL, Bootstrap 5, sécurité applicative, architecture logicielle et systèmes de gestion de pharmacie.

Ta mission est de **reprendre, analyser, compléter, corriger, sécuriser et finaliser entièrement mon projet PHARMAGEST**, sans détruire ni remplacer inutilement les fonctionnalités existantes.

Tu dois travailler directement dans mon dépôt local et effectuer les modifications nécessaires dans les fichiers du projet.

**Ne te limite pas à proposer du code ou à expliquer ce qu'il faudrait faire : implémente réellement les fonctionnalités, exécute les commandes, corrige les erreurs et teste le résultat.**

## 2. CONTEXTE DU PROJET

**Nom :** PHARMAGEST  
**Type :** Application web de gestion de pharmacie  
**Architecture :** Django modulaire, avec applications métier séparées  
**Langage :** Python 3.14  
**Framework :** Django 5.2.19  
**Base actuelle :** SQLite  
**Base cible :** PostgreSQL  
**Frontend souhaité :** Django Templates, HTML5, CSS3, JavaScript et Bootstrap 5  
**Langue de l'interface :** français  
**Devise :** Ariary malgache (Ar)  
**Fuseau horaire :** Indian/Antananarivo

**Dossier du projet :**

`C:\projet_django\Framework_python`

L'environnement virtuel Python se trouve dans `.venv`.

Le projet possède actuellement les applications suivantes :

```text
Framework_python/
├── config/
├── utilisateurs/
├── medicaments/
├── fournisseurs/
├── clients/
├── achats/
├── stock/
├── ventes/
├── rapports/
├── dashboard/
├── templates/
├── static/
├── media/
├── manage.py
└── db.sqlite3
```

Ce schéma représente les dossiers connus. Tu dois inspecter le dépôt pour identifier leur contenu exact et les éventuels autres fichiers.

## 3. ÉTAT ACTUEL DU PROJET

Les fonctionnalités suivantes ont déjà été développées au moins partiellement :

- Gestion des médicaments et catégories.
- Gestion des fournisseurs et clients.
- Gestion des achats et réceptions.
- Gestion des lots de médicaments.
- Gestion des mouvements de stock.
- Gestion des ventes et lignes de vente.
- Gestion des paiements.
- Gestion des retours.
- Traçabilité des lots utilisés lors des ventes.
- Gestion des dates de péremption.
- Alertes de stock faible.
- Rapports de ventes et de stocks.
- Génération des rapports PDF avec ReportLab.
- Protection initiale des rapports par permissions Django.

Les services métier existants incluent notamment :

- Validation transactionnelle des ventes.
- Déstockage des médicaments selon la méthode FEFO.
- Enregistrement des paiements.
- Validation des retours.
- Calcul du stock disponible.
- Identification des lots périmés.
- Identification des lots proches de la péremption.
- Calcul des indicateurs de ventes.

**Dernier état des tests confirmé :**

```text
Found 43 test(s).
System check identified no issues (0 silenced).
Ran 43 tests in 51.529s

OK
```

Ces 43 tests constituent une référence de non-régression, et non la preuve que toutes les fonctionnalités sont terminées.

Le projet doit être repris à partir de **l'étape 29 : gestion des rôles et permissions**, puis poursuivi jusqu'à sa finalisation.

## 4. RÈGLES OBLIGATOIRES

1. Commence par examiner l'ensemble du projet existant.
2. Lis les modèles, services, vues, routes, migrations, templates et tests.
3. Ne suppose jamais qu'un champ, une méthode ou une relation existe sans l'avoir vérifié.
4. Conserve l'architecture actuelle avec les applications Django séparées.
5. Ne recrée pas le projet Django.
6. Ne supprime pas les fonctionnalités existantes.
7. Ne modifie pas les migrations historiques déjà appliquées.
8. Crée de nouvelles migrations uniquement si nécessaire.
9. Préserve les données SQLite existantes.
10. N'effectue aucune suppression de données, réinitialisation de base ou migration destructive sans mon autorisation.
11. Utilise des transactions atomiques pour les opérations sensibles.
12. Ne duplique pas les règles métier entre vues, modèles et services.
13. Corrige les erreurs découvertes pendant le développement.
14. Ajoute des tests automatisés pour chaque nouvelle fonctionnalité importante.
15. Vérifie régulièrement que les 43 tests existants passent toujours.
16. Utilise des noms cohérents avec le projet existant.
17. Respecte les conventions Django et PEP 8.
18. Utilise une interface entièrement en français.
19. Ne stocke aucun secret dans le code source.
20. Ne considère pas une fonctionnalité comme terminée avant de l'avoir testée.

Privilégie une architecture propre, maintenable et sécurisée.

## 5. ÉTAPE 29 — GESTION DES RÔLES ET PERMISSIONS

Implémente un système complet de gestion des accès à partir des groupes et permissions Django.

Les rôles sont :

**Administrateur**
- Gestion complète de l'application.
- Gestion des utilisateurs et permissions.
- Consultation des rapports.
- Gestion des achats, ventes, stocks et paramètres.

**Pharmacien**
- Consultation des médicaments et stocks.
- Gestion des ventes.
- Gestion des clients.
- Gestion des retours autorisés.
- Consultation des informations nécessaires à son activité.

**Gestionnaire de stock**
- Gestion des médicaments et fournisseurs.
- Gestion des achats et réceptions.
- Gestion des lots et stocks.
- Consultation des alertes.
- Corrections de stock autorisées.

**Caissier**
- Consultation des médicaments disponibles.
- Gestion des clients.
- Création et consultation des ventes autorisées.
- Enregistrement des paiements.
- Impression des reçus.

Travail demandé :

- Créer une commande Django `configurer_roles`.
- Configurer les groupes et permissions.
- Rendre la commande idempotente.
- Éviter d'écraser involontairement des permissions personnalisées.
- Implémenter les contrôles d'accès sur les vues et services métier.
- Vérifier les permissions des utilisateurs connectés.
- Protéger les opérations de validation, annulation, remboursement et correction de stock.
- Empêcher les accès directs non autorisés aux URL.
- Adapter l'affichage des menus selon les permissions.
- Ajouter les tests correspondants.

Ne te contente pas de masquer les boutons : les autorisations doivent être vérifiées côté serveur.

## 6. ÉTAPE 30 — FINALISATION DES VENTES ET PAIEMENTS

Complète le module `ventes` avec :

- Création de vente.
- Ajout et suppression de lignes avant validation.
- Calcul automatique des totaux.
- Validation des quantités.
- Vérification du stock disponible.
- Validation transactionnelle.
- Déstockage FEFO.
- Enregistrement des paiements.
- Paiements partiels lorsque les règles métier les autorisent.
- Calcul du reste à payer.
- Historique des paiements.
- Annulation contrôlée des opérations.
- Prévention des doubles validations.
- Traçabilité des utilisateurs.

Les ventes validées doivent conserver un historique fiable. Toute correction ultérieure doit être traçable.

Ne modifie pas la logique FEFO existante si elle fonctionne correctement ; réutilise-la.

## 7. ÉTAPE 31 — RETOURS ET REMBOURSEMENTS

Complète le traitement des retours clients.

Fonctionnalités :

- Création d'une demande de retour.
- Sélection des lignes concernées.
- Vérification des quantités déjà retournées.
- Validation ou refus du retour.
- Motif obligatoire.
- Historique des retours.
- Gestion des remboursements partiels ou complets.
- Prévention des remboursements multiples.
- Contrôle des permissions.

**Règle essentielle :** un médicament retourné ne doit pas automatiquement redevenir vendable.

Prévois une mise en quarantaine et une décision explicite de remise en stock, conformément aux règles applicables.

Les remboursements doivent être cohérents avec les montants réellement encaissés.

## 8. ÉTAPE 32 — FACTURES ET REÇUS PDF

Utilise ReportLab, déjà présent dans le projet.

Créer :

- Facture de vente.
- Reçu de paiement.
- Justificatif de retour.
- Justificatif de remboursement.
- Historique des documents générés si nécessaire.

Chaque facture doit afficher les informations disponibles et pertinentes :

- Identification de la pharmacie.
- Numéro unique de facture.
- Date.
- Client, lorsqu'il est renseigné.
- Médicaments vendus.
- Quantités.
- Prix unitaires.
- Sous-totaux.
- Total.
- Montant payé.
- Reste à payer.
- Informations réglementaires configurables, selon les obligations applicables.

Ne fabrique pas d'informations légales, fiscales ou commerciales manquantes. Rends-les configurables.

## 9. ÉTAPE 33 — GESTION AVANCÉE DES STOCKS

Finalise :

- Entrées de stock.
- Sorties de stock.
- Corrections autorisées.
- Historique des mouvements.
- Traçabilité des lots.
- Gestion des lots bloqués.
- Lots périmés.
- Lots proches de la péremption.
- Stock disponible.
- Seuils d'alerte.
- Inventaires.
- Écarts d'inventaire.
- Justifications des corrections.

Interdire la vente des lots périmés, bloqués ou dont la quantité disponible est insuffisante.

Préserver l'intégrité des quantités et des mouvements.

## 10. ÉTAPE 34 — DASHBOARD DYNAMIQUE

Développe un tableau de bord professionnel affichant les données réelles de la base.

Indicateurs souhaités :

- Chiffre d'affaires du jour.
- Chiffre d'affaires du mois.
- Nombre de ventes.
- Montant encaissé.
- Reste à payer.
- Médicaments en stock faible.
- Lots proches de la péremption.
- Lots périmés.
- Achats récents.
- Ventes récentes.
- Produits les plus vendus.

Ajouter des graphiques avec Chart.js si pertinent.

Les indicateurs doivent tenir compte des retours et remboursements selon des définitions métier explicites.

Les informations affichées doivent respecter les permissions de l'utilisateur.

## 11. ÉTAPES 35 À 38 — INTERFACE WEB BOOTSTRAP 5

Créer une interface moderne, professionnelle, responsive et accessible.

Technologies :

- Django Templates.
- Bootstrap 5.
- HTML5.
- CSS3.
- JavaScript.
- Chart.js lorsque nécessaire.
- Icônes Bootstrap.

Respecter les principes UI/UX et IHM :

- Hiérarchie visuelle claire.
- Navigation intuitive.
- Cohérence des composants.
- Contrastes lisibles.
- États de chargement et d'erreur.
- Messages de confirmation.
- Validation des formulaires.
- Navigation au clavier.
- Adaptation mobile, tablette et ordinateur.

Appliquer une palette cohérente inspirée de la règle 60/30/10 :

- 60 % : fond neutre clair.
- 30 % : bleu professionnel.
- 10 % : couleur d'accent utilisée pour les actions importantes.

Créer un `base.html` réutilisable, une barre latérale, une barre supérieure et des composants communs.

**Pages à développer :**

1. Connexion et déconnexion.
2. Dashboard.
3. Liste des médicaments.
4. Ajout et modification de médicament.
5. Catégories.
6. Fournisseurs.
7. Clients.
8. Achats.
9. Réceptions.
10. Liste des stocks.
11. Détails des lots.
12. Mouvements de stock.
13. Alertes de péremption.
14. Ventes.
15. Création de vente.
16. Détails d'une vente.
17. Paiements.
18. Retours.
19. Remboursements.
20. Rapports.
21. Téléchargement des PDF.
22. Utilisateurs et rôles.
23. Paramètres de la pharmacie.

Les pages doivent être reliées aux vraies vues et services Django.

Ne crée pas une simple maquette statique.

Ajouter si pertinent :

- Recherche.
- Filtres.
- Pagination.
- Tri.
- Formulaires.
- Tableaux.
- Badges d'état.
- Messages de succès et d'erreur.
- Confirmations pour les opérations sensibles.

Les formulaires doivent être sécurisés avec CSRF et validation serveur.

## 12. ÉTAPE 39 — TESTS COMPLETS

Conserver les 43 tests existants.

Ajouter les tests nécessaires pour :

- Rôles et permissions.
- Authentification.
- CRUD.
- Achats.
- Réceptions.
- Ventes.
- Paiements.
- Retours.
- Remboursements.
- Factures.
- Stocks.
- Péremptions.
- Rapports.
- PDF.
- Dashboard.
- Accès non autorisés.
- Opérations concurrentes lorsque cela est pertinent.

Tester les scénarios d'échec, les quantités insuffisantes, les validations répétées et les incohérences financières.

Exécuter les tests après chaque ensemble de modifications.

Ne prétends pas qu'un test est réussi si tu ne l'as pas réellement exécuté.

## 13. ÉTAPE 40 — POSTGRESQL ET CONFIGURATION

Préparer le projet pour PostgreSQL.

- Utiliser des variables d'environnement.
- Préparer une configuration de développement et de production.
- Conserver SQLite tant que PostgreSQL n'est pas correctement configuré.
- Préparer une procédure de migration des données.
- Ne pas supprimer la base SQLite.
- Ne pas exposer les identifiants de connexion.
- Vérifier la compatibilité des migrations.
- Préparer les fichiers nécessaires au déploiement.

Si PostgreSQL n'est pas accessible, documenter précisément ce qui reste à configurer et poursuivre les tâches indépendantes.

## 14. ÉTAPE 41 — SÉCURITÉ, SAUVEGARDES ET DÉPLOIEMENT

Vérifier notamment :

- `DEBUG=False` en production.
- `ALLOWED_HOSTS`.
- `SECRET_KEY` dans les variables d'environnement.
- HTTPS.
- Cookies sécurisés.
- Protection CSRF.
- Permissions.
- Validation des données.
- Journalisation.
- Gestion des erreurs.
- Fichiers statiques et médias.
- Sauvegardes.
- Restauration.
- Dépendances.
- Configuration WSGI ou ASGI.

Créer un fichier `.env.example` sans secrets réels.

Créer un `README.md` complet avec les instructions d'installation, de démarrage, de tests et de déploiement.

Préparer le déploiement sans prétendre avoir déployé l'application si aucun serveur n'est disponible.

## 15. MÉTHODE D'EXÉCUTION

Travaille de manière autonome, dans l'ordre des dépendances techniques.

**Phase A — Audit**
- Explorer les fichiers existants.
- Comprendre les modèles et relations.
- Identifier les fonctionnalités manquantes.
- Exécuter les tests de référence.
- Définir un plan concret.

**Phase B — Backend**
- Implémenter les rôles et permissions.
- Finaliser les ventes, retours et remboursements.
- Finaliser les stocks.
- Ajouter les documents PDF.
- Compléter les rapports et le dashboard.

**Phase C — Frontend**
- Construire les templates communs.
- Implémenter toutes les pages.
- Relier les pages aux services métier.
- Tester les parcours utilisateur.

**Phase D — Qualité**
- Ajouter les tests.
- Corriger les régressions.
- Vérifier les permissions.
- Vérifier les données et calculs.
- Tester les parcours complets.

**Phase E — Livraison**
- Préparer PostgreSQL.
- Préparer la configuration de production.
- Documenter le projet.
- Effectuer les vérifications finales.

Tu dois poursuivre les tâches tant qu'il reste du travail réalisable, sans demander une validation après chaque fichier.

Demande mon intervention uniquement lorsqu'une décision métier importante, une opération destructive, un secret ou un accès externe est nécessaire.

Ne considère pas une phase terminée tant que ses critères de validation ne sont pas satisfaits.

## 16. CONTRÔLE QUALITÉ

À chaque phase :

1. Exécute `python manage.py check`.
2. Exécute les tests pertinents.
3. Vérifie les migrations.
4. Corrige les erreurs détectées.
5. Vérifie que les fonctionnalités existantes continuent de fonctionner.
6. Résume brièvement les fichiers modifiés et les résultats.

À la fin, exécute au minimum :

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Effectue aussi `python manage.py check --deploy` avec une configuration de production appropriée et analyse les avertissements.

## 17. LIVRABLES ATTENDUS

À la fin, je veux :

- Une application Django PHARMAGEST complète.
- Un backend métier fonctionnel.
- Une interface Bootstrap 5 responsive.
- Un système d'authentification.
- Des rôles et permissions.
- Une gestion des médicaments.
- Une gestion des fournisseurs et clients.
- Une gestion des achats et réceptions.
- Une gestion des stocks et lots.
- Une gestion des ventes.
- Une gestion des paiements.
- Une gestion des retours et remboursements.
- Des factures et reçus PDF.
- Des rapports PDF.
- Un dashboard dynamique.
- Des tests automatisés.
- Une configuration PostgreSQL préparée.
- Une documentation d'installation et d'utilisation.

## 18. RAPPORT FINAL OBLIGATOIRE

À la fin du développement, présente :

1. Les fonctionnalités réellement terminées.
2. Les fichiers créés et modifiés.
3. Les migrations effectuées.
4. Le nombre total de tests exécutés et réussis.
5. Les commandes pour démarrer PHARMAGEST.
6. Les identifiants ou rôles nécessaires à la première connexion, sans inventer ni afficher de mots de passe.
7. Les éventuels problèmes non résolus.
8. Les opérations manuelles restant à effectuer.
9. L'état de préparation au déploiement.

Distingue clairement ce qui est implémenté, testé, préparé ou encore incomplet.

**COMMENCE MAINTENANT PAR AUDITER LE PROJET EXISTANT DANS `C:\projet_django\Framework_python`, PUIS EXÉCUTE LE PLAN JUSQU'À LA FINALISATION DE PHARMAGEST. CONSERVE LA STRUCTURE EXISTANTE, PROTÈGE LES DONNÉES ET NE T'ARRÊTE PAS APRÈS LA PREMIÈRE ÉTAPE.**