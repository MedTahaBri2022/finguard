import json
import os
import tempfile
from typing import Optional

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.auth import (
    get_current_client_user,
    require_platform_admin,
)

from app.models.client_profile import ClientProfile
from app.models.client_baseline import ClientBaseline
from app.models.user import User

from app.services import schema_mapper
from app.services.data_cleaner import (
    clean_transaction_dataframe,
)
from app.services.baseline_service import (
    build_client_baseline,
)


router = APIRouter(
    prefix="/api/v1/clients",
    tags=["Clients"],
)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class ClientProfileCreate(BaseModel):
    name: str

    business_type: Optional[str] = None

    base_currency: str = "MAD"

    risk_tolerance: str = "conservative"

    column_mapping: Optional[
        dict[str, str]
    ] = None

    business_rules: Optional[
        dict
    ] = None

    failure_rate_warning: Optional[
        float
    ] = None

    refund_rate_warning: Optional[
        float
    ] = None

    high_amount_multiplier: Optional[
        float
    ] = None

    minimum_history_rows: int = 100

    is_active: bool = True


class ClientProfileUpdate(BaseModel):
    name: Optional[str] = None

    business_type: Optional[
        str
    ] = None

    base_currency: Optional[
        str
    ] = None

    risk_tolerance: Optional[
        str
    ] = None

    column_mapping: Optional[
        dict[str, str]
    ] = None

    business_rules: Optional[
        dict
    ] = None

    failure_rate_warning: Optional[
        float
    ] = None

    refund_rate_warning: Optional[
        float
    ] = None

    high_amount_multiplier: Optional[
        float
    ] = None

    minimum_history_rows: Optional[
        int
    ] = None

    is_active: Optional[
        bool
    ] = None


# ============================================================
# HELPERS
# ============================================================

def _parse_json_field(
    value: Optional[str],
):
    if not value:
        return None

    try:
        return json.loads(
            value
        )

    except Exception:
        return None


def _serialize_client(
    client: ClientProfile,
):
    return {
        "id": client.id,

        "name": client.name,

        "business_type": (
            client.business_type
        ),

        "base_currency": (
            client.base_currency
        ),

        "risk_tolerance": (
            client.risk_tolerance
        ),

        "column_mapping": (
            _parse_json_field(
                client.column_mapping_json
            )
        ),

        "business_rules": (
            _parse_json_field(
                client.business_rules_json
            )
        ),

        "failure_rate_warning": (
            client.failure_rate_warning
        ),

        "refund_rate_warning": (
            client.refund_rate_warning
        ),

        "high_amount_multiplier": (
            client.high_amount_multiplier
        ),

        "baseline_ready": (
            client.baseline_ready
        ),

        "minimum_history_rows": (
            client.minimum_history_rows
        ),

        "is_active": (
            client.is_active
        ),

        "created_at": (
            client.created_at
        ),

        "updated_at": (
            client.updated_at
        ),
    }


def _load_dataframe(
    file_path: str,
    filename: str,
) -> pd.DataFrame:

    extension = (
        os.path.splitext(
            filename
        )[1]
        .lower()
    )

    if extension == ".csv":
        return pd.read_csv(
            file_path
        )

    if extension in {
        ".xlsx",
        ".xls",
    }:
        return pd.read_excel(
            file_path
        )

    raise ValueError(
        "Unsupported file format."
    )


# ============================================================
# CREATE CLIENT
# ============================================================

@router.post("")
def create_client(
    payload: ClientProfileCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_platform_admin
    ),
):

    existing = (
        db.query(
            ClientProfile
        )
        .filter(
            ClientProfile.name
            == payload.name
        )
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                "A client profile with "
                "this name already exists."
            ),
        )

    risk_tolerance = (
        payload.risk_tolerance
        .strip()
        .lower()
    )

    allowed_tolerances = {
        "conservative",
        "balanced",
        "aggressive",
    }

    if (
        risk_tolerance
        not in allowed_tolerances
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "risk_tolerance must be "
                "conservative, balanced "
                "or aggressive."
            ),
        )

    client = ClientProfile(
        name=payload.name,

        business_type=(
            payload.business_type
        ),

        base_currency=(
            payload.base_currency
            .strip()
            .upper()
        ),

        risk_tolerance=(
            risk_tolerance
        ),

        column_mapping_json=(
            json.dumps(
                payload.column_mapping
            )
            if payload.column_mapping
            is not None
            else None
        ),

        business_rules_json=(
            json.dumps(
                payload.business_rules
            )
            if payload.business_rules
            is not None
            else None
        ),

        failure_rate_warning=(
            payload.failure_rate_warning
        ),

        refund_rate_warning=(
            payload.refund_rate_warning
        ),

        high_amount_multiplier=(
            payload.high_amount_multiplier
        ),

        baseline_ready=False,

        minimum_history_rows=(
            payload.minimum_history_rows
        ),

        is_active=(
            payload.is_active
        ),
    )

    db.add(
        client
    )

    db.commit()

    db.refresh(
        client
    )

    return {
        "message": (
            "Client profile created."
        ),

        "client": (
            _serialize_client(
                client
            )
        ),
    }


