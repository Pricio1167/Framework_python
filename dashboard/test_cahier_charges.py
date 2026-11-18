from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import re
import tempfile
from unittest.mock import patch
from urllib.parse import urlsplit

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from achats.models import CommandeAchat, LigneAchat, ReceptionAchat, LigneReception
from achats.operations import commander, annuler_commande
from achats.services import valider_reception
from clients.models import Client
from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from utilisateurs.roles import configurer_roles
from ventes.models import Vente, RetourVente, LigneRetour, Paiement
from ventes.operations import ajouter_ligne, confirmer_vente, confirmer_retour, payer, verifier_paiement, rembourser, solde


class CahierChargesTests(TestCase):
    def setUp(self):
        self.acteur = get_user_model().objects.create_superuser("cahier", email="responsable@example.test", password="AncienMotDePasse!642")
        self.client.force_login(self.acteur)
        self.categorie = Categorie.objects.create(nom="Cahier des charges")
        self.medicament = Medicament.objects.create(nom_commercial="Médicament du cahier", categorie=self.categorie,
            forme="comprime", dosage="500 mg", code_barres="3612345678901", prix_achat=100, prix_vente=150)
        self.lot = LotStock.objects.create(medicament=self.medicament, numero_lot="CDC-1", quantite=20,
                                         date_peremption=timezone.localdate()+timedelta(days=90))
        self.fournisseur = Fournisseur.objects.create(nom="Fournisseur cahier")
        self.personne = Client.objects.create(nom="Client cahier")

    def vente(self, quantite=4):
        vente = Vente.objects.create(utilisateur=self.acteur, client=self.personne)
        ajouter_ligne(vente.pk, self.medicament, quantite, self.acteur)
        confirmer_vente(vente.pk, self.acteur)
        return vente

    def commande(self):
        commande = CommandeAchat.objects.create(fournisseur=self.fournisseur, utilisateur=self.acteur)
        LigneAchat.objects.create(commande=commande, medicament=self.medicament, quantite=20, prix_unitaire=100)
        commander(commande.pk, self.acteur)
        return commande

    def png(self, nom="photo.png"):
        flux = BytesIO()
        Image.new("RGB", (24, 24), "white").save(flux, "PNG")
        return SimpleUploadedFile(nom, flux.getvalue(), content_type="image/png")

    def test_photo_ajout_detail_et_filtre_categorie(self):
        dossier = tempfile.TemporaryDirectory(dir=Path(settings.BASE_DIR)/"tmp")
        self.addCleanup(dossier.cleanup)
        with self.settings(MEDIA_ROOT=dossier.name):
            reponse = self.client.post("/gestion/medicaments/ajouter/", {
                "nom_commercial": "Avec photo", "categorie": self.categorie.pk, "forme": "comprime", "dosage": "1 mg",
                "prix_achat": "100", "prix_vente": "150", "seuil_alerte": 10, "actif": "on", "photo": self.png(),
            })
            self.assertEqual(reponse.status_code, 302)
            medicament = Medicament.objects.get(nom_commercial="Avec photo")
            self.assertTrue(medicament.photo.storage.exists(medicament.photo.name))
            self.assertContains(self.client.get(reverse("fiche_detail", args=["medicaments", medicament.pk])), medicament.photo.url)
            self.assertContains(self.client.get("/gestion/medicaments/", {"categorie": self.categorie.pk}), "Avec photo")

    def test_photos_fausse_extension_taille(self):
        from medicaments.validators import valider_photo
        for fichier in (SimpleUploadedFile("fake.png", b"pas une image", content_type="image/png"),
                        self.png("incorrect.jpg"), SimpleUploadedFile("gros.png", self.png().read()+b"x"*(5*1024*1024))):
            with self.subTest(fichier=fichier.name), self.assertRaises(ValidationError):
                valider_photo(fichier)

    def test_archivage_et_suppression_protegee(self):
        vente = self.vente()
        self.client.post(reverse("fiche_action", args=["medicaments", self.medicament.pk]), {})
        self.medicament.refresh_from_db()
        self.assertFalse(self.medicament.actif)
        self.assertEqual(vente.lignes.count(), 1)
        self.client.post(reverse("fiche_action", args=["categories", self.categorie.pk]), {"action": "supprimer"})
        self.assertTrue(Categorie.objects.filter(pk=self.categorie.pk).exists())

    def test_historique_clients_et_fournisseurs(self):
        vente = self.vente()
        commande = self.commande()
        self.assertContains(self.client.get(reverse("fiche_detail", args=["clients", self.personne.pk])), str(vente))
        self.assertContains(self.client.get(reverse("fiche_detail", args=["fournisseurs", self.fournisseur.pk])), str(commande))

    def test_code_barres_unique(self):
        with self.assertRaises(ValidationError):
            Medicament.objects.create(nom_commercial="Doublon interdit", categorie=self.categorie, forme="comprime",
                dosage="1 mg", prix_achat=1, prix_vente=2, code_barres=self.medicament.code_barres)

    def test_prix_et_identite_historiques(self):
        vente = self.vente()
        commande = self.commande()
        self.medicament.prix_achat = 500
        self.medicament.prix_vente = 700
        self.medicament.nom_commercial = "Nouveau nom courant"
        self.medicament.save()
        self.assertEqual(vente.total, Decimal("600"))
        self.assertEqual(commande.total, Decimal("2000"))
        vente.refresh_from_db()
        commande.refresh_from_db()
        self.assertIn("Médicament du cahier", vente.instantane_facture["lignes"][0]["medicament"])
        self.assertEqual(commande.instantane_document["lignes"][0]["prix_unitaire"], "100.00")

    def test_responsable_gestion_consultation_seule(self):
        configurer_roles()
        compte = get_user_model().objects.create_user("responsable-gestion")
        compte.groups.add(Group.objects.get(name="Responsable de gestion"))
        self.assertTrue(compte.has_perm("achats.view_commandeachat"))
        self.assertTrue(compte.has_perm("ventes.view_vente"))
        self.assertFalse(compte.has_perm("ventes.change_vente"))
        self.client.force_login(compte)
        self.assertEqual(self.client.get("/rapports/").status_code, 200)
        self.assertEqual(self.client.get("/gestion/clients/").status_code, 403)

    def test_lot_choisi_reserve_avant_fefo(self):
        lot_proche = LotStock.objects.create(medicament=self.medicament, numero_lot="CDC-PROCHE", quantite=5,
                                             date_peremption=timezone.localdate()+timedelta(days=10))
        vente = Vente.objects.create(utilisateur=self.acteur)
        auto = ajouter_ligne(vente.pk, self.medicament, 4, self.acteur)
        choix = ajouter_ligne(vente.pk, self.medicament, 5, self.acteur, lot_demande=lot_proche)
        confirmer_vente(vente.pk, self.acteur)
        self.assertEqual(choix.lots_utilises.get().lot_id, lot_proche.pk)
        self.assertEqual(auto.lots_utilises.get().lot_id, self.lot.pk)

    def test_lot_bloque_non_propose_et_scan_code_barres(self):
        vente = Vente.objects.create(utilisateur=self.acteur)
        reponse = self.client.get(reverse("vente_detail", args=[vente.pk]), {"produit": self.medicament.code_barres})
        self.assertEqual(list(reponse.context["ligne_form"].fields["medicament"].queryset), [self.medicament])
        self.lot.bloque = True
        self.lot.save()
        reponse = self.client.get(reverse("vente_detail", args=[vente.pk]))
        self.assertFalse(reponse.context["ligne_form"].fields["medicament"].queryset.exists())

    def test_recette_vente_trois_unites(self):
        vente = self.vente(quantite=3)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 17)
        self.assertEqual(vente.lignes.get().lots_utilises.get().quantite, 3)
        with self.assertRaises(ValidationError):
            confirmer_vente(vente.pk, self.acteur)

    def test_prescription_exige_controle_professionnel(self):
        self.medicament.prescription_requise = True
        self.medicament.save()
        vente = Vente.objects.create(utilisateur=self.acteur)
        ajouter_ligne(vente.pk, self.medicament, 1, self.acteur)
        with self.assertRaises(ValidationError):
            confirmer_vente(vente.pk, self.acteur)
        confirmer_vente(vente.pk, self.acteur, controle="Contrôle professionnel CDC-01")
        vente.refresh_from_db()
        self.assertEqual(vente.controle_delivrance["acteur"], self.acteur.pk)

    def test_paiement_electronique_attend_verification(self):
        vente = self.vente()
        paiement = payer(vente.pk, "600", "MOBILE", self.acteur)
        self.assertEqual(paiement.statut, "EN_ATTENTE")
        self.assertEqual(solde(vente)["paye"], 0)
        self.assertEqual(solde(vente)["encaissable"], 0)
        self.assertEqual(self.client.get(reverse("paiement_document", args=[paiement.pk])).status_code, 404)
        verifier_paiement(paiement.pk, self.acteur, "OPERATEUR-CDC-001")
        self.assertEqual(solde(vente)["paye"], Decimal("600"))
        with self.assertRaises(ValidationError):
            verifier_paiement(paiement.pk, self.acteur, "OPERATEUR-CDC-001")

    def test_ref_paiement_non_reutilisable_et_permission(self):
        premier = payer(self.vente().pk, "100", "MOBILE", self.acteur)
        verifier_paiement(premier.pk, self.acteur, "REFERENCE-UNIQUE")
        second = payer(self.vente().pk, "100", "MOBILE", self.acteur)
        with self.assertRaises(ValidationError):
            verifier_paiement(second.pk, self.acteur, "REFERENCE-UNIQUE")
        employe = get_user_model().objects.create_user("pas-verificateur")
        with self.assertRaises(PermissionDenied):
            verifier_paiement(second.pk, employe, "AUTRE-REFERENCE")

    def test_retour_lot_non_delivre_refuse(self):
        vente = self.vente()
        autre = LotStock.objects.create(medicament=self.medicament, numero_lot="JAMAIS-DELIVRE", quantite=0,
                                        date_peremption=timezone.localdate()+timedelta(days=100))
        retour = RetourVente.objects.create(vente=vente, utilisateur=self.acteur, motif="Retour")
        LigneRetour.objects.create(retour=retour, ligne_vente=vente.lignes.get(), quantite=1, lot_origine=autre)
        with self.assertRaises(ValidationError):
            confirmer_retour(retour.pk, self.acteur)

    def test_paiement_en_attente_non_remboursable(self):
        vente = self.vente()
        payer(vente.pk, "600", "CARTE", self.acteur)
        retour = RetourVente.objects.create(vente=vente, utilisateur=self.acteur, motif="Retour")
        LigneRetour.objects.create(retour=retour, ligne_vente=vente.lignes.get(), quantite=4, lot_origine=self.lot)
        confirmer_retour(retour.pk, self.acteur)
        with self.assertRaises(ValidationError):
            rembourser(retour.pk, "1", "Demande", self.acteur)

    def test_confirmation_reelle_apres_retour(self):
        vente = self.vente()
        paiement = payer(vente.pk, "600", "MOBILE", self.acteur)
        retour = RetourVente.objects.create(vente=vente, utilisateur=self.acteur, motif="Retour avant rapprochement")
        LigneRetour.objects.create(retour=retour, ligne_vente=vente.lignes.get(), quantite=2, lot_origine=self.lot)
        confirmer_retour(retour.pk, self.acteur)
        verifier_paiement(paiement.pk, self.acteur, "REFERENCE-REGLEMENT-REEL")
        remboursement = rembourser(retour.pk, "300", "Trop-perçu vérifié après le retour", self.acteur)
        self.assertEqual(remboursement.montant, Decimal("300"))
        self.assertEqual(solde(vente)["reste"], 0)

    def test_bons_achats_reception_rapports(self):
        commande = self.commande()
        self.assertEqual(commande.total, Decimal("2000"))
        reception = ReceptionAchat.objects.create(commande=commande, utilisateur=self.acteur)
        LigneReception.objects.create(reception=reception, ligne_achat=commande.lignes.get(), numero_lot="RECU-CDC",
            date_peremption=timezone.localdate()+timedelta(days=300), quantite_recue=20)
        valider_reception(reception.pk)
        for nom, args in (("bon_commande_pdf", [commande.pk]), ("bon_reception_pdf", [reception.pk]),
                          ("rapport_achats_pdf", []), ("rapport_peremptions_pdf", [])):
            reponse = self.client.get(reverse(nom, args=args))
            self.assertEqual(reponse.status_code, 200)
            self.assertTrue(b"".join(reponse.streaming_content).startswith(b"%PDF-"))
            reponse.close()
        reception.refresh_from_db()
        self.assertEqual(reception.instantane_document["total"], "2000.00")
        with self.assertRaises(ValidationError):
            annuler_commande(commande.pk, self.acteur, "Trop tard")

    def test_annulation_commande_sans_stock(self):
        commande = self.commande()
        annuler_commande(commande.pk, self.acteur, "Commande devenue inutile")
        commande.refresh_from_db()
        self.assertEqual(commande.statut, "ANNULEE")
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite, 20)

    def test_changement_mot_de_passe(self):
        reponse = self.client.post(reverse("password_change"), {"old_password": "AncienMotDePasse!642",
            "new_password1": "NouveauMotDePasse!749", "new_password2": "NouveauMotDePasse!749"})
        self.assertEqual(reponse.status_code, 302)
        self.acteur.refresh_from_db()
        self.assertTrue(self.acteur.check_password("NouveauMotDePasse!749"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_reinitialisation_usage_unique_et_pas_enumeration(self):
        self.client.logout()
        reponse = self.client.post(reverse("password_reset"), {"email": self.acteur.email})
        self.assertEqual(reponse.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        lien = re.search(r"http://[^\s]+", mail.outbox[0].body).group(0)
        redirection = self.client.get(urlsplit(lien).path)
        self.assertEqual(redirection.status_code, 302)
        self.client.post(redirection.url, {"new_password1": "RecuperationSure!749", "new_password2": "RecuperationSure!749"})
        self.acteur.refresh_from_db()
        self.assertTrue(self.acteur.check_password("RecuperationSure!749"))
        self.assertContains(self.client.get(urlsplit(lien).path), "Ce lien a expiré")
        inconnu = self.client.post(reverse("password_reset"), {"email": "inconnu@example.test"})
        self.assertEqual(inconnu.status_code, reponse.status_code)

    def test_jeton_expire(self):
        uid = urlsafe_base64_encode(force_bytes(self.acteur.pk))
        with patch("django.contrib.auth.tokens.PasswordResetTokenGenerator._now", return_value=datetime.now()-timedelta(hours=2)):
            jeton = default_token_generator.make_token(self.acteur)
        self.client.logout()
        self.assertContains(self.client.get(reverse("password_reset_confirm", args=[uid, jeton])), "Ce lien a expiré")
