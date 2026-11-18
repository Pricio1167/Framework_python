from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from .models import Vente, LigneVente, RetourVente, LigneRetour, Paiement
from .operations import confirmer_vente, confirmer_retour, payer, verifier_paiement


@skipUnlessDBFeature("has_select_for_update")
class ConcurrencePostgreSQLTests(TransactionTestCase):
    def setUp(self):
        self.acteur = get_user_model().objects.create_superuser("concurrence")
        categorie = Categorie.objects.create(nom="Concurrence")
        self.medicament = Medicament.objects.create(
            nom_commercial="Produit concurrence", categorie=categorie, forme="comprime",
            dosage="1 mg", prix_achat=10, prix_vente=20,
        )
        self.lot = LotStock.objects.create(
            medicament=self.medicament, numero_lot="CONCURRENT", quantite=10,
            date_peremption=timezone.localdate() + timedelta(days=90),
        )

    def vente(self, quantite):
        vente = Vente.objects.create(utilisateur=self.acteur)
        LigneVente.objects.create(vente=vente, medicament=self.medicament,
                                 quantite=quantite, prix_unitaire=20)
        return vente

    def parallele(self, operations):
        barriere = Barrier(len(operations))

        def executer(operation):
            close_old_connections()
            try:
                acteur = get_user_model().objects.get(pk=self.acteur.pk)
                barriere.wait(timeout=15)
                try:
                    operation(acteur)
                    return "OK"
                except ValidationError:
                    return "REFUS"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(executer, operations))

    def test_deux_ventes_ne_survendent_pas(self):
        ventes = [self.vente(7), self.vente(7)]
        resultat = self.parallele([lambda acteur, pk=v.pk: confirmer_vente(pk, acteur) for v in ventes])
        self.assertCountEqual(resultat, ["OK", "REFUS"])
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 3)

    def test_double_validation_concurrente(self):
        vente = self.vente(4)
        resultat = self.parallele([lambda acteur: confirmer_vente(vente.pk, acteur)] * 2)
        self.assertCountEqual(resultat, ["OK", "REFUS"])
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 6)

    def test_paiements_concurrents_plafonnes(self):
        vente = self.vente(4)
        confirmer_vente(vente.pk, self.acteur)
        resultat = self.parallele([lambda acteur: payer(vente.pk, "60", "ESPECES", acteur)] * 2)
        self.assertCountEqual(resultat, ["OK", "REFUS"])
        self.assertEqual(Paiement.objects.filter(vente=vente).count(), 1)

    def test_meme_paiement_concurrent_idempotent(self):
        vente = self.vente(4)
        confirmer_vente(vente.pk, self.acteur)
        cle = uuid4()
        resultat = self.parallele([
            lambda acteur: payer(vente.pk, "30", "ESPECES", acteur, cle_operation=cle),
        ] * 2)
        self.assertEqual(resultat, ["OK", "OK"])
        self.assertEqual(Paiement.objects.filter(vente=vente).count(), 1)

    def test_reference_electronique_concurrente_unique(self):
        paiements = []
        for _ in range(2):
            vente = self.vente(2)
            confirmer_vente(vente.pk, self.acteur)
            paiements.append(payer(vente.pk, "30", "MOBILE", self.acteur))
        resultat = self.parallele([
            lambda acteur, pk=p.pk: verifier_paiement(pk, acteur, "REFERENCE-CONCURRENTE") for p in paiements
        ])
        self.assertCountEqual(resultat, ["OK", "REFUS"])
        self.assertEqual(Paiement.objects.filter(statut="CONFIRME").count(), 1)

    def test_receptions_concurrentes_sur_meme_lot(self):
        from achats.models import CommandeAchat, LigneAchat, ReceptionAchat, LigneReception
        from achats.services import valider_reception
        from fournisseurs.models import Fournisseur
        fournisseur = Fournisseur.objects.create(nom="Fournisseur concurrence")
        receptions = []
        for _ in range(2):
            commande = CommandeAchat.objects.create(fournisseur=fournisseur, utilisateur=self.acteur, statut="COMMANDEE")
            ligne = LigneAchat.objects.create(commande=commande, medicament=self.medicament, quantite=3, prix_unitaire=10)
            reception = ReceptionAchat.objects.create(commande=commande, utilisateur=self.acteur)
            LigneReception.objects.create(reception=reception, ligne_achat=ligne, numero_lot=self.lot.numero_lot,
                date_peremption=self.lot.date_peremption, quantite_recue=3)
            receptions.append(reception)
        resultat = self.parallele([lambda acteur, pk=r.pk: valider_reception(pk) for r in receptions])
        self.assertEqual(resultat, ["OK", "OK"])
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 16)

    def test_retours_concurrents_plafonnes(self):
        vente = self.vente(4)
        confirmer_vente(vente.pk, self.acteur)
        retours = []
        for _ in range(2):
            retour = RetourVente.objects.create(vente=vente, utilisateur=self.acteur, motif="Demande concurrente")
            LigneRetour.objects.create(retour=retour, ligne_vente=vente.lignes.get(), quantite=3)
            retours.append(retour)
        resultat = self.parallele([lambda acteur, pk=r.pk: confirmer_retour(pk, acteur) for r in retours])
        self.assertCountEqual(resultat, ["OK", "REFUS"])
