from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from rapports.http import PDFResponse as FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from utilisateurs.permissions import exiger_permission
from .models import Vente, Paiement, RetourVente, Remboursement
from .operations import solde


def document(titre, reference, informations, lignes, identite=None):
    flux = BytesIO()
    styles = getSampleStyleSheet()
    def texte(valeur):
        return Paragraph(escape(str(valeur)), styles["BodyText"])
    from dashboard.parametres import identite_pharmacie
    identite = identite or identite_pharmacie()
    elements = [Paragraph(escape(identite.get("pharmacie", settings.PHARMACIE_NOM)), styles["Title"]),
                texte(identite.get("adresse", settings.PHARMACIE_ADRESSE)), Spacer(1, 8 * mm),
                Paragraph(escape(titre), styles["Heading1"]), texte(reference)]
    elements.extend(texte(info) for info in informations)
    elements.append(Spacer(1, 6 * mm))
    tableau = Table([[texte(cellule) for cellule in ligne] for ligne in lignes],
                    repeatRows=1, hAlign="LEFT", colWidths=[80*mm, 25*mm, 32*mm, 33*mm])
    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eff5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, -1), .4, colors.lightgrey),
    ]))
    elements.extend([tableau, Spacer(1, 8 * mm), texte(identite.get("mentions", settings.PHARMACIE_MENTIONS))])
    def pied_de_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20*mm, 14*mm, reference)
        canvas.drawRightString(190*mm, 14*mm, f"Page {doc.page}")
        canvas.restoreState()
    SimpleDocTemplate(flux, title=titre, leftMargin=20*mm, rightMargin=20*mm).build(
        elements, onFirstPage=pied_de_page, onLaterPages=pied_de_page,
    )
    flux.seek(0)
    return FileResponse(flux, as_attachment=True, filename=f"{reference}.pdf", content_type="application/pdf")


@login_required
def facture(request, pk, type_document):
    exiger_permission(request.user, "ventes.view_vente")
    vente = get_object_or_404(Vente, pk=pk, statut="VALIDEE")
    if type_document != "facture":
        raise Http404
    bilan = solde(vente)
    lignes = [["Médicament", "Quantité", "Prix unitaire", "Sous-total"]]
    instantane = vente.instantane_facture
    if instantane:
        lignes += [[l["medicament"], l["quantite"], f"{l['prix_unitaire']} Ar", f"{l['sous_total']} Ar"]
                   for l in instantane["lignes"]]
    else:
        lignes += [[l.medicament, l.quantite, f"{l.prix_unitaire} Ar", f"{l.sous_total} Ar"]
                   for l in vente.lignes.select_related("medicament")]
    return document("Facture de vente", f"FAC-{vente.pk:08d}", [
        f"Date : {vente.date_vente:%d/%m/%Y}", f"Client : {instantane.get('client', str(vente.client or 'Client de passage'))}",
        f"Total brut : {vente.total} Ar ; retours : {bilan['retours']} Ar",
        f"Payé : {bilan['paye']} Ar ; remboursé : {bilan['rembourse']} Ar ; solde : {bilan['reste']} Ar",
    ], lignes, instantane)


@login_required
def recu(request, pk):
    exiger_permission(request.user, "ventes.view_paiement")
    paiement = get_object_or_404(Paiement, pk=pk, statut="CONFIRME")
    return document("Reçu de paiement", f"REC-{paiement.pk:08d}", [
        f"Vente : {paiement.vente_id}", f"Date : {timezone.localtime(paiement.date_paiement):%d/%m/%Y %H:%M}",
        f"Enregistré par : {paiement.utilisateur}",
    ], [["Opération", "Quantité", "Mode", "Montant"],
        ["Paiement", "1", paiement.get_mode_display(), f"{paiement.montant} Ar"]])


@login_required
def justificatif_retour(request, pk):
    exiger_permission(request.user, "ventes.view_retourvente")
    retour = get_object_or_404(RetourVente, pk=pk, statut="VALIDE")
    lignes = [["Produit", "Quantité", "Prix", "Valeur"]]
    lignes += [[l.ligne_vente.medicament, l.quantite, f"{l.ligne_vente.prix_unitaire} Ar",
                f"{l.quantite*l.ligne_vente.prix_unitaire} Ar"] for l in retour.lignes.select_related("ligne_vente__medicament")]
    return document("Justificatif de retour", f"RET-{retour.pk:08d}",
                    [f"Vente : {retour.vente_id}", f"Date : {timezone.localtime(retour.date_retour):%d/%m/%Y %H:%M}",
                     f"Motif : {retour.motif}", "Produits initialement placés hors stock vendable. Consulter les décisions de quarantaine."], lignes)


@login_required
def justificatif_remboursement(request, pk):
    exiger_permission(request.user, "ventes.view_remboursement")
    remboursement = get_object_or_404(Remboursement, pk=pk)
    return document("Justificatif de remboursement", f"REM-{pk:08d}",
                    [f"Retour : {remboursement.retour_id}",
                     f"Date : {timezone.localtime(remboursement.date_creation):%d/%m/%Y %H:%M}",
                     f"Enregistré par : {remboursement.utilisateur}", f"Motif : {remboursement.motif}"],
                    [["Opération", "Quantité", "Devise", "Montant"], ["Remboursement", 1, "Ar", remboursement.montant]])
