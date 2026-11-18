from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from stock.operations import inventorier
from utilisateurs.roles import configurer_roles
from ventes.models import Vente, LigneVente, RetourVente, LigneRetour
from ventes.operations import confirmer_vente, confirmer_retour, payer, rembourser, solde


class GestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("responsable", password="test-password")
        cls.employe = get_user_model().objects.create_user("employe")
        categorie = Categorie.objects.create(nom="Antalgiques")
        cls.medicament = Medicament.objects.create(
            nom_commercial="Produit", categorie=categorie, forme="comprime", dosage="500 mg",
            prix_achat=100, prix_vente=150,
        )
        cls.lot = LotStock.objects.create(medicament=cls.medicament, numero_lot="L1", quantite=20,
                                         date_peremption=timezone.localdate()+timedelta(days=90))
        cls.vente = Vente.objects.create(utilisateur=cls.admin)
        cls.ligne = LigneVente.objects.create(vente=cls.vente, medicament=cls.medicament,
                                              quantite=4, prix_unitaire=150)

    def connecter(self):
        self.client.force_login(self.admin)

    def retour(self):
        confirmer_vente(self.vente.pk, self.admin)
        retour = RetourVente.objects.create(vente=self.vente, utilisateur=self.admin, motif="Emballage altéré")
        LigneRetour.objects.create(retour=retour, ligne_vente=self.ligne, quantite=2)
        confirmer_retour(retour.pk, self.admin)
        return retour

    def test_roles_idempotents_et_droits_personnalises(self):
        configurer_roles()
        groupe = Group.objects.get(name="Caissier")
        personnalisee = Permission.objects.get(content_type__app_label="fournisseurs", codename="view_fournisseur")
        groupe.permissions.add(personnalisee)
        nombre = groupe.permissions.count()
        call_command("configurer_roles", verbosity=0)
        self.assertEqual(groupe.permissions.count(), nombre)
        self.assertTrue(groupe.permissions.filter(pk=personnalisee.pk).exists())

    def test_dashboard_anonyme(self):
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_dashboard_sans_droits(self):
        self.client.force_login(self.employe)
        reponse = self.client.get("/")
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, "Chiffre d’affaires du jour")

    def test_acces_direct_interdit(self):
        self.client.force_login(self.employe)
        self.assertEqual(self.client.get("/gestion/medicaments/").status_code, 403)
        self.assertEqual(self.client.post(f"/ventes/{self.vente.pk}/valider/").status_code, 403)

    def test_service_refuse_sans_permission(self):
        with self.assertRaises(PermissionDenied):
            confirmer_vente(self.vente.pk, self.employe)
        with self.assertRaises(PermissionDenied):
            inventorier(self.lot.pk, 10, "Comptage", self.employe)

    def test_ecrans_administrateur(self):
        from dashboard.catalogue import ECRANS
        self.connecter()
        for slug, (_, _, champs) in ECRANS.items():
            with self.subTest(slug=slug):
                self.assertEqual(self.client.get(f"/gestion/{slug}/").status_code, 200)
                if champs:
                    self.assertEqual(self.client.get(f"/gestion/{slug}/ajouter/").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get(f"/ventes/{self.vente.pk}/").status_code, 200)

    def test_creation_client(self):
        self.connecter()
        reponse = self.client.post("/gestion/clients/ajouter/", {"nom": "Client test", "actif": "on"})
        self.assertEqual(reponse.status_code, 302)
        from clients.models import Client
        self.assertTrue(Client.objects.filter(nom="Client test").exists())

    def test_ligne_confirmee_non_modifiable(self):
        confirmer_vente(self.vente.pk, self.admin)
        self.connecter()
        reponse = self.client.post(f"/gestion/lignes-ventes/{self.ligne.pk}/modifier/", {
            "vente": self.vente.pk, "medicament": self.medicament.pk, "quantite": 1,
        })
        self.assertEqual(reponse.status_code, 200)
        self.ligne.refresh_from_db()
        self.assertEqual(self.ligne.quantite, 4)

    def test_validation_get_refuse(self):
        self.connecter()
        self.assertEqual(self.client.get(f"/ventes/{self.vente.pk}/valider/").status_code, 405)

    def test_paiement_partiel_solde(self):
        confirmer_vente(self.vente.pk, self.admin)
        payer(self.vente.pk, "200", "ESPECES", self.admin)
        self.assertEqual(solde(self.vente)["reste"], Decimal("400"))

    def test_retour_quarantaine(self):
        self.retour()
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 16)

    def test_remboursement_plafonne(self):
        retour = self.retour()
        payer(self.vente.pk, "300", "ESPECES", self.admin)
        with self.assertRaises(ValidationError):
            rembourser(retour.pk, "1", "Demande", self.admin)

    def test_remboursements_partiels_et_double(self):
        confirmer_vente(self.vente.pk, self.admin)
        payer(self.vente.pk, "600", "ESPECES", self.admin)
        retour = RetourVente.objects.create(vente=self.vente, utilisateur=self.admin, motif="Retour")
        LigneRetour.objects.create(retour=retour, ligne_vente=self.ligne, quantite=2)
        confirmer_retour(retour.pk, self.admin)
        rembourser(retour.pk, "100", "Partiel", self.admin)
        rembourser(retour.pk, "200", "Solde", self.admin)
        with self.assertRaises(ValidationError):
            rembourser(retour.pk, "1", "Doublon", self.admin)

    def test_paiement_apres_retour_ne_depasse_pas_net(self):
        self.retour()
        with self.assertRaises(ValidationError):
            payer(self.vente.pk, "301", "ESPECES", self.admin)

    def test_inventaire_trace(self):
        lot = inventorier(self.lot.pk, "17", "Comptage physique", self.admin)
        self.assertEqual(lot.quantite, 17)
        mouvement = lot.mouvements.get()
        self.assertEqual(mouvement.quantite, 3)
        self.assertIn("20 → 17", mouvement.motif)

    def test_inventaire_sans_motif_refuse(self):
        with self.assertRaises(ValidationError):
            inventorier(self.lot.pk, 17, "", self.admin)

    def test_facture_et_recu_pdf(self):
        confirmer_vente(self.vente.pk, self.admin)
        paiement = payer(self.vente.pk, "100", "ESPECES", self.admin)
        self.connecter()
        for url in (reverse("vente_document", args=[self.vente.pk, "facture"]),
                    reverse("paiement_document", args=[paiement.pk])):
            reponse = self.client.get(url)
            self.assertEqual(reponse.status_code, 200)
            self.assertTrue(b"".join(reponse.streaming_content).startswith(b"%PDF-"))
            reponse.close()

    def test_csrf_requis(self):
        from django.test import Client
        navigateur = Client(enforce_csrf_checks=True)
        navigateur.force_login(self.admin)
        self.assertEqual(navigateur.post(f"/ventes/{self.vente.pk}/valider/").status_code, 403)

    def test_decision_quarantaine_unique(self):
        from ventes.operations import decider_quarantaine
        retour = self.retour()
        ligne = retour.lignes.get()
        decider_quarantaine(ligne.pk, "CONSERVER", "Contrôle nécessaire", self.admin)
        with self.assertRaises(ValidationError):
            decider_quarantaine(ligne.pk, "DESTRUCTION", "Deuxième décision", self.admin)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 16)

    def test_reintegration_desactivee_par_defaut(self):
        from ventes.operations import decider_quarantaine
        retour = self.retour()
        with self.assertRaises(ValidationError):
            decider_quarantaine(retour.lignes.get().pk, "REINTEGRER", "Contrôle", self.admin, self.lot.pk)

    def test_reintegration_explicite(self):
        from ventes.operations import decider_quarantaine
        retour = self.retour()
        with self.settings(AUTORISER_REMISE_STOCK_RETOURS=True):
            decider_quarantaine(retour.lignes.get().pk, "REINTEGRER", "Politique autorisée et contrôle effectué", self.admin, self.lot.pk)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 18)

    def test_refus_trace(self):
        from ventes.operations import refuser_retour
        from ventes.models import EvenementAudit
        retour = RetourVente.objects.create(vente=self.vente, utilisateur=self.admin, motif="Demande")
        refuser_retour(retour.pk, "Demande non admissible", self.admin)
        retour.refresh_from_db()
        self.assertEqual(retour.statut, "REFUSE")
        self.assertTrue(EvenementAudit.objects.filter(action="refus_retour", acteur=self.admin).exists())

    def test_pdfs_retour_remboursement(self):
        confirmer_vente(self.vente.pk, self.admin)
        payer(self.vente.pk, "600", "ESPECES", self.admin)
        retour = RetourVente.objects.create(vente=self.vente, utilisateur=self.admin, motif="Retour")
        LigneRetour.objects.create(retour=retour, ligne_vente=self.ligne, quantite=2)
        confirmer_retour(retour.pk, self.admin)
        remboursement = rembourser(retour.pk, "300", "Solde retour", self.admin)
        self.connecter()
        self.assertEqual(self.client.get(f"/ventes/{self.vente.pk}/").status_code, 200)
        for nom, pk in (("retour_document", retour.pk), ("remboursement_document", remboursement.pk)):
            reponse = self.client.get(reverse(nom, args=[pk]))
            self.assertEqual(reponse.status_code, 200)
            self.assertTrue(b"".join(reponse.streaming_content).startswith(b"%PDF-"))
            reponse.close()

    def test_caissier_ne_valide_pas_ni_rembourse(self):
        configurer_roles()
        self.employe.groups.add(Group.objects.get(name="Caissier"))
        self.assertTrue(self.employe.has_perm("ventes.add_paiement"))
        self.assertFalse(self.employe.has_perm("ventes.change_vente"))
        self.assertFalse(self.employe.has_perm("ventes.add_remboursement"))

    def test_administration_interdit_suppression_operations(self):
        from django.contrib import admin
        from django.test import RequestFactory
        from achats.models import CommandeAchat, ReceptionAchat
        requete = RequestFactory().get("/admin/")
        requete.user = self.admin
        for model in (Vente, RetourVente, CommandeAchat, ReceptionAchat):
            self.assertFalse(admin.site._registry[model].has_delete_permission(requete))

    def test_facture_conserve_identite_produit(self):
        confirmer_vente(self.vente.pk, self.admin)
        self.medicament.nom_commercial = "Nouveau nom"
        self.medicament.save()
        self.vente.refresh_from_db()
        self.assertIn("Produit", self.vente.instantane_facture["lignes"][0]["medicament"])
        self.assertNotIn("Nouveau nom", self.vente.instantane_facture["lignes"][0]["medicament"])

    def test_pages_utilisateurs_et_parametres(self):
        self.connecter()
        for url in ("/utilisateurs/", "/utilisateurs/creer/", f"/utilisateurs/{self.employe.pk}/", "/parametres/"):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_parametres_enregistres_et_utilises(self):
        self.connecter()
        self.assertEqual(self.client.post("/parametres/", {"nom": "Pharmacie test", "adresse": "Adresse réelle", "mentions": ""}).status_code, 302)
        confirmer_vente(self.vente.pk, self.admin)
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.instantane_facture["pharmacie"], "Pharmacie test")

    def test_utilisateurs_parametres_interdits(self):
        self.client.force_login(self.employe)
        for url in ("/utilisateurs/", "/utilisateurs/creer/", "/parametres/"):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_attribution_role_sans_privileges_systeme(self):
        configurer_roles()
        groupe = Group.objects.get(name="Caissier")
        self.connecter()
        reponse = self.client.post(f"/utilisateurs/{self.employe.pk}/", {
            "first_name": "Employé", "is_active": "on", "groups": [groupe.pk],
            "is_superuser": "on", "is_staff": "on",
        })
        self.assertEqual(reponse.status_code, 302)
        self.employe.refresh_from_db()
        self.assertFalse(self.employe.is_superuser)
        self.assertFalse(self.employe.is_staff)
        self.assertTrue(self.employe.groups.filter(pk=groupe.pk).exists())

    def test_identifiant_retour_invalide_ne_provoque_pas_erreur_serveur(self):
        self.connecter()
        reponse = self.client.post(f"/ventes/{self.vente.pk}/retour/", {"retour": "invalide"})
        self.assertEqual(reponse.status_code, 302)
