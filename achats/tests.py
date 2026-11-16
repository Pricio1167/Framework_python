
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock

from .models import (
    CommandeAchat,
    LigneAchat,
    ReceptionAchat,
    LigneReception,
)
from .services import valider_reception


class ReceptionAchatTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="pharmacien_test",
            password="TestPassword123!"
        )

        self.fournisseur = Fournisseur.objects.create(
            nom="Fournisseur Test"
        )

        self.categorie = Categorie.objects.create(
            nom="Antalgiques"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Paracetamol Test",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
        )

        self.commande = CommandeAchat.objects.create(
            fournisseur=self.fournisseur,
            utilisateur=self.utilisateur,
            statut="COMMANDEE"
        )

        self.ligne_achat = LigneAchat.objects.create(
            commande=self.commande,
            medicament=self.medicament,
            quantite=100,
            prix_unitaire=Decimal("100.00")
        )

    def creer_reception(self, quantite):
        reception = ReceptionAchat.objects.create(
            commande=self.commande,
            utilisateur=self.utilisateur
        )

        LigneReception.objects.create(
            reception=reception,
            ligne_achat=self.ligne_achat,
            numero_lot="LOT-TEST-001",
            date_peremption=(
                timezone.localdate() + timedelta(days=365)
            ),
            quantite_recue=quantite
        )

        return reception

    def test_commande_ne_modifie_pas_stock(self):
        self.assertEqual(LotStock.objects.count(), 0)
        self.assertEqual(MouvementStock.objects.count(), 0)

    def test_reception_augmente_stock(self):
        reception = self.creer_reception(100)

        valider_reception(reception.pk)

        lot = LotStock.objects.get(
            numero_lot="LOT-TEST-001"
        )

        self.assertEqual(lot.quantite, 100)
        self.assertEqual(lot.quantite_recue, 100)
        self.assertEqual(MouvementStock.objects.count(), 1)

        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, "RECUE")

    def test_reception_double_interdite(self):
        reception = self.creer_reception(100)

        valider_reception(reception.pk)

        with self.assertRaises(ValidationError):
            valider_reception(reception.pk)

        lot = LotStock.objects.get(
            numero_lot="LOT-TEST-001"
        )

        self.assertEqual(lot.quantite, 100)
        self.assertEqual(MouvementStock.objects.count(), 1)

    def test_reception_partielle(self):
        reception = self.creer_reception(40)

        valider_reception(reception.pk)

        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, "PARTIELLE")

        lot = LotStock.objects.get(
            numero_lot="LOT-TEST-001"
        )
        self.assertEqual(lot.quantite, 40)

    def test_quantite_superieure_refusee(self):
        reception = self.creer_reception(120)

        with self.assertRaises(ValidationError):
            valider_reception(reception.pk)

        self.assertEqual(LotStock.objects.count(), 0)
        self.assertEqual(MouvementStock.objects.count(), 0)
