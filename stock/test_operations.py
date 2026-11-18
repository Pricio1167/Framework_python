from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from .models import LotStock
from .operations import mouvement_manuel, inventorier


class MouvementsManuelsTests(TestCase):
    def setUp(self):
        self.acteur = get_user_model().objects.create_superuser("stock-manuel")
        categorie = Categorie.objects.create(nom="Stock manuel")
        medicament = Medicament.objects.create(nom_commercial="Produit", categorie=categorie,
            forme="comprime", dosage="1 mg", prix_achat=1, prix_vente=2)
        self.lot = LotStock.objects.create(medicament=medicament, numero_lot="MANUEL", quantite=5,
            date_peremption=timezone.localdate()+timedelta(days=90))

    def test_entree_sortie_tracees(self):
        mouvement_manuel(self.lot.pk, "ENTREE", 3, "Régularisation documentée", self.acteur)
        mouvement_manuel(self.lot.pk, "SORTIE", 2, "Casse", self.acteur)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 6)
        self.assertEqual(self.lot.mouvements.count(), 2)

    def test_quantites_invalides_et_sortie_excessive(self):
        for valeur in ("1.5", "NaN", "-1", "0", "6"):
            with self.subTest(valeur=valeur), self.assertRaises(ValidationError):
                mouvement_manuel(self.lot.pk, "SORTIE", valeur, "Contrôle", self.acteur)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 5)
        self.assertFalse(self.lot.mouvements.exists())

    def test_entree_lot_bloque_interdite(self):
        self.lot.bloque = True
        self.lot.save()
        with self.assertRaises(ValidationError):
            mouvement_manuel(self.lot.pk, "ENTREE", 1, "Contrôle", self.acteur)

    def test_permission_et_inventaire_fractionnaire(self):
        employe = get_user_model().objects.create_user("sans-droits-stock")
        with self.assertRaises(PermissionDenied):
            mouvement_manuel(self.lot.pk, "SORTIE", 1, "Contrôle", employe)
        with self.assertRaises(ValidationError):
            inventorier(self.lot.pk, "2.5", "Contrôle", self.acteur)
