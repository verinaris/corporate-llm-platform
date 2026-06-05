"""
PDF-Export — Executive Summary als 1-2-Seiten-PDF.

Bewusst kurzgehalten — der ausführliche Plan ist die DOCX-Version.
Die PDF ist die "Tasche-fertig"-Variante für Banken-Termine etc.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.businessplan.models import BusinessPlanResult


def export_pdf(result: BusinessPlanResult) -> bytes:
    """Erzeugt ein 1-2-seitiges PDF mit Executive Summary + Scorecard."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    p = result.input

    story = []

    # --- Titel ---
    story.append(Paragraph(f"Executive Summary – {p.startup_name}", styles["Title"]))
    story.append(Spacer(1, 12))

    meta_text = (
        f"<b>Standort:</b> {p.location or '—'}  ·  "
        f"<b>Rechtsform:</b> {p.legal_form or '—'}  ·  "
        f"<b>Gründer:</b> {p.founder_name or '—'}"
    )
    story.append(Paragraph(meta_text, styles["BodyText"]))
    story.append(Spacer(1, 12))

    # --- Summary ---
    story.append(Paragraph(result.summary, styles["BodyText"]))
    story.append(Spacer(1, 14))

    # --- Scorecard ---
    story.append(Paragraph("Scorecard", styles["Heading2"]))
    score_data = [
        ["Kriterium", "Score"],
        ["Businessplan-Reifegrad", f"{result.scores.business_plan_maturity}/100"],
        ["Bankenfähigkeit", f"{result.scores.bankability}/100"],
        ["Förderfähigkeit", f"{result.scores.fundability}/100"],
        ["Investorenfähigkeit", f"{result.scores.investability}/100"],
    ]
    score_table = Table(score_data, colWidths=[280, 100])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 14))

    # --- Kritische Prüfpunkte ---
    story.append(Paragraph("Kritische Prüfpunkte", styles["Heading2"]))
    for c in result.checks:
        status_color = (
            "green" if c.status == "OK"
            else "orange" if c.status == "Nachschärfen"
            else "red"
        )
        para = (
            f"<b>{c.area} – <font color='{status_color}'>{c.status}</font>:</b> "
            f"{c.finding}  <i>{c.recommendation}</i>"
        )
        story.append(Paragraph(para, styles["BodyText"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # --- Top-3-Förderprogramme ---
    top_funding = result.funding[:3]
    if top_funding:
        story.append(Paragraph("Top Fördermittel-Kandidaten", styles["Heading2"]))
        for fm in top_funding:
            para = (
                f"<b>{fm.name}</b> ({fm.fit}): {fm.why}"
            )
            story.append(Paragraph(para, styles["BodyText"]))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))
    disclaimer = (
        "<i>Hinweis: Dieses Dokument ist eine strukturierte Vorbereitung, "
        "keine Rechts-, Steuer- oder Fördermittelberatung. "
        "Fördermittel müssen vor Antragstellung tagesaktuell geprüft werden.</i>"
    )
    story.append(Paragraph(disclaimer, styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
