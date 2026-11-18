# PHARMAGEST

Application Django modulaire de gestion de pharmacie, interface française,
montants en Ariary et fuseau `Indian/Antananarivo`.

## Installation et démarrage sous Windows

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/configurer_local.py
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py configurer_roles
.venv/Scripts/python.exe manage.py createsuperuser
.venv/Scripts/python.exe manage.py runserver
```

Ouvrir http://127.0.0.1:8000/connexion/. Aucun compte ni mot de passe par
défaut n'est créé. Le superutilisateur créé localement permet la première
connexion. Les comptes existants sont conservés.

Renseigner une `SECRET_KEY` aléatoire stable dans `.env` même en développement
pour conserver les sessions entre redémarrages. Sans clé en développement,
une clé temporaire est générée. En production, l'absence de clé bloque le démarrage.

## Rôles et accès

La commande `configurer_roles` crée Administrateur, Pharmacien, Gestionnaire de
stock, Caissier et Responsable de gestion. Elle ajoute les droits de référence sans retirer les droits
personnalisés.

1. Connectez-vous avec le superutilisateur sur http://127.0.0.1:8000/connexion/.
2. Ouvrez **Utilisateurs et rôles**, puis **Créer un utilisateur**.
3. Saisissez un identifiant et un mot de passe, cochez le rôle métier et
   enregistrez. Pour un compte existant, utilisez **Modifier**.
4. Déconnectez-vous ou ouvrez une fenêtre privée. Sur `/connexion/`, saisissez
   l'identifiant et le mot de passe du compte métier. Le menu affiche les écrans
   autorisés pour ce rôle.

Pour tester la caisse, préparez un brouillon avec le compte **Caissier**,
ouvrez la même vente avec le compte **Pharmacien** et validez-la. Le caissier
peut ensuite enregistrer le paiement. Il faut au préalable un médicament
disponible dans un lot vendable.

Les groupes sont également disponibles dans `/admin/`.
Un groupe Administrateur ne confère pas le statut superutilisateur.
L'accès à l'administration Django nécessite aussi `is_staff`.

Les écrans et les opérations POST contrôlent les permissions côté serveur.
Les nouveaux points d'entrée interactifs sont dans `ventes/operations.py` et
`stock/operations.py`. Les services historiques restent des primitives internes
de confiance, utilisées par les tests historiques ; ne jamais les exposer
directement à une nouvelle route sans contrôle d'accès.

## Parcours métier

1. Créer les catégories, médicaments, fournisseurs et clients depuis les écrans Gestion.
2. Créer une commande d'achat, puis ses lignes. Confirmer la commande dans Achats.
3. Créer une réception et ses lignes avec numéros de lot et dates de péremption.
   Confirmer la réception : le service existant enregistre les entrées de stock.
4. Ouvrir Nouvelle vente, choisir éventuellement un client, ajouter les médicaments
   et retirer les lignes erronées depuis le même écran, puis confirmer la vente.
   Les prix sont repris du médicament lors de l'enregistrement d'une ligne.
   Le service existant déstocke les lots FEFO, hors lots bloqués ou périmés.
5. Enregistrer les paiements partiels ou complets depuis les détails de la vente.
6. Demander un retour depuis la vente en indiquant les quantités concernées et
   le motif. Le valider ou le refuser dans les détails
   de la vente. Les produits retournés restent hors stock vendable.
7. Le remboursement est limité à la valeur du retour restant à rembourser et
   au trop-perçu réel de la vente. Une vente partiellement payée peut donc
   recevoir un avoir par diminution du solde, sans remboursement d'argent.
8. Enregistrer une décision de quarantaine. Une décision est définitive.
   « À détruire » enregistre une instruction ; elle ne certifie pas la destruction physique.
9. Les corrections de stock se font par inventaire justifié : quantité constatée,
   écart et utilisateur sont enregistrés dans les mouvements.
10. Les pages de détail des lots proposent aussi les entrées exceptionnelles et
    les sorties hors vente justifiées ; une sortie ne peut pas dépasser le stock.

Les achats et réceptions disposent de pages de détail pour ajouter leurs lignes
sans changer d'écran. Les rapports proposent des dates de début et de fin, un
bilan financier et les PDF correspondants.

## Interface et suivi quotidien

La navigation regroupe les écrans par activité : quotidien, approvisionnement,
suivi des opérations et référentiels. Sur mobile, le bouton Menu ouvre la
navigation ; Échap la referme. Les liens restent conditionnés par les permissions.

Le dashboard présente les ventes du jour, le chiffre d'affaires net du mois,
l'encaissement net, les alertes et un graphique brut/net sur sept jours. Une
version tabulaire du graphique est également disponible. Les listes proposent
recherche, tri, filtres d'état et pagination ; les médicaments affichent leur
stock réellement vendable. Les ressources graphiques sont stockées localement.

Les formulaires de paiement et de remboursement portent une référence unique.
Une nouvelle soumission du même formulaire renvoie la même opération au lieu
d'en créer une seconde. Pour une autre opération, recharger la page. Les
références historiques restent nulles ; les données existantes sont conservées.

La couverture détaillée des étapes 29 à 41 et les routes des 23 écrans demandés
figurent dans `verification/ETAT_PROMPT.md`.

## Exigences complémentaires du cahier des charges Word

Le guide complet se trouve dans `docs/GUIDE_UTILISATION.md`, la conformité
module par module dans `verification/CONFORMITE_CAHIER_DES_CHARGES.md`, et le
MCD, MLD et les diagrammes UML dans `docs/conception/`.

Les médicaments acceptent une photo JPEG, PNG ou WebP de 5 Mo et 16 millions
de pixels maximum, contrôlée selon son format réel. Les fiches client et
fournisseur présentent leurs historiques autorisés et paginés. L'archivage
conserve l'historique ; la suppression d'une fiche utilisée est bloquée.

La caisse recherche un nom ou un code-barres saisi par un lecteur clavier.
Les médicaments inactifs, sans lot vendable, périmés ou bloqués ne sont pas
proposés dans les sélecteurs. Un lot peut être choisi explicitement ; sans choix,
FEFO s'applique. Les lignes de retour permettent d'identifier le lot délivré.
Les médicaments signalés comme nécessitant une prescription exigent une
référence de contrôle professionnel avant validation. Le responsable doit
paramétrer ce besoin selon une politique validée ; aucune règle réglementaire
n'est déduite automatiquement du nom du médicament.

Les nouveaux paiements CARTE et MOBILE sont **en attente**. Ils réservent le
montant payable, mais ne sont ni encaissés ni remboursables. Une personne ayant
`ventes.confirmer_paiement` vérifie le statut réel chez l'opérateur, atteste le
contrôle et saisit une référence unique pour confirmer, ou refuse le paiement.
Il n'y a pas de passerelle bancaire automatique ni de faux accusé de réception.
Les anciens paiements conservent leur état historique ; leurs preuves ne sont
pas inventées. `manage.py auditer_integrite` signale les incohérences et les
paiements historiques sans preuve, sans modifier de données.

Les mots de passe se modifient dans Mon mot de passe. La récupération utilise
les jetons Django expirant dans une heure, invalidés après usage. En développement,
les e-mails sont écrits dans `tmp/emails/` sans envoi réseau. En production,
configurer `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
`EMAIL_USE_TLS` et `DEFAULT_FROM_EMAIL`, avec le backend SMTP ; aucune adresse
d'expéditeur réelle ni aucun identifiant SMTP n'est inventé. Le service indique
qu'il est indisponible si l'envoi n'est pas configuré.

