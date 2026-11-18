
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


class Vente(models.Model):

    STATUTS = [
        ("BROUILLON", "Brouillon"),
        ("VALIDEE", "Validée"),
        ("ANNULEE", "Annulée"),
    ]

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ventes"
    )

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.PROTECT,
        related_name="ventes"
    )

    date_vente = models.DateTimeField(auto_now_add=True)
    instantane_facture = models.JSONField(default=dict, blank=True, editable=False)
    controle_delivrance = models.JSONField(default=dict, blank=True, editable=False)

    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default="BROUILLON"
    )

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ["-date_vente"]

    @property
    def total(self):
        return sum(
            (
                ligne.sous_total
                for ligne in self.lignes.all()
            ),
            Decimal("0.00")
        )

    def __str__(self):
        return f"Vente N°{self.pk}"


class LigneVente(models.Model):
    lot_demande = models.ForeignKey("stock.LotStock", on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="lignes_demandees", verbose_name="Lot demandé")

    vente = models.ForeignKey(
        Vente,
        on_delete=models.CASCADE,
        related_name="lignes"
    )

    medicament = models.ForeignKey(
        "medicaments.Medicament",
        on_delete=models.PROTECT,
        related_name="lignes_vente"
    )

    quantite = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        return f"{self.medicament} - {self.quantite}"


class Paiement(models.Model):
    cle_operation = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    statut = models.CharField(max_length=15, choices=[("CONFIRME", "Confirmé"), ("EN_ATTENTE", "En attente"),
                                                     ("REFUSE", "Refusé")], default="CONFIRME")
    reference_verification = models.CharField(max_length=200, blank=True)
    verifie_par = models.ForeignKey("utilisateurs.Utilisateur", on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="paiements_verifies")
    date_verification = models.DateTimeField(null=True, blank=True)

    MODES = [
        ("ESPECES", "Espèces"),
        ("CARTE", "Carte bancaire"),
        ("MOBILE", "Mobile Money"),
    ]

    vente = models.ForeignKey(
        Vente,
        on_delete=models.PROTECT,
        related_name="paiements"
    )

    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"))
        ]
    )

    mode = models.CharField(
        max_length=20,
        choices=MODES
    )

    date_paiement = models.DateTimeField(
        auto_now_add=True
    )

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Paiement"
        permissions = [("confirmer_paiement", "Vérifier un paiement électronique")]
        constraints = [models.UniqueConstraint(
            fields=["mode", "reference_verification"], name="reference_electronique_confirmee_unique",
            condition=models.Q(statut="CONFIRME") & ~models.Q(reference_verification="") & ~models.Q(mode="ESPECES"),
        )]
        verbose_name_plural = "Paiements"
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"Paiement N°{self.pk}"



class RetourVente(models.Model):

    STATUTS = [
        ("BROUILLON", "Brouillon"),
        ("VALIDE", "Validé"),
        ("REFUSE", "Refusé"),
    ]

    vente = models.ForeignKey(
        Vente,
        on_delete=models.PROTECT,
        related_name="retours",
    )

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.PROTECT,
    )

    date_retour = models.DateTimeField(auto_now_add=True)

    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default="BROUILLON",
    )

    motif = models.TextField()

    class Meta:
        verbose_name = "Retour de vente"
        verbose_name_plural = "Retours de vente"
        ordering = ["-date_retour"]

    def __str__(self):
        return f"Retour N°{self.pk}"


class LigneRetour(models.Model):
    lot_origine = models.ForeignKey("stock.LotStock", on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="retours_declares", verbose_name="Lot retourné")

    retour = models.ForeignKey(
        RetourVente,
        on_delete=models.CASCADE,
        related_name="lignes",
    )

    ligne_vente = models.ForeignKey(
        LigneVente,
        on_delete=models.PROTECT,
        related_name="lignes_retour",
    )

    quantite = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Ligne de retour"
        verbose_name_plural = "Lignes de retour"

    def __str__(self):
        return (
            f"{self.ligne_vente.medicament} "
            f"- {self.quantite}"
        )

class LigneVenteLot(models.Model):
    ligne_vente = models.ForeignKey(
        LigneVente,
        on_delete=models.PROTECT,
        related_name="lots_utilises",
    )

    lot = models.ForeignKey(
        "stock.LotStock",
        on_delete=models.PROTECT,
        related_name="lignes_vente",
    )

    quantite = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Lot utilisé dans une vente"
        verbose_name_plural = "Lots utilisés dans les ventes"

    def __str__(self):
        return (
            f"Vente {self.ligne_vente.vente_id} - "
            f"Lot {self.lot.numero_lot} - "
            f"Quantité {self.quantite}"
        )


class Remboursement(models.Model):
    cle_operation = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    retour = models.ForeignKey(RetourVente, on_delete=models.PROTECT, related_name="remboursements")
    montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    utilisateur = models.ForeignKey("utilisateurs.Utilisateur", on_delete=models.PROTECT)
    motif = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Remboursement"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Remboursement N°{self.pk}"


class EvenementAudit(models.Model):
    acteur = models.ForeignKey("utilisateurs.Utilisateur", on_delete=models.PROTECT)
    action = models.CharField(max_length=60)
    objet = models.CharField(max_length=150)
    motif = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)


class DecisionQuarantaine(models.Model):
    ligne_retour = models.OneToOneField(LigneRetour, on_delete=models.PROTECT, related_name="decision")
    decision = models.CharField(max_length=20, choices=[("DESTRUCTION", "À détruire"), ("CONSERVER", "Conserver hors vente"), ("REINTEGRER", "Remise en stock autorisée")])
    lot = models.ForeignKey("stock.LotStock", on_delete=models.PROTECT, null=True, blank=True)
    motif = models.TextField()
    utilisateur = models.ForeignKey("utilisateurs.Utilisateur", on_delete=models.PROTECT)
    date_creation = models.DateTimeField(auto_now_add=True)
