from django.db import models

class Fournisseur(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    numero_fiscal = models.CharField(max_length=100, blank=True)
    contact_principal = models.CharField(max_length=150, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ["nom"]

    def __str__(self):
        return self.nom