Les ventes confirmées et leurs lignes ne se modifient plus dans les écrans de
gestion. Les annulations concernent les brouillons ; corriger une vente validée
par un retour et, si nécessaire, un remboursement.

### Remise en stock des retours

Elle est désactivée par défaut. Faire valider la politique métier et les obligations
locales par le responsable de la pharmacie avant de définir
`AUTORISER_REMISE_STOCK_RETOURS=true`. Cette option ne constitue aucune validation
réglementaire. La décision exige les permissions de quarantaine et de correction
de stock, une justification et un lot réellement utilisé par la vente, encore
vendable. Pour un retour couvrant plusieurs lots, scinder les lignes de retour
par lot. Aucune remise en stock automatique n'est réalisée.

## Documents et indicateurs

Facture `FAC-<id>`, reçu `REC-<id>`, retour `RET-<id>` et remboursement `REM-<id>`
sont des références uniques au sein de la base. Les nouvelles ventes validées
conservent un instantané du client, des produits et de la pharmacie. Les soldes
de paiement restent actualisés. Les ventes antérieures utilisent leurs données
courantes. Les PDF ne sont pas des archives fiscales certifiées.
Ne pas utiliser cette numérotation comme preuve de conformité fiscale sans validation locale.
Configurer le nom, l'adresse et les mentions dans l'écran Paramètres ; les
valeurs initiales proviennent de `.env`.
Aucune identification légale n'est inventée.

