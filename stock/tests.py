
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from stock.services import (
    stock_disponible,
    medicaments_stock_faible,
    lots_proches_peremption,
    lots_perimes,
    lots_fefo,
)


class StockTests(TestCase):

    def setUp(self):
        self.categorie = Categorie.objects.create(
            nom="Categorie Test Stock"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Medicament Test",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            seuil_alerte=10,
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

    def test_stock_disponible(self):
        self.creer_lot("LOT-A", 60, 20)
        self.creer_lot("LOT-B", -1, 15)
        self.creer_lot("LOT-C", 90, 10, bloque=True)

        self.assertEqual(
            stock_disponible(self.medicament),
            20
        )

    def test_stock_faible(self):
        self.creer_lot("LOT-A", 60, 5)

        alertes = medicaments_stock_faible()

        self.assertEqual(len(alertes), 1)
        self.assertEqual(alertes[0]["quantite"], 5)

    def test_lots_proches_peremption(self):
        self.creer_lot("LOT-A", 10, 20)
        self.creer_lot("LOT-B", 60, 10)

        lots = lots_proches_peremption(jours=30)

        self.assertEqual(lots.count(), 1)
        self.assertEqual(lots.first().numero_lot, "LOT-A")

    def test_lots_perimes(self):
        self.creer_lot("LOT-A", -2, 10)
        self.creer_lot("LOT-B", 60, 20)

        lots = lots_perimes()

        self.assertEqual(lots.count(), 1)
        self.assertEqual(lots.first().numero_lot, "LOT-A")

    def test_ordre_fefo(self):
        self.creer_lot("LOT-A", 90, 10)
        self.creer_lot("LOT-B", 20, 10)
        self.creer_lot("LOT-C", 60, 10)

        lots = list(lots_fefo(self.medicament))

        self.assertEqual(
            [lot.numero_lot for lot in lots],
            ["LOT-B", "LOT-C", "LOT-A"]
        )
