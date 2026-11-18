# État des exigences de prompt.md

Ce document distingue l'implémentation, les essais techniques et les opérations
qui dépendent d'informations réelles. Les résultats chiffrés sont consignés dans
`resultats.json` et `RAPPORT_FINAL.md`.

| Étape | État du livrable local |
| --- | --- |
| 29 — Rôles et permissions | Cinq groupes (dont Responsable de gestion ajouté selon le cahier des charges Word), commande idempotente, droits personnalisés conservés, contrôles serveur, menus conditionnels, tests d'accès |
| 30 — Ventes et paiements | Saisie, lignes, prix, validation atomique FEFO, paiements partiels, solde, historique, annulation des brouillons et références uniques contre les doubles soumissions |
| 31 — Retours et remboursements | Demande par ligne, quantités déjà retournées, validation/refus motivés, quarantaine, décision explicite, remboursement plafonné et rejeu idempotent |
| 32 — PDF | Facture, reçu, retour, remboursement et rapports ReportLab ; identité configurable et instantané des nouvelles ventes |
| 33 — Stocks | Entrées/sorties justifiées, corrections, lots, mouvements, blocages, péremptions, alertes, inventaires et écarts |
| 34 — Dashboard | Données réelles, indicateurs bruts/nets, sept jours d'évolution, alertes, opérations récentes et classement des produits |
| 35–38 — Interface | Bootstrap et icônes locaux, navigation regroupée, menu mobile, pages métier, formulaires, filtres, recherche, tri, pagination, états et confirmations |
| 39 — Tests | Suites SQLite et PostgreSQL, parcours complets, accès refusés, CSRF, finances, PDF, concurrence et doubles soumissions ; résultats du dernier passage dans le rapport |
| 40 — PostgreSQL | Configuration par environnement, migrations testées, transfert sur copie, comparaison des données et restauration vérifiée ; SQLite de travail conservée |
| 41 — Production | Configuration sécurisée, fichiers de déploiement, serveur WSGI vérifié, collecte statique, sauvegarde/restauration et documentation ; déploiement externe préparé |

## Les 23 écrans et accès demandés

| Écran | Route |
| --- | --- |
| Connexion / déconnexion | `/connexion/` ; `/deconnexion/` en POST |
| Dashboard | `/` |
| Médicaments | `/gestion/medicaments/` |
| Ajout / modification médicament | `/gestion/medicaments/ajouter/` ; `/gestion/medicaments/<id>/modifier/` |
| Catégories | `/gestion/categories/` |
| Fournisseurs | `/gestion/fournisseurs/` |
| Clients | `/gestion/clients/` |
| Achats | `/gestion/achats/` ; détail `/gestion/achats/<id>/` |
| Réceptions | `/gestion/receptions/` ; détail `/gestion/receptions/<id>/` |
| Stocks | `/gestion/stocks/` |
| Détails des lots | `/gestion/stocks/<id>/` |
| Mouvements | `/gestion/mouvements/` |
| Alertes de péremption | `/gestion/stocks/?stock=proches` ; `?stock=perimes` |
| Ventes | `/gestion/ventes/` |
| Création de vente | `/ventes/nouvelle/` |
| Détail d'une vente | `/ventes/<id>/` |
| Paiements | Saisie dans la vente ; historique `/gestion/paiements/` |
| Retours | Demande et validation dans la vente ; historique `/gestion/retours/` |
| Remboursements | Saisie dans la vente ; historique `/gestion/remboursements/` |
| Rapports | `/rapports/` |
| PDF | Liens protégés dans les ventes, paiements, retours et rapports |
| Utilisateurs et rôles | `/utilisateurs/` |
| Paramètres de pharmacie | `/parametres/` |

## Limites vérifiables

- Le navigateur intégré reste indisponible : la revue visuelle réelle sur
  ordinateur/mobile et les interactions au clavier ne sont pas déclarées réussies.
  Les pages, parcours et permissions sont testés par Django et HTTP WSGI.
- Le nom, l'adresse et les mentions légales réels sont à renseigner dans Paramètres.
  Aucun renseignement fiscal ou commercial n'est inventé.
- La remise en stock des retours est désactivée par défaut et exige une politique
  métier explicitement validée avant activation.
- Les factures antérieures à l'ajout des instantanés n'ont pas d'identité historique
  reconstruite. Les PDF ne sont pas présentés comme archives fiscales certifiées.
- Le domaine et le serveur externes doivent être fournis pour une mise en ligne.
  Le prompt exige de préparer ce déploiement sans prétendre l'avoir effectué.

Le développement local peut être livré sans inventer ces informations. La revue
utilisateur et l'installation sur une infrastructure réelle sont des validations
distinctes et ne sont pas annoncées comme déjà réalisées.
