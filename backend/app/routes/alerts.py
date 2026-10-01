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

from app.models.alert import Alert
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"],
)


# ============================================================
# HELPERS
# ============================================================

def _serialize_alert(
    alert: Alert,
) -> dict:
    return {
        "id": alert.id,
        "analysis_id": alert.analysis_id,
        "client_profile_id": (
            alert.client_profile_id
        ),
        "title": alert.title,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "amount_at_risk": (
            alert.amount_at_risk
        ),
        "transaction_id": (
            alert.transaction_id
        ),
        "is_read": alert.is_read,
        "created_at": (
            alert.created_at.isoformat()
            if alert.created_at
            else None
        ),
    }


# ============================================================
# GET UNREAD ALERTS
# ============================================================

@router.get("/unread")
def get_unread_alerts(
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

    alerts = (
        db.query(Alert)
        .filter(
            Alert.client_profile_id
            == client_profile_id,

            Alert.is_read.is_(False),
        )
        .order_by(
            Alert.created_at.desc()
        )
        .all()
    )

    return {
        "success": True,
        "count": len(alerts),
        "alerts": [
            _serialize_alert(
                alert
            )
            for alert in alerts
        ],
    }


# ============================================================
# MARK ALL ALERTS AS READ
# ============================================================

@router.patch("/read-all")
def mark_all_alerts_as_read(
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

    alerts = (
        db.query(Alert)
        .filter(
            Alert.client_profile_id
            == client_profile_id,

            Alert.is_read.is_(False),
        )
        .all()
    )

    for alert in alerts:
        alert.is_read = True

    db.commit()

    return {
        "success": True,
        "updated": len(alerts),
    }


# ============================================================
# MARK ONE ALERT AS READ
# ============================================================

@router.patch("/{alert_id}/read")
def mark_alert_as_read(
    alert_id: int,

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

    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,

            Alert.client_profile_id
            == client_profile_id,
        )
        .first()
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    alert.is_read = True

    db.commit()
    db.refresh(
        alert
    )

    return {
        "success": True,
        "message": (
            "Alert marked as read."
        ),
        "alert": _serialize_alert(
            alert
        ),
    }


# ============================================================
# GET ALL ALERTS
# ============================================================

@router.get("/")
def get_all_alerts(
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

    alerts = (
        db.query(Alert)
        .filter(
            Alert.client_profile_id
            == client_profile_id
        )
        .order_by(
            Alert.created_at.desc()
        )
        .limit(100)
        .all()
    )

    return {
        "success": True,
        "count": len(alerts),
        "alerts": [
            _serialize_alert(
                alert
            )
            for alert in alerts
        ],
    }


# ============================================================
# GET ONE ALERT
# ============================================================

@router.get("/{alert_id}")
def get_alert_by_id(
    alert_id: int,

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

    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,

            Alert.client_profile_id
            == client_profile_id,
        )
        .first()
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return {
        "success": True,
        "alert": _serialize_alert(
            alert
        ),
    }