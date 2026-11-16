
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
        verbose_name_plural = "Paiements"
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"Paiement N°{self.pk}"
