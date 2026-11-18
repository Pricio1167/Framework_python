
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from dashboard import gestion
from ventes import views as ventes_views
from ventes import documents
from dashboard import parametres
from dashboard import parcours
from dashboard import fiches
from achats import documents as achats_documents
from utilisateurs import views as utilisateurs_views
from utilisateurs import auth_views as comptes_views


urlpatterns = [
    path("documents/achats/<int:pk>/", achats_documents.bon_commande, name="bon_commande_pdf"),
    path("documents/receptions/<int:pk>/", achats_documents.bon_reception, name="bon_reception_pdf"),
    path("fiches/<slug:slug>/<int:pk>/", fiches.detail, name="fiche_detail"),
    path("fiches/<slug:slug>/<int:pk>/action/", fiches.action, name="fiche_action"),
    path("compte/mot-de-passe/", comptes_views.PasswordChangeView.as_view(template_name="registration/password_form.html", success_url="/compte/mot-de-passe/modifie/"), name="password_change"),
    path("compte/mot-de-passe/modifie/", auth_views.PasswordChangeDoneView.as_view(template_name="registration/password_done.html"), name="password_change_done"),
    path("compte/reinitialiser/", comptes_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html", email_template_name="registration/password_reset_email.txt", subject_template_name="registration/password_reset_subject.txt"), name="password_reset"),
    path("compte/reinitialiser/envoye/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("compte/reinitialiser/<uidb64>/<token>/", comptes_views.PasswordResetConfirmView.as_view(template_name="registration/password_form.html"), name="password_reset_confirm"),
    path("compte/reinitialiser/termine/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_done.html"), name="password_reset_complete"),
    path("ventes/<int:pk>/lignes/<int:ligne_id>/supprimer/", ventes_views.ligne_supprimer, name="vente_ligne_supprimer"),
    path("gestion/<slug:slug>/<int:pk>/", parcours.detail, name="gestion_detail"),
    path("ventes/nouvelle/", ventes_views.creer, name="vente_creation"),
    path("ventes/<int:pk>/lignes/ajouter/", ventes_views.ligne_ajouter, name="vente_ligne_ajouter"),
    path("ventes/<int:pk>/retours/demander/", ventes_views.demander_retour, name="vente_demander_retour"),
    path("parametres/", parametres.modifier, name="parametres_pharmacie"),
    path("utilisateurs/", utilisateurs_views.liste, name="utilisateurs_liste"),
    path("utilisateurs/creer/", utilisateurs_views.modifier, name="utilisateur_creation"),
    path("utilisateurs/<int:pk>/", utilisateurs_views.modifier, name="utilisateur_modification"),
    path("documents/retours/<int:pk>/", documents.justificatif_retour, name="retour_document"),
    path("documents/remboursements/<int:pk>/", documents.justificatif_remboursement, name="remboursement_document"),
    path("gestion/<slug:slug>/<int:pk>/operation/", gestion.operation, name="gestion_operation"),
    path("gestion/<slug:slug>/<int:pk>/supprimer/", gestion.supprimer_ligne, name="gestion_suppression"),
    path("documents/ventes/<int:pk>/<slug:type_document>/", documents.facture, name="vente_document"),
    path("documents/paiements/<int:pk>/", documents.recu, name="paiement_document"),
    path("ventes/<int:pk>/", ventes_views.detail, name="vente_detail"),
    path("ventes/<int:pk>/<slug:operation>/", ventes_views.action, name="vente_action"),
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("gestion/<slug:slug>/", gestion.liste, name="gestion_liste"),
    path("gestion/<slug:slug>/ajouter/", gestion.formulaire, name="gestion_ajout"),
    path("gestion/<slug:slug>/<int:pk>/modifier/", gestion.formulaire, name="gestion_modification"),
    # Administration Django
    path("admin/", admin.site.urls),

    # Rapports PHARMAGEST
    path("rapports/", include("rapports.urls")),

    # Tableau de bord et accueil
    path("", include("dashboard.urls")),
]


# Fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
