from datetime import datetime
from pathlib import Path
import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sauvegarde SQLite cohérente, sans écrasement de sauvegarde existante."

    def add_arguments(self, parser):
        parser.add_argument("--destination", default="backups")

    def handle(self, *args, **options):
        base = settings.DATABASES["default"]
        if base["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("Utilisez pg_dump pour PostgreSQL.")
        source = Path(base["NAME"]).resolve()
        if not source.is_file():
            raise CommandError("Base SQLite introuvable.")
        destination = Path(options["destination"]).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        fichier = destination / f"pharmagest-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3"
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as origine:
            with sqlite3.connect(fichier) as copie:
                origine.backup(copie)
                if copie.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise CommandError("Échec de vérification de la sauvegarde.")
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde vérifiée : {fichier}"))
