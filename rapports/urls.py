
from django.urls import path
from . import views

from .views import (
    telecharger_rapport_ventes,
    telecharger_rapport_stock,
)

urlpatterns = [
    path("achats/pdf/", views.telecharger_achats, name="rapport_achats_pdf"),
    path("peremptions/pdf/", views.telecharger_peremptions, name="rapport_peremptions_pdf"),
    path("", views.accueil, name="rapports_accueil"),
    path(
        "ventes/pdf/",
        telecharger_rapport_ventes,
        name="rapport_ventes_pdf",
    ),
    path(
        "stocks/pdf/",
        telecharger_rapport_stock,
        name="rapport_stocks_pdf",
    ),
]
