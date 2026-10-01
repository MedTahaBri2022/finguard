import re
from typing import Any, Dict, List, Optional

import pandas as pd

from app.services.currency_service import (
    normalize_transaction_amount,
    normalize_currency,
)


# ============================================================
# COLUMN CANDIDATES
# ============================================================

AMOUNT_COLUMNS = [
    "amount",
    "transaction_amount",
    "payment_amount",
    "operation_amount",
    "total_amount",
    "total",
    "value",
    "montant",
    "valeur",
]

CURRENCY_COLUMNS = [
    "currency",
    "currency_code",
    "devise",
    "monnaie",
    "ccy",
]

DATE_COLUMNS = [
    "timestamp",
    "transaction_timestamp",
    "transaction_date",
    "payment_date",
    "operation_date",
    "created_at",
    "created_date",
    "date",
    "datetime",
    "date_transaction",
    "date_operation",
]

TRANSACTION_ID_COLUMNS = [
    "transaction_id",
    "txn_id",
    "tx_id",
    "payment_id",
    "operation_id",
    "reference",
]

STATUS_COLUMNS = [
    "status",
    "transaction_status",
    "payment_status",
    "operation_status",
    "state",
    "etat",
    "statut",
]


# ============================================================
# HELPERS
# ============================================================

def _normalize_column_name(value: Any) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
    )


def _find_column(
    df: pd.DataFrame,
    candidates: List[str],
) -> Optional[str]:

    normalized = {
        _normalize_column_name(column): column
        for column in df.columns
    }

    for candidate in candidates:
        key = _normalize_column_name(candidate)

        if key in normalized:
            return normalized[key]

    return None


