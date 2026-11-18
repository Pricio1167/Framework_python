# Modèle logique des données

Structure générée depuis les modèles Django. Aucune donnée métier n’est exportée.

## utilisateurs.Utilisateur — `utilisateurs_utilisateur`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| password | CharField(128) |  | Non |
| last_login | DateTimeField |  | Oui |
| is_superuser | BooleanField |  | Non |
| username | CharField(150) |  | Non |
| first_name | CharField(150) |  | Non |
| last_name | CharField(150) |  | Non |
| email | CharField(254) |  | Non |
| is_staff | BooleanField |  | Non |
| is_active | BooleanField |  | Non |
| date_joined | DateTimeField |  | Non |
| telephone | CharField(20) |  | Non |
| date_creation | DateTimeField |  | Non |

Relation N–N `groups` vers `auth.Group` par `utilisateurs_utilisateur_groups`.

Relation N–N `user_permissions` vers `auth.Permission` par `utilisateurs_utilisateur_user_permissions`.

## medicaments.Categorie — `medicaments_categorie`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| nom | CharField(100) |  | Non |
| description | TextField |  | Non |

## medicaments.Medicament — `medicaments_medicament`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| nom_commercial | CharField(200) |  | Non |
| denomination_generique | CharField(200) |  | Non |
| categorie_id | ForeignKey | FK → medicaments.Categorie (PROTECT) | Non |
| forme | CharField(30) |  | Non |
| dosage | CharField(100) |  | Non |
| laboratoire | CharField(150) |  | Non |
| code_barres | CharField(100) |  | Oui |
| photo | FileField(100) |  | Oui |
| prix_achat | DecimalField(12,2) |  | Non |
| prix_vente | DecimalField(12,2) |  | Non |
| seuil_alerte | PositiveIntegerField |  | Non |
| actif | BooleanField |  | Non |
| prescription_requise | BooleanField |  | Non |
| date_creation | DateTimeField |  | Non |

## fournisseurs.Fournisseur — `fournisseurs_fournisseur`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| nom | CharField(200) |  | Non |
| adresse | TextField |  | Non |
| telephone | CharField(20) |  | Non |
| email | CharField(254) |  | Non |
| numero_fiscal | CharField(100) |  | Non |
| contact_principal | CharField(150) |  | Non |
| actif | BooleanField |  | Non |
| date_creation | DateTimeField |  | Non |

## clients.Client — `clients_client`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| nom | CharField(150) |  | Non |
| telephone | CharField(20) |  | Non |
| email | CharField(254) |  | Non |
| adresse | TextField |  | Non |
| actif | BooleanField |  | Non |
| date_creation | DateTimeField |  | Non |

## achats.CommandeAchat — `achats_commandeachat`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| instantane_document | JSONField |  | Non |
| fournisseur_id | ForeignKey | FK → fournisseurs.Fournisseur (PROTECT) | Non |
| date_commande | DateTimeField |  | Non |
| statut | CharField(20) |  | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |

## achats.LigneAchat — `achats_ligneachat`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| commande_id | ForeignKey | FK → achats.CommandeAchat (CASCADE) | Non |
| medicament_id | ForeignKey | FK → medicaments.Medicament (PROTECT) | Non |
| quantite | PositiveIntegerField |  | Non |
| prix_unitaire | DecimalField(12,2) |  | Non |

## achats.ReceptionAchat — `achats_receptionachat`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| instantane_document | JSONField |  | Non |
| commande_id | ForeignKey | FK → achats.CommandeAchat (PROTECT) | Non |
| date_reception | DateTimeField |  | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| validee | BooleanField |  | Non |

## achats.LigneReception — `achats_lignereception`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| reception_id | ForeignKey | FK → achats.ReceptionAchat (PROTECT) | Non |
| ligne_achat_id | ForeignKey | FK → achats.LigneAchat (PROTECT) | Non |
| numero_lot | CharField(100) |  | Non |
| date_peremption | DateField |  | Non |
| quantite_recue | PositiveIntegerField |  | Non |

## stock.LotStock — `stock_lotstock`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| medicament_id | ForeignKey | FK → medicaments.Medicament (PROTECT) | Non |
| numero_lot | CharField(100) |  | Non |
| date_peremption | DateField |  | Non |
| quantite | PositiveIntegerField |  | Non |
| quantite_recue | PositiveIntegerField |  | Non |
| bloque | BooleanField |  | Non |
| date_creation | DateTimeField |  | Non |

