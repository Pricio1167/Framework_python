
from django.db import models
from django.core.validators import MinValueValidator
from medicaments.models import Medicament


class LotStock(models.Model):

    medicament = models.ForeignKey(
        Medicament,
        on_delete=models.PROTECT,
        related_name="lots"
    )

    numero_lot = models.CharField(max_length=100)

    date_peremption = models.DateField()

    quantite = models.PositiveIntegerField(default=0)

    quantite_recue = models.PositiveIntegerField(default=0)

    bloque = models.BooleanField(default=False)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lot de stock"
        verbose_name_plural = "Lots de stock"
        constraints = [
            models.UniqueConstraint(
                fields=["medicament", "numero_lot"],
                name="unique_lot_par_medicament"
            )
        ]
        ordering = ["date_peremption"]

    def __str__(self):
        return f"{self.medicament.nom_commercial} - {self.numero_lot}"


class MouvementStock(models.Model):

    TYPES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
        ("CORRECTION", "Correction"),
        ("RETOUR", "Retour"),
    ]

    lot = models.ForeignKey(
        LotStock,
        on_delete=models.PROTECT,
        related_name="mouvements"
    )

    type_mouvement = models.CharField(
        max_length=20,
        choices=TYPES
    )

    quantite = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    motif = models.TextField(blank=True)

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.PROTECT
    )

    date_mouvement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_mouvement} - {self.lot}"