def _safe_string(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def _parse_transaction_date(value: Any):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        parsed = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(parsed):
            return None

        return parsed.to_pydatetime()

    except Exception:
        return None


# ============================================================
# METADATA / NON-TRANSACTION ROW DETECTION
# ============================================================

def _looks_like_metadata_row(
    row: pd.Series,
    amount_column: Optional[str],
    transaction_id_column: Optional[str],
    status_column: Optional[str],
    date_column: Optional[str],
) -> bool:
    """
    Conservative generic metadata/profile-row detection.

    Removes rows only when there is strong evidence that
    they are profiling/summary metadata rather than
    real financial transactions.
    """

    values = [
        _safe_string(value).lower()
        for value in row.tolist()
    ]

    joined = " ".join(values)

    # ========================================================
    # 1. EXPLICIT METADATA MARKERS
    # ========================================================

    metadata_keywords = {
        "stringlengths",
        "string_lengths",
        "stringclasses",
        "float64",
        "int64",
        "object",
        "datatype",
        "data_type",
        "statistics",
        "summary",
        "nullcount",
        "null_count",
        "percentile",
        "percentiles",
    }

    if any(
        value in metadata_keywords
        for value in values
    ):
        return True

    if "stringlengths" in joined:
        return True

    # ========================================================
    # 2. PROFILING PERCENTAGE ROW
    #
    # Example:
    # 1 | 1 | 0.04 | 99.9% | 0.55 | 7.1% ...
    # ========================================================

    percentage_cells = sum(
        1
        for value in values
        if re.fullmatch(
            r"-?\d+(?:[.,]\d+)?%",
            value,
        )
    )

    if percentage_cells >= 2:
        return True

    # ========================================================
    # 3. INVALID AMOUNT VALUE
    # ========================================================

    if amount_column is not None:

        raw_amount = _safe_string(
            row.get(amount_column)
        )

        if raw_amount.endswith("%"):
            return True

    # ========================================================
    # 4. MULTIPLE DATES IN ONE TIMESTAMP CELL
    #
    # Profiling exports may store:
    # min_timestamp + max_timestamp
    #
    # Example:
    # 2024-04-04 07:12:032024-07-07 14:24:03
    # ========================================================

    if date_column is not None:

        raw_date = _safe_string(
            row.get(date_column)
        )

        detected_dates = re.findall(
            r"\b\d{4}-\d{2}-\d{2}\b",
            raw_date,
        )

        if len(detected_dates) >= 2:
            return True

    # ========================================================
    # 5. TRANSACTION ID METADATA MARKERS
    # ========================================================

    if transaction_id_column is not None:

        transaction_id = _safe_string(
            row.get(
                transaction_id_column
            )
        ).lower()

        if transaction_id in metadata_keywords:
            return True

    # ========================================================
    # 6. STATUS METADATA MARKERS
    # ========================================================

    if status_column is not None:

        status = _safe_string(
            row.get(
                status_column
            )
        ).lower()

        if status in {
            "datatype",
            "data_type",
            "stringlengths",
            "statistics",
            "summary",
        }:
            return True

    return False


# ============================================================
# DOMINANT DATASET CURRENCY
# ============================================================

def _infer_dataset_currency(
    currencies: List[str],
    total_rows: int,
) -> Optional[str]:
    """
    Conservative dataset-level currency inference.

    Currency is inferred only when:

    - at least 80% of dataset rows explicitly reveal currency
    - at least 95% of known currencies agree

    This prevents FinGuard from assigning a currency to
    many unknown rows based on only a small sample.
    """

    known = [
        currency
        for currency in currencies
        if currency
        and currency != "UNKNOWN"
    ]

    if not known or total_rows <= 0:
        return None

    known_coverage = (
        len(known)
        / total_rows
    )

    if known_coverage < 0.80:
        return None

    counts = (
        pd.Series(known)
        .value_counts()
    )

    dominant_currency = str(
        counts.index[0]
    )

    dominant_count = int(
        counts.iloc[0]
    )

    dominance = (
        dominant_count
        / len(known)
    )

    if dominance < 0.95:
        return None

    return dominant_currency


# ============================================================
# MAIN CLEANER
# ============================================================

def clean_transaction_dataframe(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    if df is None:
        raise ValueError(
            "Dataset is missing."
        )

    working_df = df.copy()

    working_df.columns = [
        str(column).strip()
        for column in working_df.columns
    ]

    original_rows = len(
        working_df
    )

    original_columns = len(
        working_df.columns
    )

    # ========================================================
    # DETECT IMPORTANT COLUMNS
    # ========================================================

    amount_column = _find_column(
        working_df,
        AMOUNT_COLUMNS,
    )

    if amount_column is None:
        raise ValueError(
            "FinGuard could not identify an amount column."
        )

    currency_column = _find_column(
        working_df,
        CURRENCY_COLUMNS,
    )

    date_column = _find_column(
        working_df,
        DATE_COLUMNS,
    )

    transaction_id_column = _find_column(
        working_df,
        TRANSACTION_ID_COLUMNS,
    )

    status_column = _find_column(
        working_df,
        STATUS_COLUMNS,
    )

    # ========================================================
    # REMOVE COMPLETELY EMPTY ROWS
    # ========================================================

    working_df = (
        working_df
        .dropna(
            how="all"
        )
        .copy()
    )

    # ========================================================
    # REMOVE STRONG METADATA / PROFILE ROWS
    # ========================================================

    metadata_mask = working_df.apply(
        lambda row: _looks_like_metadata_row(
            row=row,
            amount_column=amount_column,
            transaction_id_column=transaction_id_column,
            status_column=status_column,
            date_column=date_column,
        ),
        axis=1,
    )

    working_df = working_df.loc[
        ~metadata_mask
    ].copy()

    working_df.reset_index(
        drop=True,
        inplace=True,
    )

    cleaned_rows = len(
        working_df
    )

    removed_rows = (
        original_rows
        - cleaned_rows
    )

    # ========================================================
    # FIRST PASS:
    # DETECT EXPLICIT CURRENCIES
    # ========================================================

    detected_currencies: List[str] = []

    for _, row in working_df.iterrows():

        explicit_currency = None

        if currency_column is not None:

            explicit_currency = (
                normalize_currency(
                    row.get(
                        currency_column
                    )
                )
            )

        detected_currencies.append(
            explicit_currency
            or "UNKNOWN"
        )

    # ========================================================
    # CONSERVATIVE DATASET CURRENCY INFERENCE
    # ========================================================

    dataset_currency = (
        _infer_dataset_currency(
            currencies=detected_currencies,
            total_rows=cleaned_rows,
        )
    )

    # ========================================================
    # SECOND PASS:
    # AMOUNT + CURRENCY + HISTORICAL FX NORMALIZATION
    # ========================================================

    original_numeric_amounts = []
    normalized_amounts_mad = []

    detected_currency_values = []
    currency_confidences = []
    currency_sources = []
    currency_conflicts = []

    conversion_applied_values = []
    normalization_statuses = []

    normalized_dates = []

    fx_rates = []
    fx_rate_dates = []
    fx_providers = []

    # ========================================================
    # QUALITY COUNTERS
    # ========================================================

    conflict_count = 0
    unknown_count = 0
    missing_fx_date_count = 0
    fx_unavailable_count = 0
    normalized_count = 0

    currency_stats: Dict[str, int] = {}

    # ========================================================
    # NORMALIZE EACH TRANSACTION
    # ========================================================

    for _, row in working_df.iterrows():

        raw_amount = row.get(
            amount_column
        )

        explicit_currency = (
            row.get(
                currency_column
            )
            if currency_column is not None
            else None
        )

        transaction_date = (
            _parse_transaction_date(
                row.get(
                    date_column
                )
            )
            if date_column is not None
            else None
        )

        result = (
            normalize_transaction_amount(
                amount_value=raw_amount,
                currency_value=explicit_currency,
                inferred_currency=dataset_currency,
                transaction_date=transaction_date,
            )
        )

        # ====================================================
        # ORIGINAL AMOUNT
        # ====================================================

        original_numeric_amounts.append(
            result.get(
                "original_amount"
            )
        )

        # ====================================================
        # NORMALIZED MAD AMOUNT
        # ====================================================

        normalized_amounts_mad.append(
            result.get(
                "normalized_amount_mad"
            )
        )

        # ====================================================
        # CURRENCY
        # ====================================================

        detected_currency = (
            result.get(
                "original_currency"
            )
            or "UNKNOWN"
        )

        detected_currency_values.append(
            detected_currency
        )

        currency_stats[
            detected_currency
        ] = (
            currency_stats.get(
                detected_currency,
                0,
            )
            + 1
        )

        currency_confidences.append(
            result.get(
                "currency_confidence",
                0.0,
            )
        )

        currency_sources.append(
            result.get(
                "currency_source"
            )
        )

        # ====================================================
        # CONFLICT
        # ====================================================

        conflict = bool(
            result.get(
                "currency_conflict",
                False,
            )
        )

        currency_conflicts.append(
            conflict
        )

        # ====================================================
        # CONVERSION
        # ====================================================

        conversion_applied_values.append(
            bool(
                result.get(
                    "conversion_applied",
                    False,
                )
            )
        )

        # ====================================================
        # NORMALIZATION STATUS
        # ====================================================

        status = str(
            result.get(
                "normalization_status",
                ""
            )
        )

        normalization_statuses.append(
            status
        )

        normalized_dates.append(
            transaction_date
        )

        # ====================================================
        # FX METADATA
        # ====================================================

        fx_rates.append(
            result.get(
                "fx_rate"
            )
        )

        fx_rate_dates.append(
            result.get(
                "fx_rate_date"
            )
        )

        fx_providers.append(
            result.get(
                "fx_provider"
            )
        )

        # ====================================================
        # QUALITY COUNTERS
        # ====================================================

        if conflict:
            conflict_count += 1

        if status == "unknown_currency":

            unknown_count += 1

        elif status == "missing_fx_date":

            missing_fx_date_count += 1

        elif status == "fx_unavailable":

            fx_unavailable_count += 1

        if (
            result.get(
                "normalized_amount_mad"
            )
            is not None
        ):

            normalized_count += 1

    # ========================================================
    # ADD INTERNAL FINGUARD COLUMNS
    # ========================================================

    working_df[
        "_original_numeric_amount"
    ] = original_numeric_amounts

    working_df[
        "_normalized_amount_mad"
    ] = normalized_amounts_mad

    working_df[
        "_detected_currency"
    ] = detected_currency_values

    working_df[
        "_currency_confidence"
    ] = currency_confidences

    working_df[
        "_currency_source"
    ] = currency_sources

    working_df[
        "_currency_conflict"
    ] = currency_conflicts

    working_df[
        "_conversion_applied"
    ] = conversion_applied_values

    working_df[
        "_currency_normalization_status"
    ] = normalization_statuses

    working_df[
        "_transaction_date_normalized"
    ] = normalized_dates

    working_df[
        "_fx_rate_to_mad"
    ] = fx_rates

    working_df[
        "_fx_rate_date"
    ] = fx_rate_dates

    working_df[
        "_fx_provider"
    ] = fx_providers

    # ========================================================
    # NORMALIZATION COVERAGE
    # ========================================================

    if cleaned_rows > 0:

        normalization_coverage = (
            normalized_count
            / cleaned_rows
        )

    else:

        normalization_coverage = 0.0

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "dataframe":
            working_df,

        # ----------------------------------------------------
        # DATASET
        # ----------------------------------------------------

        "original_rows":
            original_rows,

        "cleaned_rows":
            cleaned_rows,

        "removed_rows":
            removed_rows,

        "original_columns":
            original_columns,

        # ----------------------------------------------------
        # DETECTED COLUMNS
        # ----------------------------------------------------

        "amount_column":
            amount_column,

        "currency_column":
            currency_column,

        "date_column":
            date_column,

        "transaction_id_column":
            transaction_id_column,

        "status_column":
            status_column,

        # ----------------------------------------------------
        # CURRENCY
        # ----------------------------------------------------

        "dataset_currency":
            dataset_currency,

        "currency_stats":
            currency_stats,

        "currency_conflicts":
            conflict_count,

        "unknown_currency_rows":
            unknown_count,

        # ----------------------------------------------------
        # HISTORICAL FX
        # ----------------------------------------------------

        "fx_unavailable_rows":
            fx_unavailable_count,

        "missing_fx_date_rows":
            missing_fx_date_count,

        "normalized_currency_rows":
            normalized_count,

        "normalization_coverage":
            round(
                normalization_coverage,
                4,
            ),
    }