# ============================================================
# LIST CLIENTS
# ============================================================

@router.get("")
def list_clients(
    active_only: bool = Query(
        True
    ),

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_platform_admin
    ),
):

    query = db.query(
        ClientProfile
    )

    if active_only:
        query = query.filter(
            ClientProfile.is_active
            == True
        )

    clients = (
        query
        .order_by(
            ClientProfile.id.asc()
        )
        .all()
    )

    return {
        "total": len(
            clients
        ),

        "clients": [
            _serialize_client(
                client
            )
            for client
            in clients
        ],
    }


# ============================================================
# GET CURRENT CLIENT PROFILE
# ============================================================

@router.get("/me")
def get_current_client_profile(
    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_client_user
    ),
):

    client = (
        db.query(
            ClientProfile
        )
        .filter(
            ClientProfile.id
            == current_user.client_profile_id,

            ClientProfile.is_active.is_(
                True
            ),
        )
        .first()
    )

    if client is None:
        raise HTTPException(
            status_code=404,
            detail="Client profile not found.",
        )

    result = (
        _serialize_client(
            client
        )
    )

    result["analysis_count"] = len(
        client.analyses
    )

    result["baseline_count"] = len(
        client.baselines
    )

    return result


# ============================================================
# GET CLIENT
# ============================================================

@router.get(
    "/{client_id}"
)
def get_client(
    client_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_platform_admin
    ),
):

    client = (
        db.query(
            ClientProfile
        )
        .filter(
            ClientProfile.id
            == client_id
        )
        .first()
    )

    if client is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Client profile not found."
            ),
        )

    result = (
        _serialize_client(
            client
        )
    )

    result[
        "analysis_count"
    ] = len(
        client.analyses
    )

    result[
        "baseline_count"
    ] = len(
        client.baselines
    )

    return result


# ============================================================
# UPDATE CLIENT
# ============================================================

@router.patch(
    "/{client_id}"
)
def update_client(
    client_id: int,

    payload: ClientProfileUpdate,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_platform_admin
    ),
):

    client = (
        db.query(
            ClientProfile
        )
        .filter(
            ClientProfile.id
            == client_id
        )
        .first()
    )

    if client is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Client profile not found."
            ),
        )

    if payload.name is not None:

        duplicate = (
            db.query(
                ClientProfile
            )
            .filter(
                ClientProfile.name
                == payload.name,
                ClientProfile.id
                != client.id,
            )
            .first()
        )

        if duplicate is not None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "A client profile with "
                    "this name already exists."
                ),
            )

        client.name = (
            payload.name
        )

    if (
        payload.business_type
        is not None
    ):
        client.business_type = (
            payload.business_type
        )

    if (
        payload.base_currency
        is not None
    ):
        client.base_currency = (
            payload.base_currency
            .strip()
            .upper()
        )

    if (
        payload.risk_tolerance
        is not None
    ):
        risk_tolerance = (
            payload.risk_tolerance
            .strip()
            .lower()
        )

        allowed = {
            "conservative",
            "balanced",
            "aggressive",
        }

        if (
            risk_tolerance
            not in allowed
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid risk tolerance."
                ),
            )

        client.risk_tolerance = (
            risk_tolerance
        )

    if (
        payload.column_mapping
        is not None
    ):
        client.column_mapping_json = (
            json.dumps(
                payload.column_mapping
            )
        )

    if (
        payload.business_rules
        is not None
    ):
        client.business_rules_json = (
            json.dumps(
                payload.business_rules
            )
        )

    if (
        payload.failure_rate_warning
        is not None
    ):
        client.failure_rate_warning = (
            payload.failure_rate_warning
        )

    if (
        payload.refund_rate_warning
        is not None
    ):
        client.refund_rate_warning = (
            payload.refund_rate_warning
        )

    if (
        payload.high_amount_multiplier
        is not None
    ):
        client.high_amount_multiplier = (
            payload.high_amount_multiplier
        )

    if (
        payload.minimum_history_rows
        is not None
    ):
        client.minimum_history_rows = (
            payload.minimum_history_rows
        )

    if (
        payload.is_active
        is not None
    ):
        client.is_active = (
            payload.is_active
        )

    db.commit()

    db.refresh(
        client
    )

    return {
        "message": (
            "Client profile updated."
        ),

        "client": (
            _serialize_client(
                client
            )
        ),
    }


