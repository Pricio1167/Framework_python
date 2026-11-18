from pathlib import Path
import warnings

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def valider_photo(fichier):
    """Contrôle le contenu réel des nouveaux fichiers, sans toucher aux photos historiques."""
    if not fichier or getattr(fichier, "_committed", False):
        return
    if fichier.size > 5 * 1024 * 1024:
        raise ValidationError("La photo ne doit pas dépasser 5 Mo.")
    if Path(fichier.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError("Utilisez une image JPEG, PNG ou WebP.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            fichier.seek(0)
            with Image.open(fichier) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"} or image.width * image.height > 16_000_000:
                    raise ValidationError("Format ou dimensions d’image non autorisés (16 millions de pixels maximum).")
                correspondance = {"JPEG": {".jpg", ".jpeg"}, "PNG": {".png"}, "WEBP": {".webp"}}
                if Path(fichier.name).suffix.lower() not in correspondance[image.format]:
                    raise ValidationError("L’extension de la photo ne correspond pas à son format réel.")
                image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise ValidationError("Le fichier ne contient pas une image valide.")
    finally:
        fichier.seek(0)
