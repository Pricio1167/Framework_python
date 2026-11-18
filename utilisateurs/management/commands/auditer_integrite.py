"""Contrôles en lecture seule des données existantes, sans réparation implicite."""
import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from PIL import Image

from achats.models import CommandeAchat, LigneReception
from medicaments.models import Medicament
from stock.models import LotStock
from ventes.finance import solde
from ventes.models import Vente, LigneRetour, Remboursement, Paiement


class Command(BaseCommand):
    help = "Audite les lots, ventes, retours, paiements et photos sans modifier les données."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="verification/audit_integrite.json")

    def handle(self, *args, **options):
        erreurs = []
        avertissements = []
        for medicament in Medicament.objects.all():
            if medicament.prix_achat < 0 or medicament.prix_vente < 0:
                erreurs.append(f"Médicament {medicament.pk} : prix négatif")
            if medicament.photo:
                try:
                    with medicament.photo.open("rb") as fichier, Image.open(fichier) as image:
                        image.verify()
                except (OSError, ValueError):
                    erreurs.append(f"Médicament {medicament.pk} : photo manquante ou invalide")
        for vente in Vente.objects.filter(statut="VALIDEE").prefetch_related("lignes__lots_utilises", "paiements", "retours"):
            for ligne in vente.lignes.all():
                if ligne.quantite <= 0 or ligne.prix_unitaire < 0:
                    erreurs.append(f"Ligne de vente {ligne.pk} : quantité ou prix invalide")
                allocations = list(ligne.lots_utilises.select_related("lot"))
                if sum(l.quantite for l in allocations) != ligne.quantite:
                    erreurs.append(f"Ligne de vente {ligne.pk} : allocations de lots incomplètes")
                if any(l.lot.medicament_id != ligne.medicament_id for l in allocations):
                    erreurs.append(f"Ligne de vente {ligne.pk} : médicament différent de celui du lot")
                retourne = LigneRetour.objects.filter(ligne_vente=ligne, retour__statut="VALIDE").aggregate(total=Sum("quantite"))["total"] or 0
                if retourne > ligne.quantite:
                    erreurs.append(f"Ligne de vente {ligne.pk} : retours supérieurs à la quantité vendue")
            bilan = solde(vente)
            if bilan["rembourse"] > bilan["paye"]:
                erreurs.append(f"Vente {vente.pk} : remboursements supérieurs aux encaissements confirmés")
            if bilan["paye"] - bilan["rembourse"] > vente.total - bilan["retours"]:
                avertissements.append(f"Vente {vente.pk} : trop-perçu restant à traiter ou à justifier")
        for remboursement in Remboursement.objects.select_related("retour"):
            if remboursement.montant <= 0 or remboursement.retour.statut != "VALIDE":
                erreurs.append(f"Remboursement {remboursement.pk} : montant ou état de retour incohérent")
        for commande in CommandeAchat.objects.exclude(statut__in=["BROUILLON", "ANNULEE"]).prefetch_related("lignes"):
            for ligne in commande.lignes.all():
                recu = LigneReception.objects.filter(ligne_achat=ligne, reception__validee=True).aggregate(total=Sum("quantite_recue"))["total"] or 0
                if recu > ligne.quantite or (commande.statut == "RECUE" and recu != ligne.quantite):
                    erreurs.append(f"Commande {commande.pk} : quantités réceptionnées incohérentes")
        if LotStock.objects.filter(quantite__lt=0).exists():
            erreurs.append("Présence de stocks négatifs")
        historiques = Paiement.objects.filter(statut="CONFIRME", mode__in=["MOBILE", "CARTE"], reference_verification="").count()
        if historiques:
            avertissements.append(f"{historiques} paiements électroniques historiques sans preuve enregistrée : rapprochement manuel nécessaire")
        resultat = {"statut": "ERREURS" if erreurs else "OK", "erreurs": erreurs,
                    "avertissements": avertissements, "lecture_seule": True}
        sortie = Path(options["output"])
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f"Audit en lecture seule : {len(erreurs)} erreur(s), {len(avertissements)} avertissement(s). Rapport : {sortie}")
        if erreurs:
            raise CommandError("Des incohérences exigent une vérification métier ; aucune donnée modifiée.")
