"""Initialise uniquement le fichier .env absent, sans révéler de secrets."""
from pathlib import Path
import secrets

racine = Path(__file__).resolve().parent.parent
destination = racine / ".env"
if destination.exists():
    print("Configuration locale existante conservée.")
else:
    exemple = (racine / ".env.example").read_text(encoding="utf-8")
    exemple = exemple.replace("SECRET_KEY=\n", f"SECRET_KEY={secrets.token_urlsafe(60)}\n")
    with destination.open("x", encoding="utf-8") as fichier:
        fichier.write(exemple)
    print("Configuration locale créée avec une clé aléatoire stable ; aucun secret affiché.")