Les rapports distinguent chiffre d'affaires brut, retours validés, chiffre
d'affaires net, encaissements, remboursements et encaissements nets. Les périodes
sélectionnent les ventes par date de création ; les paiements et retours associés
sont cumulés sur ces ventes, quelle que soit leur propre date. Il s'agit d'une
analyse par cohorte de ventes, pas d'un journal de caisse par date d'encaissement.
Le solde dû est calculé vente par vente après retours et remboursements.
Le classement des médicaments déduit les quantités retournées validées.

## Vérifications

```powershell
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe manage.py test
```

Les tests créent une base temporaire ; ils ne réinitialisent pas les données locales.
Les tests de concurrence sont exécutés uniquement sous PostgreSQL : SQLite
ne fournit pas les mêmes verrous de lignes. Ils apparaissent comme ignorés
dans la suite SQLite. Pour rejouer toute la vérification sur une instance isolée,
avec PostgreSQL installé et ses exécutables dans le PATH :

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe scripts/verifier_postgresql.py
```

Ce script initialise un cluster temporaire protégé par mot de passe sur un port
local libre, exécute les tests, transfère une copie cohérente de SQLite, compare
les données exportées et vérifie des restaurations SQLite et PostgreSQL. Il arrête
son propre cluster à la fin. Les bases de travail existantes ne sont pas modifiées.
Les résultats et exports restent dans `tmp/` (ignoré par Git) et contiennent des
données de la copie : conserver ce répertoire avec des accès restreints.

## Sauvegarde et restauration

```powershell
.venv/Scripts/python.exe manage.py sauvegarder_sqlite
```

La commande emploie l'API de sauvegarde SQLite, vérifie l'intégrité et crée un
nom unique dans `backups/`. Sauvegarder séparément `media/`, `.env` et le code.
Copier les sauvegardes hors du serveur avec des droits d'accès restreints.
Pour restaurer, arrêter les processus applicatifs, conserver une copie de la base
actuelle puis copier la sauvegarde choisie vers une **nouvelle base de test**.
Vérifier son intégrité, les utilisateurs et les soldes avant tout remplacement
de la base active. Le remplacement de production reste une opération manuelle.

## PostgreSQL

Installer `requirements-production.txt`, provisionner une base PostgreSQL vide
et un utilisateur dédié puis renseigner `DB_ENGINE=postgresql`, `DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST` et `DB_PORT`. La configuration garde SQLite
tant que `DB_ENGINE` n'est pas explicitement changé.

Procédure de transfert à répéter d'abord sur des copies :

1. Arrêter les écritures, sauvegarder SQLite et les médias.
2. Avec la configuration SQLite, exécuter `python -X utf8 manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --indent 2 --output sauvegarde-donnees.json`. Le mode UTF-8 est important sous Windows pour conserver les accents.
3. Passer à une base PostgreSQL **vide**, puis lancer `migrate` et `loaddata sauvegarde-donnees.json`.
4. Vérifier les comptages par modèle, relations, séquences, lots, totaux, paiements,
   retours, remboursements et permissions. Exécuter les tests sur PostgreSQL.
5. Reconfigurer les rôles, valider les parcours et conserver SQLite pour le retour arrière.

Le fichier d'export contient des données personnelles et des empreintes de mots
de passe : le conserver hors du dépôt, avec des accès restreints. Cette procédure
a été vérifiée sur une instance PostgreSQL locale isolée. La base de travail
reste SQLite jusqu'au choix explicite d'une base de production.

## Production

Installer les dépendances de production et configurer une clé secrète stable,
`DEBUG=false`, `ALLOWED_HOSTS` avec les vrais noms de domaine et
`CSRF_TRUSTED_ORIGINS` avec leurs origines HTTPS. Configurer les informations
de pharmacie. Ne jamais commiter `.env`.

```powershell
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py configurer_roles
.venv/Scripts/python.exe manage.py collectstatic --noinput
.venv/Scripts/python.exe manage.py check --deploy
.venv/Scripts/waitress-serve.exe --listen=127.0.0.1:8000 --trusted-proxy=127.0.0.1 --trusted-proxy-headers=x-forwarded-proto config.wsgi:application
```

Placer un serveur HTTPS devant Waitress, servir `staticfiles/` et les médias
avec une configuration appropriée, et superviser le processus. Les cookies
sécurisés, redirection HTTPS et HSTS sont activés quand DEBUG est faux.
Définir `TRUST_PROXY=true` uniquement si ce proxy local contrôlé transmet bien
`X-Forwarded-Proto`. Ne jamais accepter cet en-tête depuis un accès direct public. Planifier et
tester les sauvegardes/restaurations, la rotation des logs et les mises à jour.
Configurer le monitoring et les accès système avant ouverture au public.

Un déploiement conteneurisé complet (PostgreSQL, Waitress, statiques, médias et
proxy Caddy avec certificat HTTPS) est fourni dans `compose.yaml`. Voir
`deploy/README.md`. La configuration Compose a été validée sans démarrer de
service public. Aucun vrai domaine ni serveur externe n'a été configuré.

## Vérification visuelle et limites avant exploitation

- Le contrôle navigateur est bloqué par l'outil d'automatisation ; vérifier les
  pages et le mobile sur la machine cible. Les PDF ont été rendus en PNG et inspectés.
- Les essais de concurrence, transfert et restauration sont vérifiés sur PostgreSQL
  local isolé ; planifier également les sauvegardes de la future infrastructure réelle.
- Validation des règles locales de conservation, remise en stock et facturation.
- Les écrans Utilisateurs et Paramètres sont accessibles aux utilisateurs autorisés ;
  les permissions détaillées restent administrables dans Django.
- Les nouvelles ventes disposent d'un instantané de facturation ; les ventes
  antérieures n'en ont pas. Les PDF ne sont ni signés ni archivés comme documents fiscaux certifiés.
- Bootstrap et les icônes sont inclus avec leurs licences dans `static/vendor/` :
  l'interface n'a pas besoin d'un CDN.
- Aucun hébergement externe ni certificat HTTPS n'est provisionné par ce dépôt.

Les données fictives et rendus PDF se préparent avec
`python scripts/preparer_revue.py`. Cette commande utilise exclusivement une
base dans `tmp/revue/`. `python scripts/verifier_wsgi.py` contrôle les pages
authentifiées et les protections de production via un serveur Waitress local
temporaire. Ces commandes ne créent aucun compte dans la base de travail.
