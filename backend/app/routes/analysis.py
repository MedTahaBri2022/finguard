import io
import json
import os
import tempfile
import zipfile
from typing import Any, Dict, Optional

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.auth import (
    get_current_client_user,
)

from app.models.analysis import Analysis
from app.models.alert import Alert
from app.models.finding import Finding
from app.models.client_profile import ClientProfile
from app.models.client_baseline import ClientBaseline
from app.models.user import User

from app.services import ai_service
from app.services import leak_detector
from app.services import schema_mapper

from app.services.data_cleaner import (
    clean_transaction_dataframe,
)


router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Analysis"],
)


# ============================================================
# HELPERS
# ============================================================

def _parse_json(
    value: Optional[str],
) -> Optional[
    Dict[str, Any]
]:

    if not value:
        return None

    try:
        parsed = json.loads(
            value
        )

        if isinstance(
            parsed,
            dict,
        ):
            return parsed

    except Exception:
        pass

    return None


def _load_client_mapping(
    client: Optional[
        ClientProfile
    ],
) -> Optional[
    Dict[str, str]
]:

    if client is None:
        return None

    mapping = _parse_json(
        client.column_mapping_json
    )

    if not mapping:
        return None

    return {
        str(source): str(target)

        for source, target
        in mapping.items()
    }


def _load_business_rules(
    client: Optional[
        ClientProfile
    ],
) -> Dict[str, Any]:

    if client is None:
        return {}

    rules = (
        _parse_json(
            client.business_rules_json
        )
        or {}
    )

    if (
        client.failure_rate_warning
        is not None
    ):
        rules[
            "failure_rate_warning"
        ] = (
            client.failure_rate_warning
        )

    if (
        client.refund_rate_warning
        is not None
    ):
        rules[
            "refund_rate_warning"
        ] = (
            client.refund_rate_warning
        )

    if (
        client.high_amount_multiplier
        is not None
    ):
        rules[
            "high_amount_multiplier"
        ] = (
            client.high_amount_multiplier
        )

    return rules


def _load_active_baseline(
    db: Session,
    client: Optional[
        ClientProfile
    ],
) -> tuple[
    Optional[ClientBaseline],
    Optional[Dict[str, Any]],
]:

    if client is None:
        return None, None

    baseline_record = (
        db.query(
            ClientBaseline
        )
        .filter(
            ClientBaseline.client_profile_id
            == client.id,

            ClientBaseline.is_active.is_(
                True
            ),
        )
        .order_by(
            ClientBaseline.version.desc()
        )
        .first()
    )

    if baseline_record is None:
        return None, None

    baseline_data = (
        _parse_json(
            baseline_record.baseline_json
        )
    )

    if baseline_data is None:
        return (
            baseline_record,
            None,
        )

    return (
        baseline_record,
        baseline_data,
    )



# ============================================================
# UPLOAD SECURITY
# ============================================================

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DATASET_ROWS = 100_000
MAX_DATASET_COLUMNS = 100
MAX_FILENAME_LENGTH = 255

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}

ALLOWED_MIME_TYPES = {
    ".csv": {
        "text/csv",
        "application/csv",
        "text/plain",
        "application/vnd.ms-excel",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
    ".xls": {
        "application/vnd.ms-excel",
        "application/octet-stream",
    },
}


def _validate_upload_metadata(
    file: UploadFile,
) -> tuple[str, str]:

    raw_filename = (
        file.filename
        or ""
    ).strip()

    if not raw_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid filename is required.",
        )

    if len(raw_filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is too long.",
        )

    # Reject path traversal / path-like names.
    if (
        raw_filename != os.path.basename(raw_filename)
        or "/" in raw_filename
        or "\\" in raw_filename
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    extension = (
        os.path.splitext(
            raw_filename
        )[1]
        .lower()
    )

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Only CSV, XLSX and XLS "
                "files are supported."
            ),
        )

    content_type = (
        file.content_type
        or ""
    ).lower().strip()

    allowed_mime_types = (
        ALLOWED_MIME_TYPES[
            extension
        ]
    )

    if (
        content_type
        and content_type
        not in allowed_mime_types
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Uploaded file MIME type "
                "does not match the supported format."
            ),
        )

    return (
        raw_filename,
        extension,
    )


async def _read_upload_safely(
    file: UploadFile,
) -> bytes:

    contents = await file.read(
        MAX_UPLOAD_SIZE_BYTES + 1
    )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if (
        len(contents)
        > MAX_UPLOAD_SIZE_BYTES
    ):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "Uploaded file exceeds "
                "the 10 MB limit."
            ),
        )

    return contents


