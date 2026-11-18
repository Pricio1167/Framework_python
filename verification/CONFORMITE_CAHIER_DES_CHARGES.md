# Conformité au cahier des charges Word

Référence lue intégralement : `Cahier des charges projet pharmacie.docx`.
L'analyse comprend le texte, les huit tableaux et les six images indicatives.
Le document original n'a pas été modifié. Cette grille décrit les fonctionnalités
implémentées ; les résultats des commandes exécutées sont dans `resultats.json`.

## Modules fonctionnels

| Référence | Implémentation dans le projet | Vérification principale |
| --- | --- | --- |
| A — Authentification | Connexion/déconnexion, comptes, activation, cinq groupes, mot de passe, récupération par jeton expirant, audit sans mot de passe en clair | Tests de changement, expiration, usage unique, absence de divulgation d'un compte inconnu et contrôles de permissions |
| B — Médicaments | Champs du catalogue, photo réelle contrôlée, fiche, recherche nom/code-barres, filtre catégorie, tri, pagination, archivage et suppression protégée | `CahierChargesTests.test_photo_ajout_detail_et_filtre_categorie`, tests des fichiers, du code-barres et de l'historique |
| C — Catégories | Création, liste, modification, recherche, détail et refus de suppression d'une catégorie utilisée | `test_archivage_et_suppression_protegee` |
| D — Fournisseurs | Coordonnées, recherche, création/modification, désactivation, fiche et historique paginé des commandes/réceptions et montants | `test_historique_clients_et_fournisseurs`, parcours achats et WSGI |
| E — Clients | Fiches minimales, actif/inactif, historique autorisé, client facultatif en vente | Parcours de création de vente, historique et accès interdit au Responsable de gestion sans droit client |
| F — Achats | Commandes/lignes, total, brouillon, confirmation, réceptions partielles, annulation avant réception validée, bons PDF et instantanés | Tests achats existants, parcours web complet et tests des nouveaux documents |
| G — Stocks | Stock disponible, FEFO, lots, mouvements, sorties/entrées exceptionnelles, inventaires, écarts, blocage et alertes | Tests stock, ventes et concurrence PostgreSQL, audit d'intégrité |
| H — Ventes | Caisse, recherche/scanner clavier, lot explicite ou FEFO, panier, prix historiques, validation atomique, paiements partiels, reçus | Tests FEFO, lot réservé, prix figés, quantités, rejeu, paiements en attente et confirmation |
| I — Retours | Vente d'origine, ligne, lot délivré, quantité, motif, responsable, validation/refus, quarantaine et remboursement plafonné | Tests de retours cumulés, lot non délivré, décision unique et absence de remboursement sur paiement non confirmé |
| J — Dashboard | Médicaments actifs, jour/mois, période sélectionnée pour ventes et achats, brut/net/encaissements, classement et alertes | Tests des données réelles, du graphique et du masquage sans permission ; contrôle WSGI |
| K — PDF | Facture, reçu, retour/remboursement, bons de commande et réception, rapports ventes/achats/stock et liste des péremptions | Tests PDF et rendu en images sur données fictives |

Les cinq profils sont Administrateur, Pharmacien (responsable selon les droits),
Gestionnaire de stock, Caissier et Responsable de gestion. Le cumul des groupes
reste soumis à une personne autorisée. Les clients/fournisseurs sont des fiches
commerciales ; le document ne prévoit pas de portail public pour eux.

## Règles RG01 à RG12

