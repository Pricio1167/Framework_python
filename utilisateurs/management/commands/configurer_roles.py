from django.core.management.base import BaseCommand

from utilisateurs.roles import configurer_roles


class Command(BaseCommand):
    help = "Crée les rôles PHARMAGEST et ajoute leurs droits sans retirer les droits personnalisés."

    def handle(self, *args, **options):
        for groupe in configurer_roles():
            self.stdout.write(self.style.SUCCESS(f"Rôle configuré : {groupe.name}"))