# ============================================================
# BUILD CLIENT BASELINE
# ============================================================

@router.post(
    "/{client_id}/baseline"
)
async def create_client_baseline(
    client_id: int,

    file: UploadFile = File(
        ...
    ),

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_platform_admin
    ),
):

    # --------------------------------------------------------
    # CLIENT
    # --------------------------------------------------------

    client = (
        db.query(
            ClientProfile
        )
        .filter(
            ClientProfile.id
            == client_id
        )
        .first()
    )

    if client is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Client profile not found."
            ),
        )

    if not client.is_active:
        raise HTTPException(
            status_code=400,
            detail=(
                "Client profile is inactive."
            ),
        )

    # --------------------------------------------------------
    # FILE VALIDATION
    # --------------------------------------------------------

    filename = (
        file.filename
        or "historical_dataset"
    )

    extension = (
        os.path.splitext(
            filename
        )[1]
        .lower()
    )

    allowed_extensions = {
        ".csv",
        ".xlsx",
        ".xls",
    }

    if (
        extension
        not in allowed_extensions
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV, XLSX and XLS "
                "files are supported."
            ),
        )

    temp_path = None

    try:

        # ----------------------------------------------------
        # TEMP FILE
        # ----------------------------------------------------

        contents = await file.read()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            temp_file.write(
                contents
            )

            temp_path = (
                temp_file.name
            )

        # ----------------------------------------------------
        # READ DATASET
        # ----------------------------------------------------

        df = _load_dataframe(
            file_path=temp_path,
            filename=filename,
        )

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Historical dataset "
                    "is empty."
                ),
            )

        df.columns = [
            str(column).strip()
            for column
            in df.columns
        ]

        # ----------------------------------------------------
        # CLIENT MAPPING
        # ----------------------------------------------------

        mapping = (
            _parse_json_field(
                client.column_mapping_json
            )
        )

        mapping_mode = (
            "client_profile"
        )

        if not mapping:

            mapping = (
                schema_mapper
                .detect_schema_mapping(
                    df
                )
            )

            mapping_mode = (
                "automatic"
            )

        # ----------------------------------------------------
        # VALIDATE MAPPING
        # ----------------------------------------------------

        validation = (
            schema_mapper
            .validate_mapping(
                df,
                mapping,
            )
        )

        errors = validation.get(
            "errors",
            []
        )

        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Invalid schema mapping."
                    ),
                    "errors": errors,
                    "warnings": (
                        validation.get(
                            "warnings",
                            [],
                        )
                    ),
                },
            )

        # ----------------------------------------------------
        # APPLY CANONICAL MAPPING
        # ----------------------------------------------------

        canonical_df = (
            schema_mapper
            .apply_schema_mapping(
                df,
                mapping,
                keep_unmapped_columns=True,
            )
        )

        # ----------------------------------------------------
        # CLEAN + CURRENCY NORMALIZATION
        # ----------------------------------------------------

        cleaned = (
            clean_transaction_dataframe(
                canonical_df
            )
        )

        cleaned_df = cleaned[
            "dataframe"
        ]

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No usable historical "
                    "transactions remain after "
                    "data cleaning."
                ),
            )

        # ----------------------------------------------------
        # BUILD BASELINE
        # ----------------------------------------------------

        baseline = (
            build_client_baseline(
                df=cleaned_df,

                minimum_history_rows=(
                    client.minimum_history_rows
                ),
            )
        )

        readiness = (
            baseline.get(
                "readiness",
                {},
            )
        )

        baseline_ready = bool(
            readiness.get(
                "baseline_ready",
                False,
            )
        )

        # ----------------------------------------------------
        # VERSION
        # ----------------------------------------------------

        latest_baseline = (
            db.query(
                ClientBaseline
            )
            .filter(
                ClientBaseline.client_profile_id
                == client.id
            )
            .order_by(
                ClientBaseline.version.desc()
            )
            .first()
        )

        next_version = (
            latest_baseline.version + 1
            if latest_baseline
            is not None
            else 1
        )

        # ----------------------------------------------------
        # DISABLE OLD BASELINES
        # ----------------------------------------------------

        old_baselines = (
            db.query(
                ClientBaseline
            )
            .filter(
                ClientBaseline.client_profile_id
                == client.id,
                ClientBaseline.is_active
                == True,
            )
            .all()
        )

        for old_baseline in old_baselines:
            old_baseline.is_active = (
                False
            )

        # ----------------------------------------------------
        # SAVE BASELINE
        # ----------------------------------------------------

        baseline_record = (
            ClientBaseline(
                client_profile_id=(
                    client.id
                ),

                version=(
                    next_version
                ),

                sample_size=(
                    int(
                        baseline.get(
                            "sample_size",
                            len(cleaned_df),
                        )
                    )
                ),

                baseline_json=(
                    json.dumps(
                        baseline
                    )
                ),

                is_active=True,
            )
        )

        db.add(
            baseline_record
        )

        # ----------------------------------------------------
        # UPDATE CLIENT
        # ----------------------------------------------------

        client.baseline_ready = (
            baseline_ready
        )

        db.commit()

        db.refresh(
            baseline_record
        )

        db.refresh(
            client
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {
            "message": (
                "Client baseline created."
            ),

            "client": {
                "id": client.id,
                "name": client.name,

                "baseline_ready": (
                    client.baseline_ready
                ),

                "minimum_history_rows": (
                    client.minimum_history_rows
                ),
            },

            "baseline": {
                "id": (
                    baseline_record.id
                ),

                "version": (
                    baseline_record.version
                ),

                "sample_size": (
                    baseline_record.sample_size
                ),

                "is_active": (
                    baseline_record.is_active
                ),

                "created_at": (
                    baseline_record.created_at
                ),
            },

            "schema": {
                "mapping_mode": (
                    mapping_mode
                ),

                "mapping": mapping,

                "warnings": (
                    validation.get(
                        "warnings",
                        [],
                    )
                ),
            },

            "data_cleaning": {
                "original_rows": (
                    cleaned.get(
                        "original_rows"
                    )
                ),

                "cleaned_rows": (
                    cleaned.get(
                        "cleaned_rows"
                    )
                ),

                "removed_rows": (
                    cleaned.get(
                        "removed_rows"
                    )
                ),

                "normalization_coverage": (
                    cleaned.get(
                        "normalization_coverage"
                    )
                ),

                "currency_conflicts": (
                    cleaned.get(
                        "currency_conflicts"
                    )
                ),

                "unknown_currency_rows": (
                    cleaned.get(
                        "unknown_currency_rows"
                    )
                ),

                "fx_unavailable_rows": (
                    cleaned.get(
                        "fx_unavailable_rows"
                    )
                ),

                "missing_fx_date_rows": (
                    cleaned.get(
                        "missing_fx_date_rows"
                    )
                ),
            },

            "readiness": readiness,

            "statistics": {
                "amount": (
                    baseline.get(
                        "amount"
                    )
                ),

                "operational": (
                    baseline.get(
                        "operational"
                    )
                ),

                "category_count": (
                    len(
                        baseline.get(
                            "categories",
                            {},
                        )
                    )
                ),

                "entity_count": (
                    len(
                        baseline.get(
                            "entities",
                            {},
                        )
                    )
                ),

                "transaction_type_count": (
                    len(
                        baseline.get(
                            "transaction_types",
                            {},
                        )
                    )
                ),
            },
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to build client "
                f"baseline: {str(exc)}"
            ),
        )

    finally:

        if (
            temp_path
            and os.path.exists(
                temp_path
            )
        ):
            try:
                os.remove(
                    temp_path
                )
            except Exception:
                pass