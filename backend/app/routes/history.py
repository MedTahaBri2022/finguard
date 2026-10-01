from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.auth import (
    get_current_client_user,
)

from app.models.analysis import Analysis
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/history",
    tags=["History"],
)


# ============================================================
# HELPERS
# ============================================================

def _serialize_analysis_summary(
    analysis: Analysis,
) -> dict:

    return {
        "id": analysis.id,

        "filename": (
            analysis.filename
        ),

        "rows": (
            analysis.rows
        ),

        "columns": (
            analysis.columns
        ),

        "risk_score": (
            analysis.risk_score
        ),

        "risk_level": (
            analysis.risk_level
        ),

        "total_findings": (
            analysis.total_findings
        ),

        "high_risk": (
            analysis.high_risk
        ),

        "medium_risk": (
            analysis.medium_risk
        ),

        "low_risk": (
            analysis.low_risk
        ),

        "money_at_risk": (
            analysis.money_at_risk
        ),

        "ai_summary": (
            analysis.ai_summary
        ),

        "created_at": (
            analysis.created_at.isoformat()
            if analysis.created_at
            else None
        ),
    }


def _serialize_finding(
    finding,
) -> dict:

    return {
        "id": (
            finding.id
        ),

        "type": (
            finding.type
        ),

        "severity": (
            finding.severity
        ),

        "title": (
            finding.title
        ),

        "message": (
            finding.message
        ),

        "amount_at_risk": (
            finding.amount_at_risk
        ),

        "transaction_id": (
            finding.transaction_id
        ),

        "created_at": (
            finding.created_at.isoformat()
            if finding.created_at
            else None
        ),
    }


# ============================================================
# GET ALL ANALYSES
# ============================================================

@router.get("")
def get_analysis_history(
    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_client_user
    ),
):

    client_profile_id = (
        current_user.client_profile_id
    )

    analyses = (
        db.query(Analysis)
        .filter(
            Analysis.client_profile_id
            == client_profile_id
        )
        .order_by(
            Analysis.created_at.desc()
        )
        .all()
    )

    return {
        "success": True,

        "count": len(
            analyses
        ),

        "analyses": [
            _serialize_analysis_summary(
                analysis
            )
            for analysis in analyses
        ],
    }


# ============================================================
# GET ONE ANALYSIS
# ============================================================

@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_client_user
    ),
):

    client_profile_id = (
        current_user.client_profile_id
    )

    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.id == analysis_id,

            Analysis.client_profile_id
            == client_profile_id,
        )
        .first()
    )

    if analysis is None:

        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # ========================================================
    # FINDINGS
    # ========================================================

    findings = (
        analysis.findings
    )

    analysis_data = (
        _serialize_analysis_summary(
            analysis
        )
    )

    analysis_data[
        "findings"
    ] = [
        _serialize_finding(
            finding
        )
        for finding in findings
    ]

    return {
        "success": True,

        "analysis": (
            analysis_data
        ),
    }