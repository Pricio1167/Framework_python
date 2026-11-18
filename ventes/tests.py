
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
from ventes.paiements import enregistrer_paiement
from ventes.models import Paiement
from ventes.models import RetourVente, LigneRetour
from ventes.retours import valider_retour
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock
from ventes.models import Vente, LigneVente, LigneVenteLot
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

class PaiementTests(TestCase):


    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="test_paiement",
            password="TestPassword123!"
        )

        self.categorie = Categorie.objects.create(
            nom="Categorie Paiement Test"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Medicament Paiement Test",
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

        LotStock.objects.create(
            medicament=self.medicament,
            numero_lot="LOT-PAIEMENT",
            date_peremption=timezone.localdate()
            + timedelta(days=90),
            quantite=20,
            quantite_recue=20,
        )

        LigneVente.objects.create(
            vente=self.vente,
            medicament=self.medicament,
            quantite=2,
            prix_unitaire=Decimal("150.00"),
        )

        valider_vente(self.vente.pk)
        self.vente.refresh_from_db()


    def test_paiement_complet(self):
        paiement = enregistrer_paiement(
            self.vente.pk,
            Decimal("300.00"),
            "ESPECES",
            self.utilisateur,
        )

        self.assertEqual(paiement.montant, Decimal("300.00"))
        self.assertEqual(Paiement.objects.count(), 1)

    def test_paiement_partiel(self):
        enregistrer_paiement(
            self.vente.pk, 100, "MOBILE", self.utilisateur
        )

        enregistrer_paiement(
            self.vente.pk, 200, "ESPECES", self.utilisateur
        )

        self.assertEqual(Paiement.objects.count(), 2)

    def test_paiement_superieur_refuse(self):
        with self.assertRaises(ValidationError):
            enregistrer_paiement(
                self.vente.pk, 400, "ESPECES", self.utilisateur
            )

        self.assertEqual(Paiement.objects.count(), 0)

    def test_montant_negatif_refuse(self):
        with self.assertRaises(ValidationError):
            enregistrer_paiement(
                self.vente.pk, -50, "ESPECES", self.utilisateur
            )

    def test_double_paiement_excessif_refuse(self):
        enregistrer_paiement(
            self.vente.pk, 250, "ESPECES", self.utilisateur
        )

        with self.assertRaises(ValidationError):
            enregistrer_paiement(
                self.vente.pk, 100, "MOBILE", self.utilisateur
            )

        self.assertEqual(Paiement.objects.count(), 1)

class RetourTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="test_retour",
            password="TestPassword123!"
        )

        self.categorie = Categorie.objects.create(
            nom="Categorie Retour Test"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Medicament Retour Test",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            seuil_alerte=10,
        )

        self.lot = LotStock.objects.create(
            medicament=self.medicament,
            numero_lot="LOT-RETOUR",
            date_peremption=timezone.localdate()
            + timedelta(days=90),
            quantite=20,
            quantite_recue=20,
        )

        self.vente = Vente.objects.create(
            utilisateur=self.utilisateur
        )

        self.ligne_vente = LigneVente.objects.create(
            vente=self.vente,
            medicament=self.medicament,
            quantite=10,
            prix_unitaire=Decimal("150.00"),
        )

        valider_vente(self.vente.pk)

        self.retour = RetourVente.objects.create(
            vente=self.vente,
            utilisateur=self.utilisateur,
            motif="Retour de test",
        )

    def ajouter_ligne_retour(self, quantite):
        return LigneRetour.objects.create(
            retour=self.retour,
            ligne_vente=self.ligne_vente,
            quantite=quantite,
        )

    def test_retour_valide(self):
        self.ajouter_ligne_retour(3)

        valider_retour(self.retour.pk)

        self.retour.refresh_from_db()
        self.assertEqual(self.retour.statut, "VALIDE")

    def test_retour_superieur_refuse(self):
        self.ajouter_ligne_retour(15)

        with self.assertRaises(ValidationError):
            valider_retour(self.retour.pk)

    def test_double_validation_refusee(self):
        self.ajouter_ligne_retour(2)
        valider_retour(self.retour.pk)

        with self.assertRaises(ValidationError):
            valider_retour(self.retour.pk)

    def test_retour_vide_refuse(self):
        with self.assertRaises(ValidationError):
            valider_retour(self.retour.pk)

    def test_retour_ne_modifie_pas_stock(self):
        self.ajouter_ligne_retour(4)

        self.lot.refresh_from_db()
        stock_avant = self.lot.quantite

        valider_retour(self.retour.pk)

        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, stock_avant)

    def test_retours_cumules_refuses(self):
        self.ajouter_ligne_retour(7)
        valider_retour(self.retour.pk)

        second_retour = RetourVente.objects.create(
            vente=self.vente,
            utilisateur=self.utilisateur,
            motif="Deuxieme retour",
        )

        LigneRetour.objects.create(
            retour=second_retour,
            ligne_vente=self.ligne_vente,
            quantite=4,
        )

        with self.assertRaises(ValidationError):
            valider_retour(second_retour.pk)
class RetourTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="test_retour",
            password="TestPassword123!"
        )

        self.categorie = Categorie.objects.create(
            nom="Categorie Retour Test"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Medicament Retour Test",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            seuil_alerte=10,
        )

        self.lot = LotStock.objects.create(
            medicament=self.medicament,
            numero_lot="LOT-RETOUR",
            date_peremption=timezone.localdate()
            + timedelta(days=90),
            quantite=20,
            quantite_recue=20,
        )

        self.vente = Vente.objects.create(
            utilisateur=self.utilisateur
        )

        self.ligne_vente = LigneVente.objects.create(
            vente=self.vente,
            medicament=self.medicament,
            quantite=10,
            prix_unitaire=Decimal("150.00"),
        )

        valider_vente(self.vente.pk)

        self.retour = RetourVente.objects.create(
            vente=self.vente,
            utilisateur=self.utilisateur,
            motif="Retour de test",
        )

    def ajouter_ligne_retour(self, quantite):
        return LigneRetour.objects.create(
            retour=self.retour,
            ligne_vente=self.ligne_vente,
            quantite=quantite,
        )

    def test_retour_valide(self):
        self.ajouter_ligne_retour(3)

        valider_retour(self.retour.pk)

        self.retour.refresh_from_db()

        self.assertEqual(self.retour.statut, "VALIDE")

    def test_retour_superieur_refuse(self):
        self.ajouter_ligne_retour(15)

        with self.assertRaises(ValidationError):
            valider_retour(self.retour.pk)

    def test_double_validation_refusee(self):
        self.ajouter_ligne_retour(2)

        valider_retour(self.retour.pk)

        with self.assertRaises(ValidationError):
            valider_retour(self.retour.pk)

    def test_retour_vide_refuse(self):
        with self.assertRaises(ValidationError):
            valider_retour(self.retour.pk)

    def test_retour_ne_modifie_pas_stock(self):
        self.ajouter_ligne_retour(4)

        self.lot.refresh_from_db()
        stock_avant = self.lot.quantite

        valider_retour(self.retour.pk)

        self.lot.refresh_from_db()

        self.assertEqual(
            self.lot.quantite,
            stock_avant,
        )

    def test_retours_cumules_refuses(self):
        self.ajouter_ligne_retour(7)
        valider_retour(self.retour.pk)

        second_retour = RetourVente.objects.create(
            vente=self.vente,
            utilisateur=self.utilisateur,
            motif="Deuxieme retour",
        )

        LigneRetour.objects.create(
            retour=second_retour,
            ligne_vente=self.ligne_vente,
            quantite=4,
        )

        with self.assertRaises(ValidationError):
            valider_retour(second_retour.pk)

class TracabiliteLotsTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="test_tracabilite",
            password="TestPassword123!"
        )

        self.categorie = Categorie.objects.create(
            nom="Categorie Tracabilite"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Paracetamol Tracabilite",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            seuil_alerte=10,
        )

        aujourd_hui = timezone.localdate()

        self.lot_a = LotStock.objects.create(
            medicament=self.medicament,
            numero_lot="TRACE-A",
            date_peremption=aujourd_hui + timedelta(days=30),
            quantite=5,
            quantite_recue=5,
        )

        self.lot_b = LotStock.objects.create(
            medicament=self.medicament,
            numero_lot="TRACE-B",
            date_peremption=aujourd_hui + timedelta(days=90),
            quantite=10,
            quantite_recue=10,
        )

        self.vente = Vente.objects.create(
            utilisateur=self.utilisateur
        )

        self.ligne = LigneVente.objects.create(
            vente=self.vente,
            medicament=self.medicament,
            quantite=8,
            prix_unitaire=Decimal("150.00"),
        )

    def test_repartition_sur_deux_lots(self):
        valider_vente(self.vente.pk)

        allocations = list(
            LigneVenteLot.objects.filter(
                ligne_vente=self.ligne
            ).order_by("lot__date_peremption")
        )

        self.assertEqual(len(allocations), 2)
        self.assertEqual(allocations[0].lot_id, self.lot_a.pk)
        self.assertEqual(allocations[0].quantite, 5)
        self.assertEqual(allocations[1].lot_id, self.lot_b.pk)
        self.assertEqual(allocations[1].quantite, 3)

    def test_stock_apres_repartition(self):
        valider_vente(self.vente.pk)

        self.lot_a.refresh_from_db()
        self.lot_b.refresh_from_db()

        self.assertEqual(self.lot_a.quantite, 0)
        self.assertEqual(self.lot_b.quantite, 7)

    def test_mouvements_correspondent_aux_lots(self):
        valider_vente(self.vente.pk)

        mouvements = MouvementStock.objects.filter(
            type_mouvement="SORTIE",
            lot__in=[self.lot_a, self.lot_b],
        )

        self.assertEqual(mouvements.count(), 2)

        quantites = {
            mouvement.lot_id: mouvement.quantite
            for mouvement in mouvements
        }

        self.assertEqual(quantites[self.lot_a.pk], 5)
        self.assertEqual(quantites[self.lot_b.pk], 3)

    def test_validation_repetee_sans_double_prelevement(self):
        valider_vente(self.vente.pk)

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            valider_vente(self.vente.pk)

        self.assertEqual(
            LigneVenteLot.objects.filter(
                ligne_vente=self.ligne
            ).count(),
            2,
        )

        self.lot_a.refresh_from_db()
        self.lot_b.refresh_from_db()

        self.assertEqual(self.lot_a.quantite, 0)
        self.assertEqual(self.lot_b.quantite, 7)
