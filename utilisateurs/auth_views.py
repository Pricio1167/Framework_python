import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import views
from ventes.audit import journaliser


class PasswordChangeView(views.PasswordChangeView):
    def form_valid(self, form):
        reponse = super().form_valid(form)
        journaliser(self.request.user, "modification_mot_de_passe", self.request.user,
                    "Mot de passe modifié par son titulaire")
        return reponse


class PasswordResetView(views.PasswordResetView):
    def form_valid(self, form):
        if settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend" and settings.EMAIL_HOST == "localhost":
            form.add_error(None, "L’envoi d’e-mail n’est pas configuré. Contactez le responsable pour la récupération de votre compte.")
            return self.form_invalid(form)
        try:
            return super().form_valid(form)
        except (SMTPException, OSError):
            logging.getLogger(__name__).error("Service de réinitialisation par e-mail indisponible")
            form.add_error(None, "Le service d’envoi est indisponible. Réessayez plus tard ou contactez le responsable.")
            return self.form_invalid(form)


class PasswordResetConfirmView(views.PasswordResetConfirmView):
    def form_valid(self, form):
        reponse = super().form_valid(form)
        journaliser(self.user, "reinitialisation_mot_de_passe", self.user,
                    "Mot de passe réinitialisé après validation d’un jeton Django")
        return reponse
