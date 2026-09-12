"""
Generates a PDF report for a disease prediction using ReportLab.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.services.recommendation_service import DISCLAIMER


def generate_prediction_report(prediction, user, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    filename = f"report_{prediction.id}.pdf"
    filepath = os.path.join(output_dir, filename)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleGreen",
        parent=styles["Title"],
        textColor=colors.HexColor("#2E7D32"),
    )

    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    elements = []

    elements.append(
        Paragraph(
            "GreenMind - Crop Disease Report",
            title_style,
        )
    )

    elements.append(Spacer(1, 0.5 * cm))

    # Treat predictions below 60% confidence as unconfirmed.
    confidence_threshold = 0.60

    is_low_confidence = (
        getattr(prediction, "status", None) == "low_confidence"
        or prediction.confidence < confidence_threshold
    )

    if is_low_confidence:
        detected_disease = "Unable to confidently identify"
    else:
        detected_disease = prediction.disease.replace("_", " ")

    meta_rows = [
        ["Farmer Name", user.name],
        [
            "Date",
            datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        ],
        ["Crop", prediction.crop],
        ["Detected Disease", detected_disease],
        [
            "Confidence",
            f"{prediction.confidence * 100:.1f}%",
        ],
        ["Severity", prediction.severity],
    ]

    # Show the model's top possible disease only as a hint.
    if (
        is_low_confidence
        and getattr(prediction, "possible_disease", None)
    ):
        meta_rows.append(
            [
                "Possible Disease",
                f"{prediction.possible_disease} "
                "(hint only, not a diagnosis)",
            ]
        )

    meta_table = Table(
        meta_rows,
        colWidths=[5 * cm, 10 * cm],
    )

    meta_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E8F5E9"),
                ),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(meta_table)
    elements.append(Spacer(1, 0.5 * cm))

    if getattr(prediction, "is_fallback_prediction", False):
        elements.append(
            Paragraph(
                "<b>Note:</b> This prediction was generated in "
                "development/demo fallback mode "
                "(no trained model was available) and should not "
                "be treated as a real diagnosis.",
                ParagraphStyle(
                    "Warn",
                    parent=normal_style,
                    textColor=colors.red,
                ),
            )
        )

        elements.append(Spacer(1, 0.3 * cm))

    if prediction.image_path and os.path.exists(prediction.image_path):
        try:
            elements.append(
                RLImage(
                    prediction.image_path,
                    width=8 * cm,
                    height=8 * cm,
                )
            )

            elements.append(Spacer(1, 0.5 * cm))

        except Exception:
            pass

    rec = prediction.recommendation

    if rec:
        recommendation_sections = [
            ("Treatment Guidance", rec.treatment),
            ("Fertilizer Guidance", rec.fertilizer),
            ("Pesticide Guidance", rec.pesticide_guidance),
            ("Prevention", rec.prevention),
            ("Crop Management", rec.crop_management),
            ("Monitoring Advice", rec.monitoring_advice),
        ]

        for label, value in recommendation_sections:
            if value:
                elements.append(
                    Paragraph(
                        label,
                        heading_style,
                    )
                )

                elements.append(
                    Paragraph(
                        value,
                        normal_style,
                    )
                )

                elements.append(
                    Spacer(1, 0.3 * cm)
                )

    elements.append(Spacer(1, 0.5 * cm))

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=normal_style,
        fontSize=8,
        textColor=colors.grey,
    )

    elements.append(
        Paragraph(
            f"<i>{DISCLAIMER}</i>",
            disclaimer_style,
        )
    )

    doc.build(elements)

    return filepath