def _validate_file_signature(
    contents: bytes,
    extension: str,
) -> None:

    if extension == ".xlsx":
        # XLSX is a ZIP-based Office Open XML container.
        if not contents.startswith(b"PK"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid XLSX file signature."
                ),
            )

        try:
            with zipfile.ZipFile(
                io.BytesIO(contents)
            ) as archive:
                required_members = {
                    "[Content_Types].xml",
                    "xl/workbook.xml",
                }

                archive_members = set(
                    archive.namelist()
                )

                if not required_members.issubset(
                    archive_members
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "Malformed XLSX file."
                        ),
                    )

        except HTTPException:
            raise

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed XLSX file.",
            )

    elif extension == ".xls":
        # Legacy OLE Compound File header.
        xls_signature = (
            b"\xD0\xCF\x11\xE0"
            b"\xA1\xB1\x1A\xE1"
        )

        if not contents.startswith(
            xls_signature
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid XLS file signature.",
            )

    elif extension == ".csv":
        # Reject obvious binary payloads masquerading as CSV.
        if b"\x00" in contents[:4096]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid CSV file content."
                ),
            )


def _validate_dataframe_security(
    df: pd.DataFrame,
) -> None:

    rows, columns = df.shape

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset is empty.",
        )

    if rows > MAX_DATASET_ROWS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "Dataset exceeds the maximum "
                f"of {MAX_DATASET_ROWS:,} rows."
            ),
        )

    if columns > MAX_DATASET_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Dataset exceeds the maximum "
                f"of {MAX_DATASET_COLUMNS} columns."
            ),
        )

    normalized_columns = [
        str(column).strip()
        for column in df.columns
    ]

    if any(
        not column
        for column in normalized_columns
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Dataset contains invalid "
                "column names."
            ),
        )

    if (
        len(normalized_columns)
        != len(set(normalized_columns))
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Dataset contains duplicate "
                "column names."
            ),
        )

    df.columns = (
        normalized_columns
    )

def _load_dataframe(
    file_path: str,
    extension: str,
) -> pd.DataFrame:

    try:

        if extension == ".csv":

            return pd.read_csv(
                file_path,
                low_memory=False,
            )

        if extension in {
            ".xlsx",
            ".xls",
        }:

            return pd.read_excel(
                file_path
            )

    except Exception as exc:

        raise ValueError(
            "Uploaded file is malformed "
            "or cannot be parsed."
        ) from exc

    raise ValueError(
        "Unsupported file format."
    )


# ============================================================
# ANALYZE
# ============================================================

