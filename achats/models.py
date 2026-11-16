
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


class CommandeAchat(models.Model):

    STATUTS = [
        ("BROUILLON", "Brouillon"),
        ("COMMANDEE", "Commandée"),
        ("PARTIELLE", "Partiellement réceptionnée"),
        ("RECUE", "Entièrement réceptionnée"),
        ("ANNULEE", "Annulée"),
    ]

    fournisseur = models.ForeignKey(
        "fournisseurs.Fournisseur",
        on_delete=models.PROTECT,
        related_name="commandes"
    )

    date_commande = models.DateTimeField(
        auto_now_add=True
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default="BROUILLON"
    )

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Commande d'achat"
        verbose_name_plural = "Commandes d'achat"
        ordering = ["-date_commande"]

    def __str__(self):
        return f"Commande N°{self.pk}"


class LigneAchat(models.Model):

    commande = models.ForeignKey(
        CommandeAchat,
        on_delete=models.CASCADE,
        related_name="lignes"
    )

    medicament = models.ForeignKey(
        "medicaments.Medicament",
        on_delete=models.PROTECT
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


class ReceptionAchat(models.Model):

    commande = models.ForeignKey(
        CommandeAchat,
        on_delete=models.PROTECT,
        related_name="receptions"
    )

    date_reception = models.DateTimeField(
        auto_now_add=True
    )

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.PROTECT
    )

    validee = models.BooleanField(
        default=False
    )

    class Meta:
        verbose_name = "Réception d'achat"
        verbose_name_plural = "Réceptions d'achat"
        ordering = ["-date_reception"]

    def __str__(self):
        return f"Réception N°{self.pk}"

class LigneReception(models.Model):
    reception = models.ForeignKey(
        ReceptionAchat,
        on_delete=models.PROTECT,
        related_name="lignes"
    )

    ligne_achat = models.ForeignKey(
        LigneAchat,
        on_delete=models.PROTECT,
        related_name="lignes_reception"
    )

    numero_lot = models.CharField(max_length=100)

    date_peremption = models.DateField()

    quantite_recue = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Ligne de réception"
        verbose_name_plural = "Lignes de réception"

    def __str__(self):
        return (
            f"{self.ligne_achat.medicament} "
            f"- {self.quantite_recue} unités"
        )
