# Guide d'utilisation PHARMAGEST

## Prise en main

PHARMAGEST permet à l'équipe de suivre les approvisionnements, les lots, les
ventes et les règlements d'une pharmacie. Les montants sont affichés en Ariary.

Pour une première installation, suivre le [démarrage sous Windows](../README.md#installation-et-démarrage-sous-windows).
Si l'application est déjà en service, utiliser l'adresse fournie par le
responsable. En local, ouvrir [la page de connexion sur le port 8000](http://127.0.0.1:8000/connexion/)
si le serveur du projet a été démarré sur ce port.

Pour préparer une première vente, suivre ce parcours dans l'ordre.

1. Renseigner les coordonnées de la pharmacie dans **Paramètres** et créer les comptes du personnel.
2. Créer une catégorie, un médicament et un fournisseur actif.
3. Confirmer une commande d'achat, puis valider sa réception avec un numéro de lot et une date de péremption.
4. Créer une vente et ajouter le médicament. Faire valider la vente, enregistrer le règlement, puis ouvrir la facture et le reçu.

## Connexion et accès

Démarrer le serveur selon le README, puis ouvrir `/connexion/`. Les comptes
sont créés par une personne autorisée. Il n'existe aucun mot de passe universel.
Les menus dépendent des groupes Django. Les clients et fournisseurs sont des
fiches gérées par le personnel, sans compte public ni portail autonome.

L'Administrateur gère les comptes, les rôles et les paramètres. Le Pharmacien
valide les ventes, les retours et les contrôles professionnels autorisés. Le
Gestionnaire de stock gère les approvisionnements et inventaires. Le Caissier
prépare les ventes, enregistre les paiements et imprime les reçus autorisés.
Le Responsable de gestion consulte les indicateurs et rapports sans modifier
les transactions. Un administrateur peut cumuler les groupes selon les fonctions.

Pour changer son mot de passe, choisir Mon mot de passe. Pour le récupérer,
utiliser Mot de passe oublié sur la connexion et ouvrir le lien reçu par e-mail.
Le lien expire en une heure et ne peut pas être réutilisé après changement.
Si le service d'e-mail n'est pas configuré, contacter le responsable.
Avec la configuration locale de développement par défaut, les messages de
récupération sont enregistrés dans `tmp/emails/`.

### Créer un compte pour un membre du personnel

1. Avec un compte autorisé, ouvrir **Utilisateurs et rôles**, puis **Créer un utilisateur**.
2. Saisir le nom d'utilisateur et le mot de passe, sélectionner le ou les rôles nécessaires et enregistrer.
3. Ouvrir une fenêtre privée et vérifier que le nouveau compte accède aux écrans attendus.

Pour changer un rôle ou désactiver un compte, ouvrir sa fiche depuis
**Utilisateurs et rôles** et choisir **Modifier**. Les écrans disponibles
dépendent des permissions accordées. L'administration Django sous `/admin/`
est un écran distinct qui exige le statut équipe.

## Médicaments et catégories

Ouvrir Médicaments, Ajouter, puis renseigner les champs obligatoires. Le
code-barres doit être unique lorsqu'il est renseigné. Une photo JPEG, PNG ou
WebP est facultative : 5 Mo et 16 millions de pixels maximum. Le type réel et
l'extension sont contrôlés. La photo s'affiche dans la liste et la fiche.

La liste recherche un nom ou code-barres et se filtre par catégorie. La fiche
affiche les caractéristiques, le prix, le stock vendable et les lots selon les
permissions. Le champ de prescription doit être configuré par un responsable
selon la politique de délivrance réellement validée. Une présence dans le
catalogue ne constitue pas une autorisation réglementaire de délivrance.

Modifier met à jour le catalogue. Archiver désactive le médicament et conserve
les ventes passées. Supprimer si inutilisée est réservé aux personnes autorisées ;
la base refuse la suppression si un lot ou une opération dépend de la fiche.
Une catégorie utilisée par des médicaments ne peut pas être supprimée.

## Fournisseurs et clients

Les fiches regroupent les coordonnées utiles et le statut actif/inactif.
Ouvrir Fiche pour consulter les achats et montants réceptionnés du fournisseur,
ou les ventes du client, sous réserve des permissions correspondantes. Les
historiques sont paginés. Désactiver une fiche conserve ses opérations.
Une vente peut utiliser un client de passage si la politique applicable le permet.

## Approvisionnement

1. Dans Achats, créer une commande avec un fournisseur actif.
2. Ajouter les médicaments, quantités et prix d'achat sur le détail de commande.
3. Vérifier le total puis confirmer. Le stock ne change pas à cette étape.
4. Télécharger le bon de commande si nécessaire.
5. Préparer une réception rattachée à la commande. Ajouter chaque quantité
   réellement reçue, son numéro de lot et sa date de péremption.
6. Confirmer la réception. Les entrées de stock et leur historique sont créés
   une seule fois. Le statut de commande devient partiel ou entièrement reçu.
7. Télécharger le bon de réception, avec quantités, lots et montants.

Une commande sans réception validée peut être annulée avec un motif. Une
commande partiellement réceptionnée ne s'annule pas par cette action.
Les lignes et prix des opérations confirmées ne sont plus modifiables dans les écrans.

## Vente et caisse

Créer une nouvelle vente, avec un client facultatif. Rechercher un médicament
par nom ou placer le curseur dans le champ de recherche pour scanner un code-barres
avec un lecteur fonctionnant comme un clavier. Choisir le médicament et la quantité.

Le lot est facultatif. Sans choix, la règle FEFO prélève d'abord dans les lots
vendables dont la date de péremption est la plus proche. Si un lot est
sélectionné, il doit appartenir au médicament, être non bloqué, non périmé et
suffisant. Les lots explicitement demandés sont réservés avant l'allocation
automatique des autres lignes. La disponibilité est revérifiée sous verrou à
la validation ; le stock peut avoir changé depuis la saisie.

Retirer une ligne tant que la vente est en brouillon. Vérifier les montants et,
si une prescription est requise, enregistrer la référence du contrôle professionnel
sans recopier de données médicales inutiles. Une personne autorisée confirme la
vente. Le stock et l'historique sont mis à jour atomiquement. La facture conserve
les prix et l'identité enregistrés pour les nouvelles ventes validées.

## Paiements

L'espèce est enregistrée comme encaissée. CARTE et MOBILE sont enregistrés en
attente et ne diminuent pas le solde réellement dû. Le montant en attente est
réservé pour éviter un second engagement excessif.

Un vérificateur autorisé consulte le statut réel sur le terminal, chez
l'opérateur ou dans le justificatif fiable du prestataire. Il saisit une référence
de transaction non réutilisée, atteste ce contrôle et confirme le paiement. Une
simple déclaration du client ne suffit pas. En cas d'échec, il refuse avec une
justification. Les paiements refusés ne sont ni encaissés ni réservés.

Si un retour a été validé pendant l'attente, un règlement réellement reçu reste
enregistrable dans la limite du montant initialement payable. Le trop-perçu issu
du retour devient alors remboursable ; il n'est pas effacé par le changement de solde.

Le reçu est disponible après confirmation. Les paiements partiels sont possibles
dans la limite du solde. Une nouvelle soumission du même formulaire financier
réutilise son opération ; pour un autre paiement, recharger la page.

## Retours et remboursements

Depuis la vente, indiquer les quantités, le lot réellement retourné et le motif.
La quantité cumulée ne doit dépasser ni la vente ni les unités délivrées de ce
lot. Un responsable autorisé valide ou refuse la demande avec traçabilité.

La validation met les produits hors stock vendable. Elle ne les remet pas en
vente automatiquement. Enregistrer une décision de quarantaine : conservation
hors vente, instruction de destruction ou remise en stock selon une politique
explicitement activée. L'instruction de destruction ne certifie pas sa réalisation.

Un remboursement ne peut dépasser le montant du retour et le trop-perçu
réellement encaissé. Un paiement électronique en attente n'est pas remboursable.
Une vente partiellement payée peut simplement voir diminuer son solde dû.
Les documents de retour et de remboursement restent accessibles selon les droits.

## Stock et inventaires

Les filtres des stocks distinguent lots proches de la péremption, périmés et
bloqués. La fiche de lot affiche les mouvements. Pour un inventaire, saisir la
quantité physique constatée et justifier l'écart. Les entrées exceptionnelles et
sorties hors vente demandent aussi un motif. Une sortie supérieure au stock est
refusée. Un lot périmé ou bloqué est toujours exclu des ventes.

## Dashboard et documents

Le dashboard affiche médicaments actifs, ventes, encaissements, soldes et alertes.
Le formulaire de période filtre les ventes, commandes et réceptions sur leurs
dates respectives. Les commandes et réceptions ne représentent pas un bénéfice.
Le chiffre d'affaires brut, net des retours et les encaissements sont distincts.

Dans Rapports, sélectionner les dates puis télécharger les rapports de ventes,
achats, stocks et péremptions. Les documents utilisent les informations de
pharmacie renseignées dans Paramètres. Aucun identifiant fiscal n'est inventé.

Le rapport de ventes sélectionne les ventes selon leur date de création et
inclut les règlements et retours associés, même s'ils ont été enregistrés après
la période choisie. Pour rapprocher la caisse, distinguer le montant des ventes,
les paiements confirmés, les remboursements et le solde restant dû.

## Dépannage courant

| Situation | Vérification à faire |
| --- | --- |
| Django refuse le nom d'utilisateur et le mot de passe | Vérifier le nom d'utilisateur et ses majuscules, ressaisir le mot de passe manuellement et vérifier que le compte est actif. Pour une installation locale, contrôler le port affiché dans la console Django. Deux copies du projet peuvent utiliser des bases différentes. |
| Le port 8000 ouvre une autre copie du projet | Depuis le dossier du bon projet, démarrer Django avec `./.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8001` si le port est libre, puis ouvrir [la connexion sur le port 8001](http://127.0.0.1:8001/connexion/). |
| Le mot de passe d'un compte local est perdu | Utiliser **Mot de passe oublié ?**. Une personne autorisée ayant accès au terminal du projet peut aussi exécuter `./.venv/Scripts/python.exe manage.py changepassword NOM_UTILISATEUR` et saisir le nouveau mot de passe à l'invite. |
| Un menu ou une action est absent | Demander au responsable de vérifier les rôles et les permissions du compte. Contrôler aussi le statut de l'opération, car certaines actions sont réservées aux brouillons ou aux ventes validées. |
| Un médicament est absent du sélecteur de vente | Vérifier que le médicament est actif et qu'il dispose d'un lot vendable avec une quantité suffisante. Au besoin, vérifier que la réception a bien été confirmée. |
| Un paiement par carte ou mobile ne réduit pas le solde dû | Ouvrir la vente et vérifier le statut du paiement. Une personne autorisée doit confirmer le règlement après contrôle auprès du prestataire. |

## Sauvegarde et responsabilité d'exploitation

Le README décrit les sauvegardes SQLite, le transfert PostgreSQL et les essais
de restauration isolée. Sauvegarder également les photos de `media/`, les secrets
et la version du code dans un emplacement protégé hors serveur. Ne jamais
remplacer une base active ou supprimer un volume de données sans procédure validée.

Avant une exploitation réelle, le responsable doit faire valider les règles de
délivrance, les retours, les paiements, les mentions et la conservation des
documents pour son territoire. Le logiciel ne remplace pas le contrôle professionnel.