@router.post(
    "/analyze"
)
async def analyze_transactions(
    file: UploadFile = File(
        ...
    ),

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_client_user
    ),
):

    # ========================================================
    # AUTHENTICATED CLIENT / TENANT
    # ========================================================

    client_profile_id = (
        current_user.client_profile_id
    )

    if client_profile_id is None:

        raise HTTPException(
            status_code=403,
            detail=(
                "Authenticated user is not "
                "associated with a client profile."
            ),
        )

    client = (
        db.query(
            ClientProfile
        )
        .filter(
            ClientProfile.id
            == client_profile_id,

            ClientProfile.is_active.is_(
                True
            ),
        )
        .first()
    )

    if client is None:

        raise HTTPException(
            status_code=403,
            detail=(
                "Client profile does not exist "
                "or is inactive."
            ),
        )

    # ========================================================
    # FILE / UPLOAD SECURITY
    # ========================================================

    (
        filename,
        extension,
    ) = _validate_upload_metadata(
        file
    )

    temp_path = None

    try:

        # ====================================================
        # SAVE TEMPORARILY
        # ====================================================

        contents = await _read_upload_safely(
            file
        )

        _validate_file_signature(
            contents=contents,
            extension=extension,
        )

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

        # ====================================================
        # READ DATAFRAME
        # ====================================================

        df = _load_dataframe(
            file_path=temp_path,
            extension=extension,
        )

        _validate_dataframe_security(
            df
        )

        # ====================================================
        # SCHEMA MAPPING
        # ====================================================

        client_mapping = (
            _load_client_mapping(
                client
            )
        )

        if client_mapping:

            mapping = (
                client_mapping
            )

            mapping_mode = (
                "client_profile"
            )

        else:

            mapping = (
                schema_mapper
                .detect_schema_mapping(
                    df
                )
            )

            mapping_mode = (
                "automatic"
            )

        validation = (
            schema_mapper
            .validate_mapping(
                df,
                mapping,
            )
        )

        mapping_errors = (
            validation.get(
                "errors",
                [],
            )
        )

        if mapping_errors:

            raise HTTPException(
                status_code=400,

                detail={
                    "message": (
                        "Invalid schema mapping."
                    ),

                    "errors": (
                        mapping_errors
                    ),

                    "warnings": (
                        validation.get(
                            "warnings",
                            [],
                        )
                    ),
                },
            )

        # ====================================================
        # CANONICAL DATAFRAME
        # ====================================================

        canonical_df = (
            schema_mapper
            .apply_schema_mapping(
                df,
                mapping,

                keep_unmapped_columns=True,
            )
        )

        # ====================================================
        # DATA CLEANING + FX
        # ====================================================

        cleaning_result = (
            clean_transaction_dataframe(
                canonical_df
            )
        )

        cleaned_df = (
            cleaning_result[
                "dataframe"
            ]
        )

        if cleaned_df.empty:

            raise HTTPException(
                status_code=400,

                detail=(
                    "No usable transactions "
                    "remain after cleaning."
                ),
            )

        # ====================================================
        # LOAD CLIENT BASELINE
        # ====================================================

        (
            baseline_record,
            baseline_data,
        ) = _load_active_baseline(
            db=db,
            client=client,
        )

        # Client may have baseline_ready=True
        # while baseline data is unavailable/corrupt.
        # Detector then safely falls back to
        # batch/statistical signals.
        baseline_used = bool(
            baseline_data
        )

        # ====================================================
        # CLIENT BUSINESS RULES
        # ====================================================

        business_rules = (
            _load_business_rules(
                client
            )
        )

        # ====================================================
        # LEAK DETECTOR
        # ====================================================

        detection_result = (
            leak_detector
            .detect_financial_leaks(
                df=cleaned_df,

                client_baseline=(
                    baseline_data
                ),

                business_rules=(
                    business_rules
                ),
            )
        )

        # ====================================================
        # AI EXPLANATION
        # ====================================================

        try:

            ai_result = (
                ai_service.analyze(
                    detection_result
                )
            )

        except Exception as ai_error:

            ai_result = {
                "summary": (
                    "AI explanation unavailable."
                ),

                "error": (
                    "AI service temporarily unavailable."
                ),
            }

        # ====================================================
        # EXTRACT RESULT
        # ====================================================

        findings = (
            detection_result.get(
                "findings",
                [],
            )
        )

        risk_score = float(
            detection_result.get(
                "risk_score",
                0.0,
            )
            or 0.0
        )

        risk_level = str(
            detection_result.get(
                "risk_level",
                "LOW",
            )
            or "LOW"
        )

        money_at_risk = float(
            detection_result.get(
                "money_at_risk",
                0.0,
            )
            or 0.0
        )

        high_risk = int(
            detection_result.get(
                "high_risk",
                0,
            )
            or 0
        )

        medium_risk = int(
            detection_result.get(
                "medium_risk",
                0,
            )
            or 0
        )

        low_risk = int(
            detection_result.get(
                "low_risk",
                0,
            )
            or 0
        )

        total_findings = len(
            findings
        )

        # ====================================================
        # AI SUMMARY
        # ====================================================

        ai_summary = None

        if isinstance(
            ai_result,
            dict,
        ):

            ai_summary_value = (
                ai_result.get(
                    "summary"
                )
                or ai_result.get(
                    "analysis"
                )
                or ai_result.get(
                    "message"
                )
            )

            if isinstance(
                ai_summary_value,
                (dict, list),
            ):

                ai_summary = json.dumps(
                    ai_summary_value,
                    ensure_ascii=False,
                    default=str,
                )

            elif (
                ai_summary_value
                is not None
            ):

                ai_summary = str(
                    ai_summary_value
                )

        elif ai_result is not None:

            ai_summary = str(
                ai_result
            )

        # ====================================================
        # SAVE ANALYSIS
        # ====================================================

        analysis_record = Analysis(
            client_profile_id=(
                client.id
            ),

            filename=(
                filename
            ),

            rows=int(
                len(
                    cleaned_df
                )
            ),

            columns=int(
                len(
                    canonical_df.columns
                )
            ),

            risk_score=(
                risk_score
            ),

            risk_level=(
                risk_level
            ),

            total_findings=(
                total_findings
            ),

            high_risk=(
                high_risk
            ),

            medium_risk=(
                medium_risk
            ),

            low_risk=(
                low_risk
            ),

            money_at_risk=(
                money_at_risk
            ),

            ai_summary=(
                ai_summary
            ),
        )

        db.add(
            analysis_record
        )

        # Generate analysis_record.id
        # before saving Findings and Alerts.
        db.flush()

        # ====================================================
        # SAVE FINDINGS
        # ====================================================

        for finding_data in findings:

            finding = Finding(
                analysis_id=(
                    analysis_record.id
                ),

                type=str(
                    finding_data.get(
                        "type",
                        "unknown",
                    )
                ),

                severity=str(
                    finding_data.get(
                        "severity",
                        "low",
                    )
                ),

                title=str(
                    finding_data.get(
                        "title",
                        "Financial finding",
                    )
                ),

                message=str(
                    finding_data.get(
                        "message",
                        "",
                    )
                ),

                amount_at_risk=float(
                    finding_data.get(
                        "amount_at_risk",
                        0.0,
                    )
                    or 0.0
                ),

                transaction_id=(
                    str(
                        finding_data.get(
                            "transaction_id"
                        )
                    )
                    if finding_data.get(
                        "transaction_id"
                    )
                    is not None
                    else None
                ),
            )

            db.add(
                finding
            )

        # ====================================================
        # CREATE ALERTS
        # ====================================================

        for finding_data in findings:

            severity = (
                str(
                    finding_data.get(
                        "severity",
                        "low",
                    )
                )
                .lower()
            )

            # Only meaningful alerts.
            if severity not in {
                "high",
                "medium",
            }:
                continue

            alert = Alert(

                # ============================================
                # TENANT LINKAGE
                # ============================================

                analysis_id=(
                    analysis_record.id
                ),

                client_profile_id=(
                    client.id
                ),

                # ============================================
                # ALERT DATA
                # ============================================

                title=str(
                    finding_data.get(
                        "title",
                        "Financial risk detected",
                    )
                ),

                alert_type=str(
                    finding_data.get(
                        "type",
                        "financial_risk",
                    )
                ),

                severity=(
                    severity
                ),

                message=str(
                    finding_data.get(
                        "message",
                        "",
                    )
                ),

                amount_at_risk=float(
                    finding_data.get(
                        "amount_at_risk",
                        0.0,
                    )
                    or 0.0
                ),

                transaction_id=(
                    str(
                        finding_data.get(
                            "transaction_id"
                        )
                    )
                    if finding_data.get(
                        "transaction_id"
                    )
                    is not None
                    else None
                ),

                is_read=False,
            )

            db.add(
                alert
            )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        db.refresh(
            analysis_record
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {
            "analysis_id": (
                analysis_record.id
            ),

            "engine": {
                "version": (
                    detection_result.get(
                        "engine_version"
                    )
                ),

                "baseline_used": (
                    detection_result.get(
                        "baseline_used",
                        False,
                    )
                ),
            },

            "client": {
                "id": (
                    client.id
                ),

                "name": (
                    client.name
                ),

                "base_currency": (
                    client.base_currency
                ),

                "risk_tolerance": (
                    client.risk_tolerance
                ),

                "baseline_ready": (
                    client.baseline_ready
                ),
            },

            "baseline": (
                {
                    "id": (
                        baseline_record.id
                    ),

                    "version": (
                        baseline_record.version
                    ),

                    "sample_size": (
                        baseline_record.sample_size
                    ),

                    "used": (
                        baseline_used
                    ),
                }

                if baseline_record
                else {
                    "used": False
                }
            ),

            "schema": {
                "mapping_mode": (
                    mapping_mode
                ),

                "mapping": (
                    mapping
                ),

                "warnings": (
                    validation.get(
                        "warnings",
                        [],
                    )
                ),
            },

            "dataset": {
                "filename": (
                    filename
                ),

                "rows": (
                    len(
                        cleaned_df
                    )
                ),

                "columns": (
                    len(
                        canonical_df.columns
                    )
                ),
            },

            "client_configuration": {
                "business_rules": (
                    business_rules
                ),
            },

            "detection": (
                detection_result
            ),

            "ai": (
                ai_result
            ),

            "data_cleaning": {
                "original_rows": (
                    cleaning_result.get(
                        "original_rows"
                    )
                ),

                "cleaned_rows": (
                    cleaning_result.get(
                        "cleaned_rows"
                    )
                ),

                "removed_rows": (
                    cleaning_result.get(
                        "removed_rows"
                    )
                ),

                "dataset_currency": (
                    cleaning_result.get(
                        "dataset_currency"
                    )
                ),

                "currency_stats": (
                    cleaning_result.get(
                        "currency_stats"
                    )
                ),

                "normalization_coverage": (
                    cleaning_result.get(
                        "normalization_coverage"
                    )
                ),

                "currency_conflicts": (
                    cleaning_result.get(
                        "currency_conflicts"
                    )
                ),

                "unknown_currency_rows": (
                    cleaning_result.get(
                        "unknown_currency_rows"
                    )
                ),

                "fx_unavailable_rows": (
                    cleaning_result.get(
                        "fx_unavailable_rows"
                    )
                ),

                "missing_fx_date_rows": (
                    cleaning_result.get(
                        "missing_fx_date_rows"
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
                "Analysis failed due to "
                "an internal server error."
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