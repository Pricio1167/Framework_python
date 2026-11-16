from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    telephone = models.CharField(
        max_length=20,
        blank=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.username