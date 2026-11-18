# Dossier de conception PHARMAGEST

Le système suit l'architecture MVT Django. Les applications métier sont séparées ;
les formulaires valident la saisie, les vues contrôlent les droits, et les services
transactionnels effectuent les opérations de stock et financières. Les templates
présentent les données réelles. Les fichiers ci-dessous complètent le cahier des charges.

- `MCD.mmd` : entités et cardinalités métier principales.
- `MLD.md` : tables, colonnes, clés étrangères, tables de liaison et contraintes réelles.
- `schema.json` : schéma exploitable par un outil, sans données métier.
- `UML_classes.mmd` : diagramme des classes généré depuis Django.
- `UML_vente_sequence.mmd` : validation d'une vente et allocation des lots.
- `UML_cas_utilisation.mmd` : acteurs et fonctions autorisées.

Les fichiers `.mmd` s'affichent avec un visualiseur Mermaid. Regénérer le modèle
logique et les classes après modification des modèles :

```powershell
.venv/Scripts/python.exe scripts/exporter_conception.py
```

## Acteurs et frontière du système

Les comptes authentifiés appartiennent au personnel : Administrateur, Pharmacien
(responsable selon ses permissions), Gestionnaire de stock, Caissier et Responsable
de gestion. Les groupes peuvent être cumulés par une personne autorisée. Les clients
et fournisseurs sont des fiches commerciales, pas des portails publics de connexion.

## Choix d'intégrité

Les relations d'historique utilisent PROTECT. Les entités utilisées sont archivées
ou désactivées au lieu d'être effacées. Les ventes et réceptions validées ne sont
pas modifiables dans les interfaces métier. Les prix sont conservés sur les lignes ;
les nouveaux documents confirmés possèdent un instantané d'identité et de contenu.

La validation verrouille les opérations et les lots dans une transaction atomique.
FEFO choisit les lots vendables ; un lot explicitement demandé est réservé avant
l'allocation automatique des autres lignes. Les retours désignent les unités
réellement délivrées et restent hors vente jusqu'à une décision autorisée.

Un paiement électronique est en attente. La confirmation exige une permission,
une référence et la vérification effective de son statut auprès du prestataire.
La référence confirmée est unique pour le moyen de paiement. Les montants en
attente ne sont pas encaissés ni remboursables. Aucun prestataire bancaire externe
n'est simulé ou présenté comme intégré.

Les modèles historiques antérieurs aux instantanés conservent leurs données :
aucun passé fiscal, aucune prescription ni preuve de paiement n'est reconstitué.
