
from io import BytesIO
from xml.sax.saxutils import escape

from django.db.models import Sum
from .http import PDFResponse as FileResponse
from django.utils import timezone

from medicaments.models import Medicament

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)

from .services import rapport_ventes, rapport_stock


# ==========================================================
# CONFIGURATION GENERALE
# ==========================================================

COULEUR_PRINCIPALE = colors.HexColor("#17365D")
COULEUR_SECONDAIRE = colors.HexColor("#EAF1F8")


def creer_document(buffer, titre):
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=titre,
        leftMargin=35,
        rightMargin=35,
        topMargin=40,
        bottomMargin=40,
    )


def creer_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="PharmagestTitre",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=COULEUR_PRINCIPALE,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="PharmagestCellule",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
        )
    )

    styles.add(
        ParagraphStyle(
            name="PharmagestEntete",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.white,
        )
    )

    return styles


def creer_tableau(entetes, lignes, largeurs, styles):
    donnees = [
        [
            Paragraph(escape(str(valeur)), styles["PharmagestEntete"])
            for valeur in entetes
        ]
    ]

    for ligne in lignes:
        donnees.append([
            Paragraph(
                escape(str(valeur)),
                styles["PharmagestCellule"],
            )
            for valeur in ligne
        ])

    tableau = Table(
        donnees,
        colWidths=largeurs,
        repeatRows=1,
        hAlign="LEFT",
    )

    tableau.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COULEUR_PRINCIPALE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                COULEUR_SECONDAIRE,
            ]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    return tableau


def ajouter_section(elements, titre, entetes, lignes, largeurs, styles):
    titre_section = Paragraph(titre, styles["Heading3"])

    if not lignes:
        elements.append(
            KeepTogether([
                titre_section,
                Paragraph(
                    "Aucune donnée à signaler.",
                    styles["Normal"],
                ),
                Spacer(1, 15),
            ])
        )
        return

    tableau = creer_tableau(
        entetes,
        lignes,
        largeurs,
        styles,
    )

    elements.append(titre_section)
    elements.append(Spacer(1, 8))
    elements.append(tableau)
    elements.append(Spacer(1, 20))


# ==========================================================
# RAPPORT PDF DES VENTES
# ==========================================================

def generer_pdf_ventes(date_debut=None, date_fin=None):
    rapport = rapport_ventes(date_debut, date_fin)

    buffer = BytesIO()

    document = creer_document(
        buffer,
        "Rapport des ventes - PHARMAGEST",
    )

    styles = creer_styles()

    elements = [
        Paragraph(
            "PHARMAGEST",
            styles["PharmagestTitre"],
        ),
        Paragraph(
            "Rapport des ventes",
            styles["Heading2"],
        ),
        Paragraph(
            "Date : "
            + timezone.localdate().strftime("%d/%m/%Y"),
            styles["Normal"],
        ),
        Spacer(1, 20),
    ]
    elements.append(Paragraph(
        "Période des ventes : " + (date_debut.strftime("%d/%m/%Y") if date_debut else "début de l’historique")
        + " - " + (date_fin.strftime("%d/%m/%Y") if date_fin else "aujourd’hui"), styles["Normal"],
    ))
    elements.append(Paragraph("Référence : RV-" + timezone.localtime().strftime("%Y%m%d-%H%M%S"), styles["Normal"]))

    lignes = [
        (
            "Nombre de ventes",
            str(rapport["nombre_ventes"]),
        ),
        (
            "Chiffre d'affaires brut",
            f'{rapport["chiffre_affaires"]} Ar',
        ),
        (
            "Montant encaissé",
            f'{rapport["montant_encaisse"]} Ar',
        ),
        (
            "Reste à payer",
            f'{rapport["reste_a_payer"]} Ar',
        ),
    ]

    ajouter_section(
        elements,
        "Statistiques des ventes",
        ["Indicateur", "Valeur"],
        lignes,
        [280, 220],
        styles,
    )

    elements.append(
        Paragraph(
            f"Retours validés : {rapport['retours']} Ar. "
            f"Chiffre d'affaires net : {rapport['chiffre_affaires_net']} Ar. "
            f"Remboursements : {rapport['remboursements']} Ar.",
            styles["Normal"],
        )
    )

    document.build(elements)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="rapport_ventes_pharmagest.pdf",
        content_type="application/pdf",
    )


# ==========================================================
# RAPPORT PDF DES STOCKS
# ==========================================================

def generer_pdf_stock():
    rapport = rapport_stock()

    buffer = BytesIO()

    document = creer_document(
        buffer,
        "Rapport des stocks - PHARMAGEST",
    )

    styles = creer_styles()

    aujourd_hui = timezone.localdate()

    elements = [
        Paragraph(
            "PHARMAGEST",
            styles["PharmagestTitre"],
        ),
        Paragraph(
            "Rapport des stocks",
            styles["Heading2"],
        ),
        Paragraph(
            "Date : " + aujourd_hui.strftime("%d/%m/%Y"),
            styles["Normal"],
        ),
        Spacer(1, 20),
    ]
    elements.append(Paragraph("Référence : RS-" + timezone.localtime().strftime("%Y%m%d-%H%M%S"), styles["Normal"]))

    # ------------------------------------------------------
    # 1. MEDICAMENTS EN STOCK FAIBLE
    # ------------------------------------------------------

    lignes_stocks_faibles = []

    for alerte in rapport["medicaments_stock_faible"]:
        lignes_stocks_faibles.append((alerte["medicament"].nom_commercial,
                                     str(alerte["quantite"]), str(alerte["seuil"])))

    ajouter_section(
        elements,
        "1. Médicaments en stock faible",
        ["Médicament", "Stock disponible", "Seuil"],
        lignes_stocks_faibles,
        [240, 140, 120],
        styles,
    )

    # ------------------------------------------------------
    # 2. LOTS PROCHES DE LA PEREMPTION
    # ------------------------------------------------------

    lignes_lots_proches = []

    for lot in rapport["lots_proches_peremption"]:
        lignes_lots_proches.append(
            (
                lot.medicament.nom_commercial,
                lot.numero_lot,
                lot.date_peremption.strftime("%d/%m/%Y"),
                str(lot.quantite),
            )
        )

    ajouter_section(
        elements,
        "2. Lots proches de la péremption",
        ["Médicament", "Numéro du lot", "Expiration", "Qté"],
        lignes_lots_proches,
        [180, 130, 120, 70],
        styles,
    )

    # ------------------------------------------------------
    # 3. LOTS PERIMES
    # ------------------------------------------------------

    lignes_lots_perimes = []

    for lot in rapport["lots_perimes"]:
        lignes_lots_perimes.append(
            (
                lot.medicament.nom_commercial,
                lot.numero_lot,
                lot.date_peremption.strftime("%d/%m/%Y"),
                str(lot.quantite),
            )
        )

    ajouter_section(
        elements,
        "3. Lots périmés",
        ["Médicament", "Numéro du lot", "Expiration", "Qté"],
        lignes_lots_perimes,
        [180, 130, 120, 70],
        styles,
    )

    # ------------------------------------------------------
    # GENERATION DU DOCUMENT
    # ------------------------------------------------------

    document.build(elements)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="rapport_stocks_pharmagest.pdf",
        content_type="application/pdf",
    )
