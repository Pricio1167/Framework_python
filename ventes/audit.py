import logging


def journaliser(acteur, action, objet, motif):
    from .models import EvenementAudit
    EvenementAudit.objects.create(acteur=acteur, action=action,
                                 objet=f"{objet._meta.label}:{objet.pk}", motif=motif)
    logging.getLogger("pharmagest.audit").warning(
        "acteur=%s action=%s objet=%s:%s motif=%s",
        acteur.pk, action, objet._meta.label, objet.pk, motif,
    )
