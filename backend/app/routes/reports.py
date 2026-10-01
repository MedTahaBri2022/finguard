from io import BytesIO

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.responses import StreamingResponse

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from app.core.database import get_db
from app.dependencies.auth import get_current_client_user
from app.models.analysis import Analysis
from app.models.user import User


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
)


# ============================================================
# HELPERS
# ============================================================

def format_money(value) -> str:
    try:
        return f"{float(value or 0):,.2f} DH"
    except (ValueError, TypeError):
        return "0.00 DH"


def format_integer(value) -> str:
    try:
        return f"{int(value or 0):,}"
    except (ValueError, TypeError):
        return "0"


def safe_text(value) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def severity_label(value) -> str:
    severity = str(value or "").strip().lower()

    if severity == "high":
        return "HIGH"

    if severity == "medium":
        return "MEDIUM"

    if severity == "low":
        return "LOW"

    return severity.upper() or "UNKNOWN"


# ============================================================
# GENERATE ANALYSIS PDF
# ============================================================

@router.get("/{analysis_id}/pdf")
def generate_analysis_pdf(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client_user),
):

    # ========================================================
    # FIND ANALYSIS + FINDINGS (TENANT-SCOPED)
    # ========================================================

    client_profile_id = current_user.client_profile_id

    query = (
        select(Analysis)
        .options(
            selectinload(
                Analysis.findings
            )
        )
        .where(
            Analysis.id == analysis_id,
            Analysis.client_profile_id == client_profile_id,
        )
    )

    result = db.execute(query)

    analysis = (
        result.scalar_one_or_none()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # ========================================================
    # PDF BUFFER
    # ========================================================

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"FinGuard Analysis #{analysis.id}",
        author="FinGuard",
    )

    # ========================================================
    # STYLES
    # ========================================================

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "FinGuardTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "FinGuardSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=18,
    )

    filename_style = ParagraphStyle(
        "Filename",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=16,
        spaceAfter=10,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#334155"),
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )

    table_text_style = ParagraphStyle(
        "TableText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )

    table_bold_style = ParagraphStyle(
        "TableBold",
        parent=table_text_style,
        fontName="Helvetica-Bold",
    )

    # ========================================================
    # STORY
    # ========================================================

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        Paragraph(
            "FinGuard",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "AI Financial Intelligence Report",
            subtitle_style,
        )
    )

    story.append(
        Paragraph(
            safe_text(
                analysis.filename
            ),
            filename_style,
        )
    )

    if analysis.created_at:
        created_at_text = (
            analysis.created_at.strftime(
                "%Y-%m-%d %H:%M"
            )
        )
    else:
        created_at_text = "N/A"

    story.append(
        Paragraph(
            (
                f"Analysis ID: #{analysis.id}"
                f" &nbsp; | &nbsp; "
                f"Created: {created_at_text}"
            ),
            subtitle_style,
        )
    )

    # ========================================================
    # EXECUTIVE RISK OVERVIEW
    # ========================================================

    story.append(
        Paragraph(
            "Executive Risk Overview",
            section_style,
        )
    )

    risk_score = float(
        analysis.risk_score or 0
    )

    risk_level = str(
        analysis.risk_level or "UNKNOWN"
    ).upper()

    risk_data = [
        [
            "Risk Score",
            "Risk Level",
            "Money At Risk",
        ],
        [
            f"{risk_score:.2f}/100",
            risk_level,
            format_money(
                analysis.money_at_risk
            ),
        ],
    ]

    risk_table = Table(
        risk_data,
        colWidths=[
            55 * mm,
            55 * mm,
            55 * mm,
        ],
    )

    risk_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#e2e8f0"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.HexColor("#334155"),
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                11,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                11,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                colors.HexColor("#cbd5e1"),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cbd5e1"),
            ),
        ])
    )

    story.append(
        risk_table
    )

    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    story.append(
        Paragraph(
            "Dataset Overview",
            section_style,
        )
    )

    dataset_data = [
        [
            "Rows",
            "Columns",
            "Total Findings",
        ],
        [
            format_integer(
                analysis.rows
            ),
            format_integer(
                analysis.columns
            ),
            format_integer(
                analysis.total_findings
            ),
        ],
    ]

    dataset_table = Table(
        dataset_data,
        colWidths=[
            55 * mm,
            55 * mm,
            55 * mm,
        ],
    )

    dataset_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#f1f5f9"),
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                colors.HexColor("#cbd5e1"),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cbd5e1"),
            ),
        ])
    )

    story.append(
        dataset_table
    )

    # ========================================================
    # RISK DISTRIBUTION
    # ========================================================

    story.append(
        Paragraph(
            "Risk Distribution",
            section_style,
        )
    )

    distribution_data = [
        [
            "Severity",
            "Number of Findings",
        ],
        [
            "High Risk",
            format_integer(
                analysis.high_risk
            ),
        ],
        [
            "Medium Risk",
            format_integer(
                analysis.medium_risk
            ),
        ],
        [
            "Low Risk",
            format_integer(
                analysis.low_risk
            ),
        ],
    ]

    distribution_table = Table(
        distribution_data,
        colWidths=[
            85 * mm,
            80 * mm,
        ],
    )

    distribution_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#e2e8f0"),
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica",
            ),
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "CENTER",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cbd5e1"),
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                9,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                9,
            ),
        ])
    )

    story.append(
        distribution_table
    )

    # ========================================================
    # AI EXECUTIVE SUMMARY
    # ========================================================

    if analysis.ai_summary:

        story.append(
            Paragraph(
                "AI Executive Summary",
                section_style,
            )
        )

        # Keep long AI content outside a one-cell Table.
        # Paragraphs can split naturally across PDF pages, while a single
        # oversized table row cannot and raises ReportLab LayoutError.
        story.append(
            Paragraph(
                safe_text(analysis.ai_summary),
                body_style,
            )
        )

    # ========================================================
    # DETAILED FINDINGS
    # ========================================================

    findings = list(
        analysis.findings or []
    )

    if findings:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "Detailed Findings",
                section_style,
            )
        )

        story.append(
            Paragraph(
                (
                    f"{len(findings)} findings detected "
                    f"during this analysis."
                ),
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        findings_data = [
            [
                Paragraph(
                    "Severity",
                    table_bold_style,
                ),
                Paragraph(
                    "Type",
                    table_bold_style,
                ),
                Paragraph(
                    "Transaction",
                    table_bold_style,
                ),
                Paragraph(
                    "Amount At Risk",
                    table_bold_style,
                ),
                Paragraph(
                    "Details",
                    table_bold_style,
                ),
            ]
        ]

        for finding in findings:

            findings_data.append(
                [
                    Paragraph(
                        safe_text(
                            severity_label(
                                finding.severity
                            )
                        ),
                        table_bold_style,
                    ),
                    Paragraph(
                        safe_text(
                            finding.type
                        ),
                        table_text_style,
                    ),
                    Paragraph(
                        safe_text(
                            finding.transaction_id
                            or "N/A"
                        ),
                        table_text_style,
                    ),
                    Paragraph(
                        safe_text(
                            format_money(
                                finding.amount_at_risk
                            )
                        ),
                        table_text_style,
                    ),
                    Paragraph(
                        safe_text(
                            finding.message
                        ),
                        table_text_style,
                    ),
                ]
            )

        findings_table = Table(
            findings_data,
            colWidths=[
                18 * mm,
                31 * mm,
                25 * mm,
                29 * mm,
                62 * mm,
            ],
            repeatRows=1,
        )

        findings_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#e2e8f0"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0f172a"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f8fafc"),
                    ],
                ),
            ])
        )

        story.append(
            findings_table
        )

    # ========================================================
    # FOOTER
    # ========================================================

    story.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "FinGuard — AI-powered financial "
                "monitoring and risk intelligence."
            ),
            small_style,
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )

    buffer.seek(0)

    pdf_filename = (
        f"finguard_analysis_"
        f"{analysis.id}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="{pdf_filename}"'
            )
        },
    )