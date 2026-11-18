from django.db import models

class ParametresPharmacie(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.TextField(blank=True)
    mentions = models.TextField(blank=True)

    def __str__(self):
        return self.nom