| Règle | Garantie |
| --- | --- |
| RG01 — Identifiant unique | Clés primaires Django et contraintes de base |
| RG02 — Code-barres unique | Champ unique lorsqu'il est renseigné, validation serveur et test du doublon |
| RG03 — Prix et quantités validés | Formulaires, validateurs, services transactionnels et scénarios négatifs |
| RG04 — Pas de stock à la commande | Test `test_commande_ne_modifie_pas_stock` |
| RG05 — Réception unique | Test `test_reception_double_interdite` et réceptions concurrentes sous verrou |
| RG06 — Sortie unique par vente | Test de double validation et scénarios PostgreSQL concurrents |
| RG07 — Stock non négatif | Vérification sous verrou, bornes de quantité, contraintes Django et tests d'insuffisance |
| RG08 — Lots non vendables exclus | Sélecteurs filtrés et revérification transactionnelle, tests périmé/bloqué/lot demandé |
| RG09 — Auteur et historique | Utilisateur, dates, mouvements, instantanés et événements d'audit |
| RG10 — Historique conservé | Opérations validées protégées, archivage des références, annulations et retours traçables |
| RG11 — Fonctions autorisées | Permissions dans les vues/services d'opérations, liens conditionnels et tests d'accès direct |
| RG12 — Prix historiques | Prix sur les lignes, instantanés des nouvelles ventes/commandes/réceptions et tests après modification du catalogue |

## Critères de recette du chapitre 9

| Scénario | Couverture |
| --- | --- |
| Ajouter un médicament avec photo | Upload de PNG, stockage puis affichage dans la fiche ; type, extension et taille invalides refusés |
| Modifier un médicament | Écrans de modification et conservation des prix historiques vérifiés |
| Supprimer ou archiver | Archivage sans perte de vente, suppression bloquée si dépendance |
| Réceptionner 20 unités | `test_bons_achats_reception_rapports`, tests de double réception et concurrence |
| Vendre une quantité | Tests vente et parcours complet, comparaison des quantités du lot |
| Dépasser le stock | Refus de la validation et absence de mutation partielle |
| Lot périmé | Exclusion de la sélection et refus serveur |
| Accès sans permission | Refus 403 sur les routes et services protégés |
| Reçu PDF | Flux PDF valide, montants calculés et inspection du rendu fictif |
| Deux validations simultanées | Suite PostgreSQL avec verrous de lignes et plafonds financiers |
| Restauration | Copie SQLite vérifiée et pg_dump/pg_restore dans une seconde base isolée |

## Architecture et livrables

L'architecture Django modulaire est conservée. Le code, les migrations et les
assets locaux sont dans le dépôt. Les données fictives sont produites par
`scripts/preparer_revue.py` dans une base distincte de la base de travail.
Le README couvre l'installation et le déploiement ; `docs/GUIDE_UTILISATION.md`
couvre les parcours. `docs/conception/` contient MCD, MLD, schéma réel exporté,
diagramme de classes, séquence de vente et cas d'utilisation.

La sécurité comprend CSRF, validation serveur, permissions, contrôles d'images,
secrets par environnement, configuration HTTPS, journalisation, sauvegardes et
restaurations sur copies. Les opérations de base de données sensibles sont
atomiques. Les listes et historiques disposent de pagination.

## Conditions d'exploitation réelles

- Le contrôle d'un paiement électronique est une opération manuelle autorisée
  après consultation du statut réel chez le prestataire. Aucun connecteur bancaire
  externe n'est simulé. Les paiements historiques sans preuve ne sont pas réécrits.
- Le SMTP réel nécessite ses paramètres. En développement, les e-mails de
  récupération sont écrits dans un répertoire privé de travail ; les tests
  utilisent une boîte mémoire, sans envoi à un tiers.
- Les mentions de pharmacie, règles de prescription, retours et conservation
  doivent être validées localement par le responsable, conformément au chapitre 12.
  Le programme ne déduit pas une autorisation de vente d'une simple entrée au catalogue.
- Les références historiques antérieures aux instantanés restent conservées
  sans reconstitution fictive de preuves ou d'identité passée.
- Le contrôle visuel navigateur/mobile dépend de la disponibilité de l'outil
  de navigateur. Une absence de contrôle visuel n'est pas présentée comme une réussite.
- Le domaine, le serveur externe, le certificat et les comptes de prestataires
  réels ne sont ni inventés ni présentés comme déjà déployés.

Les fonctions explicitement hors périmètre — diagnostic, prescription automatique,
consultation médicale, fabrication, système national obligatoire, comptabilité
générale complète et application mobile native — ne sont pas ajoutées.
