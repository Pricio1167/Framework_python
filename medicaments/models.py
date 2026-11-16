
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Categorie(models.Model):
    nom = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(
        blank=True
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Medicament(models.Model):

    FORMES = [
        ("comprime", "Comprimé"),
        ("gelule", "Gélule"),
        ("sirop", "Sirop"),
        ("injectable", "Injectable"),
        ("pommade", "Pommade"),
        ("autre", "Autre"),
    ]

    nom_commercial = models.CharField(
        max_length=200
    )

    denomination_generique = models.CharField(
        max_length=200,
        blank=True
    )

    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name="medicaments"
    )

    forme = models.CharField(
        max_length=30,
        choices=FORMES
    )

    dosage = models.CharField(
        max_length=100
    )

    laboratoire = models.CharField(
        max_length=150,
        blank=True
    )

    code_barres = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    photo = models.ImageField(
        upload_to="medicaments/",
        blank=True,
        null=True
    )

    prix_achat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    prix_vente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    seuil_alerte = models.PositiveIntegerField(
        default=10
    )

    actif = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Médicament"
        verbose_name_plural = "Médicaments"
        ordering = ["nom_commercial"]

    def __str__(self):
        return f"{self.nom_commercial} - {self.dosage}"

    def save(self, *args, **kwargs):
        if not self.code_barres:
            self.code_barres = None

        self.full_clean()
        super().save(*args, **kwargs)