Contrainte : `unique_lot_par_medicament` (UniqueConstraint).

## stock.MouvementStock — `stock_mouvementstock`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| lot_id | ForeignKey | FK → stock.LotStock (PROTECT) | Non |
| type_mouvement | CharField(20) |  | Non |
| quantite | PositiveIntegerField |  | Non |
| motif | TextField |  | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| date_mouvement | DateTimeField |  | Non |

## ventes.Vente — `ventes_vente`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| client_id | ForeignKey | FK → clients.Client (PROTECT) | Oui |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| date_vente | DateTimeField |  | Non |
| instantane_facture | JSONField |  | Non |
| controle_delivrance | JSONField |  | Non |
| statut | CharField(20) |  | Non |

## ventes.LigneVente — `ventes_lignevente`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| lot_demande_id | ForeignKey | FK → stock.LotStock (PROTECT) | Oui |
| vente_id | ForeignKey | FK → ventes.Vente (CASCADE) | Non |
| medicament_id | ForeignKey | FK → medicaments.Medicament (PROTECT) | Non |
| quantite | PositiveIntegerField |  | Non |
| prix_unitaire | DecimalField(12,2) |  | Non |

## ventes.Paiement — `ventes_paiement`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| cle_operation | UUIDField(32) |  | Oui |
| statut | CharField(15) |  | Non |
| reference_verification | CharField(200) |  | Non |
| verifie_par_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Oui |
| date_verification | DateTimeField |  | Oui |
| vente_id | ForeignKey | FK → ventes.Vente (PROTECT) | Non |
| montant | DecimalField(12,2) |  | Non |
| mode | CharField(20) |  | Non |
| date_paiement | DateTimeField |  | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |

Contrainte : `reference_electronique_confirmee_unique` (UniqueConstraint).

## ventes.RetourVente — `ventes_retourvente`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| vente_id | ForeignKey | FK → ventes.Vente (PROTECT) | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| date_retour | DateTimeField |  | Non |
| statut | CharField(20) |  | Non |
| motif | TextField |  | Non |

## ventes.LigneRetour — `ventes_ligneretour`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| lot_origine_id | ForeignKey | FK → stock.LotStock (PROTECT) | Oui |
| retour_id | ForeignKey | FK → ventes.RetourVente (CASCADE) | Non |
| ligne_vente_id | ForeignKey | FK → ventes.LigneVente (PROTECT) | Non |
| quantite | PositiveIntegerField |  | Non |

## ventes.LigneVenteLot — `ventes_ligneventelot`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| ligne_vente_id | ForeignKey | FK → ventes.LigneVente (PROTECT) | Non |
| lot_id | ForeignKey | FK → stock.LotStock (PROTECT) | Non |
| quantite | PositiveIntegerField |  | Non |

## ventes.Remboursement — `ventes_remboursement`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| cle_operation | UUIDField(32) |  | Oui |
| retour_id | ForeignKey | FK → ventes.RetourVente (PROTECT) | Non |
| montant | DecimalField(12,2) |  | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| motif | TextField |  | Non |
| date_creation | DateTimeField |  | Non |

## ventes.EvenementAudit — `ventes_evenementaudit`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| acteur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| action | CharField(60) |  | Non |
| objet | CharField(150) |  | Non |
| motif | TextField |  | Non |
| date_creation | DateTimeField |  | Non |

## ventes.DecisionQuarantaine — `ventes_decisionquarantaine`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| ligne_retour_id | OneToOneField | FK → ventes.LigneRetour (PROTECT) | Non |
| decision | CharField(20) |  | Non |
| lot_id | ForeignKey | FK → stock.LotStock (PROTECT) | Oui |
| motif | TextField |  | Non |
| utilisateur_id | ForeignKey | FK → utilisateurs.Utilisateur (PROTECT) | Non |
| date_creation | DateTimeField |  | Non |

## dashboard.ParametresPharmacie — `dashboard_parametrespharmacie`

| Colonne | Type | Clé / relation | Null autorisé |
| --- | --- | --- | --- |
| id | BigAutoField | PK | Non |
| nom | CharField(200) |  | Non |
| adresse | TextField |  | Non |
| mentions | TextField |  | Non |

