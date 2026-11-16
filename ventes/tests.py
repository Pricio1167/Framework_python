
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock
from ventes.models import Vente, LigneVente
from ventes.services import valider_vente


class VenteTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="test_caissier",
            password="TestPassword123!"
        )

        self.categorie = Categorie.objects.create(
            nom="Categorie Vente Test"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Medicament Vente Test",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            seuil_alerte=10,
        )

        self.vente = Vente.objects.create(
            utilisateur=self.utilisateur
        )

    def creer_lot(self, numero, jours, quantite, bloque=False):
        return LotStock.objects.create(
            medicament=self.medicament,
            numero_lot=numero,
            date_peremption=(
                timezone.localdate() + timedelta(days=jours)
            ),
            quantite=quantite,
            quantite_recue=quantite,
            bloque=bloque,
        )

    def ajouter_ligne(self, quantite):
        return LigneVente.objects.create(
            vente=self.vente,
            medicament=self.medicament,
            quantite=quantite,
            prix_unitaire=Decimal("150.00"),
        )

    def test_validation_vente(self):
        lot = self.creer_lot("LOT-A", 90, 20)
        self.ajouter_ligne(5)

        valider_vente(self.vente.pk)

        lot.refresh_from_db()
        self.vente.refresh_from_db()

        self.assertEqual(lot.quantite, 15)
        self.assertEqual(self.vente.statut, "VALIDEE")
        self.assertEqual(
            MouvementStock.objects.filter(
                type_mouvement="SORTIE"
            ).count(),
            1
        )

    def test_stock_insuffisant(self):
        lot = self.creer_lot("LOT-A", 90, 3)
        self.ajouter_ligne(5)

        with self.assertRaises(ValidationError):
            valider_vente(self.vente.pk)

        lot.refresh_from_db()
        self.vente.refresh_from_db()

        self.assertEqual(lot.quantite, 3)
        self.assertEqual(self.vente.statut, "BROUILLON")
        self.assertFalse(
            MouvementStock.objects.filter(
                type_mouvement="SORTIE"
            ).exists()
        )

    def test_lot_perime_refuse(self):
        lot = self.creer_lot("LOT-A", -1, 20)
        self.ajouter_ligne(5)

        with self.assertRaises(ValidationError):
            valider_vente(self.vente.pk)

        lot.refresh_from_db()
        self.assertEqual(lot.quantite, 20)

    def test_lot_bloque_refuse(self):
        lot = self.creer_lot(
            "LOT-A", 90, 20, bloque=True
        )
        self.ajouter_ligne(5)

        with self.assertRaises(ValidationError):
            valider_vente(self.vente.pk)

        lot.refresh_from_db()
        self.assertEqual(lot.quantite, 20)

    def test_ordre_fefo(self):
        lot_tardif = self.creer_lot("LOT-A", 90, 10)
        lot_proche = self.creer_lot("LOT-B", 20, 10)

        self.ajouter_ligne(12)

        valider_vente(self.vente.pk)

        lot_tardif.refresh_from_db()
        lot_proche.refresh_from_db()

        self.assertEqual(lot_proche.quantite, 0)
        self.assertEqual(lot_tardif.quantite, 8)

    def test_double_validation_refusee(self):
        lot = self.creer_lot("LOT-A", 90, 20)
        self.ajouter_ligne(5)

        valider_vente(self.vente.pk)

        with self.assertRaises(ValidationError):
            valider_vente(self.vente.pk)

        lot.refresh_from_db()

        self.assertEqual(lot.quantite, 15)
        self.assertEqual(
            MouvementStock.objects.filter(
                type_mouvement="SORTIE"
            ).count(),
            1
        )
