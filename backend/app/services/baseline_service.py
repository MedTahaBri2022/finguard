import math
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


# ============================================================
# CONSTANTS
# ============================================================

MIN_GROUP_SIZE = 10
MIN_ENTITY_SIZE = 5


# ============================================================
# HELPERS
# ============================================================

def _safe_float(
    value: Any,
) -> Optional[float]:
    try:
        if value is None:
            return None

        if pd.isna(value):
            return None

        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except Exception:
        return None


def _safe_rate(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        numerator / denominator,
        6,
    )


def _calculate_mad(
    values: pd.Series,
) -> float:
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.0

    median = float(
        values.median()
    )

    mad = float(
        np.median(
            np.abs(
                values.to_numpy()
                - median
            )
        )
    )

    return round(
        mad,
        4,
    )


def _amount_statistics(
    values: pd.Series,
) -> Dict[str, Any]:

    numeric = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    numeric = numeric[
        numeric >= 0
    ]

    if numeric.empty:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "mad": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "max": 0.0,
        }

    return {
        "count": int(
            len(numeric)
        ),

        "mean": round(
            float(
                numeric.mean()
            ),
            4,
        ),

        "median": round(
            float(
                numeric.median()
            ),
            4,
        ),

        "mad": _calculate_mad(
            numeric
        ),

        "p75": round(
            float(
                numeric.quantile(
                    0.75
                )
            ),
            4,
        ),

        "p90": round(
            float(
                numeric.quantile(
                    0.90
                )
            ),
            4,
        ),

        "p95": round(
            float(
                numeric.quantile(
                    0.95
                )
            ),
            4,
        ),

        "p99": round(
            float(
                numeric.quantile(
                    0.99
                )
            ),
            4,
        ),

        "max": round(
            float(
                numeric.max()
            ),
            4,
        ),
    }


def _normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return (
        str(value)
        .strip()
        .lower()
    )


# ============================================================
# OPERATIONAL RATES
# ============================================================

def _calculate_failure_rate(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    if "status" not in df.columns:
        return {
            "available": False,
            "failed_count": 0,
            "total_count": int(
                len(df)
            ),
            "rate": 0.0,
        }

    failed_statuses = {
        "failed",
        "failure",
        "declined",
        "rejected",
        "error",
        "cancelled",
        "canceled",
        "échec",
        "echec",
        "refused",
        "refusé",
        "refuse",
    }

    statuses = df[
        "status"
    ].apply(
        _normalize_text
    )

    failed_count = int(
        statuses.isin(
            failed_statuses
        ).sum()
    )

    total_count = int(
        len(statuses)
    )

    return {
        "available": True,
        "failed_count": failed_count,
        "total_count": total_count,
        "rate": _safe_rate(
            failed_count,
            total_count,
        ),
    }


def _calculate_refund_rate(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    refund_mask = pd.Series(
        False,
        index=df.index,
    )

    available = False

    if "transaction_type" in df.columns:
        available = True

        types = df[
            "transaction_type"
        ].apply(
            _normalize_text
        )

        refund_mask = (
            refund_mask
            | types.str.contains(
                r"\brefund\b",
                regex=True,
                na=False,
            )
            | types.str.contains(
                "rembourse",
                regex=False,
                na=False,
            )
        )

    if "category" in df.columns:
        available = True

        categories = df[
            "category"
        ].apply(
            _normalize_text
        )

        refund_mask = (
            refund_mask
            | categories.str.contains(
                r"\brefund\b",
                regex=True,
                na=False,
            )
            | categories.str.contains(
                "rembourse",
                regex=False,
                na=False,
            )
        )

    refund_count = int(
        refund_mask.sum()
    )

    total_count = int(
        len(df)
    )

    return {
        "available": available,
        "refund_count": refund_count,
        "total_count": total_count,
        "rate": _safe_rate(
            refund_count,
            total_count,
        ),
    }


# ============================================================
# CATEGORY BASELINES
# ============================================================

def _build_category_baselines(
    df: pd.DataFrame,
    amount_column: str,
) -> Dict[str, Any]:

    if "category" not in df.columns:
        return {}

    output: Dict[str, Any] = {}

    category_values = (
        df["category"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    working = df.copy()

    working[
        "_baseline_category"
    ] = category_values

    working = working[
        working[
            "_baseline_category"
        ]
        != ""
    ]

    for category, group in working.groupby(
        "_baseline_category"
    ):

        if len(group) < MIN_GROUP_SIZE:
            continue

        stats = _amount_statistics(
            group[
                amount_column
            ]
        )

        output[
            str(category)
        ] = stats

    return output


# ============================================================
# MERCHANT / VENDOR BASELINES
# ============================================================

def _build_merchant_baselines(
    df: pd.DataFrame,
    amount_column: str,
) -> Dict[str, Any]:
    """
    Build historical amount statistics
    for each merchant/vendor.

    This allows FinGuard to learn that
    an amount can be normal for one supplier
    but abnormal for another supplier.
    """

    if "merchant" not in df.columns:
        return {}

    output: Dict[str, Any] = {}

    working = df.copy()

    working[
        "_baseline_merchant"
    ] = (
        working[
            "merchant"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    working = working[
        working[
            "_baseline_merchant"
        ]
        != ""
    ]

    for merchant, group in working.groupby(
        "_baseline_merchant"
    ):

        if len(group) < MIN_GROUP_SIZE:
            continue

        stats = _amount_statistics(
            group[
                amount_column
            ]
        )

        output[
            str(merchant)
        ] = stats

    return output


# ============================================================
# TRANSACTION TYPE BASELINES
# ============================================================

def _build_type_baselines(
    df: pd.DataFrame,
    amount_column: str,
) -> Dict[str, Any]:

    if "transaction_type" not in df.columns:
        return {}

    output: Dict[str, Any] = {}

    working = df.copy()

    working[
        "_baseline_type"
    ] = (
        working[
            "transaction_type"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    working = working[
        working[
            "_baseline_type"
        ]
        != ""
    ]

    for tx_type, group in working.groupby(
        "_baseline_type"
    ):

        if len(group) < MIN_GROUP_SIZE:
            continue

        output[
            str(tx_type)
        ] = _amount_statistics(
            group[
                amount_column
            ]
        )

    return output


# ============================================================
# ENTITY / ACCOUNT BASELINES
# ============================================================

def _build_entity_baselines(
    df: pd.DataFrame,
    amount_column: str,
) -> Dict[str, Any]:

    if "entity_id" not in df.columns:
        return {}

    output: Dict[str, Any] = {}

    working = df.copy()

    working[
        "_baseline_entity"
    ] = (
        working[
            "entity_id"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    working = working[
        working[
            "_baseline_entity"
        ]
        != ""
    ]

    for entity_id, group in working.groupby(
        "_baseline_entity"
    ):

        if len(group) < MIN_ENTITY_SIZE:
            continue

        amount_stats = _amount_statistics(
            group[
                amount_column
            ]
        )

        total_amount = pd.to_numeric(
            group[
                amount_column
            ],
            errors="coerce",
        ).fillna(
            0.0
        ).sum()

        output[
            str(entity_id)
        ] = {
            **amount_stats,

            "total_amount": round(
                float(
                    total_amount
                ),
                4,
            ),
        }

    return output


# ============================================================
# TEMPORAL BASELINE
# ============================================================

def _build_temporal_baseline(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    date_column = None

    if (
        "_transaction_date_normalized"
        in df.columns
    ):
        date_column = (
            "_transaction_date_normalized"
        )

    elif "timestamp" in df.columns:
        date_column = "timestamp"

    if date_column is None:
        return {
            "available": False,
        }

    dates = pd.to_datetime(
        df[
            date_column
        ],
        errors="coerce",
    ).dropna()

    if dates.empty:
        return {
            "available": False,
        }

    hours = dates.dt.hour

    weekdays = dates.dt.dayofweek

    hour_distribution = (
        hours.value_counts(
            normalize=True
        )
        .sort_index()
    )

    weekday_distribution = (
        weekdays.value_counts(
            normalize=True
        )
        .sort_index()
    )

    return {
        "available": True,

        "hour_distribution": {
            str(int(hour)): round(
                float(rate),
                6,
            )
            for hour, rate
            in hour_distribution.items()
        },

        "weekday_distribution": {
            str(int(day)): round(
                float(rate),
                6,
            )
            for day, rate
            in weekday_distribution.items()
        },
    }


# ============================================================
# CURRENCY QUALITY BASELINE
# ============================================================

def _build_currency_quality(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    total = int(
        len(df)
    )

    if total <= 0:
        return {
            "normalization_coverage": 0.0,
            "conflict_rate": 0.0,
            "unknown_rate": 0.0,
        }

    normalized_count = 0

    if (
        "_normalized_amount_mad"
        in df.columns
    ):
        normalized_count = int(
            df[
                "_normalized_amount_mad"
            ]
            .notna()
            .sum()
        )

    conflict_count = 0

    if (
        "_currency_conflict"
        in df.columns
    ):
        conflict_count = int(
            df[
                "_currency_conflict"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

    unknown_count = 0

    if (
        "_currency_normalization_status"
        in df.columns
    ):
        unknown_count = int(
            (
                df[
                    "_currency_normalization_status"
                ]
                == "unknown_currency"
            ).sum()
        )

    return {
        "normalization_coverage": (
            round(
                normalized_count
                / total,
                6,
            )
        ),

        "conflict_rate": (
            round(
                conflict_count
                / total,
                6,
            )
        ),

        "unknown_rate": (
            round(
                unknown_count
                / total,
                6,
            )
        ),
    }


# ============================================================
# MAIN BASELINE BUILDER
# ============================================================

def build_client_baseline(
    df: pd.DataFrame,
    minimum_history_rows: int = 100,
) -> Dict[str, Any]:
    """
    Build a statistical historical baseline
    for one FinGuard client.

    Expected dataframe:
    already mapped to canonical schema
    and already cleaned by data_cleaner.
    """

    if df is None:
        raise ValueError(
            "Historical dataframe is missing."
        )

    if df.empty:
        raise ValueError(
            "Historical dataframe is empty."
        )

    # --------------------------------------------------------
    # SELECT NORMALIZED AMOUNT
    # --------------------------------------------------------

    amount_column = None

    if (
        "_normalized_amount_mad"
        in df.columns
    ):
        amount_column = (
            "_normalized_amount_mad"
        )

    elif "amount" in df.columns:
        amount_column = "amount"

    if amount_column is None:
        raise ValueError(
            "No amount column is available "
            "for baseline calculation."
        )

    numeric_amounts = pd.to_numeric(
        df[
            amount_column
        ],
        errors="coerce",
    )

    valid_amount_rows = int(
        numeric_amounts.notna().sum()
    )

    if valid_amount_rows == 0:
        raise ValueError(
            "Historical dataset does not "
            "contain valid numeric amounts."
        )

    sample_size = int(
        len(df)
    )

    # --------------------------------------------------------
    # GLOBAL AMOUNT BASELINE
    # --------------------------------------------------------

    amount_stats = _amount_statistics(
        numeric_amounts
    )

    # --------------------------------------------------------
    # OPERATIONAL BASELINES
    # --------------------------------------------------------

    failure = _calculate_failure_rate(
        df
    )

    refund = _calculate_refund_rate(
        df
    )

    # --------------------------------------------------------
    # CONTEXT BASELINES
    # --------------------------------------------------------

    categories = (
        _build_category_baselines(
            df=df,
            amount_column=amount_column,
        )
    )

    merchants = (
        _build_merchant_baselines(
            df=df,
            amount_column=amount_column,
        )
    )

    transaction_types = (
        _build_type_baselines(
            df=df,
            amount_column=amount_column,
        )
    )

    entities = (
        _build_entity_baselines(
            df=df,
            amount_column=amount_column,
        )
    )

    temporal = (
        _build_temporal_baseline(
            df
        )
    )

    currency_quality = (
        _build_currency_quality(
            df
        )
    )

    # --------------------------------------------------------
    # READINESS
    # --------------------------------------------------------

    enough_rows = (
        sample_size
        >= minimum_history_rows
    )

    normalization_good = (
        currency_quality[
            "normalization_coverage"
        ]
        >= 0.90
    )

    baseline_ready = bool(
        enough_rows
        and normalization_good
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    baseline = {
        "schema_version": 2,

        "sample_size": sample_size,

        "valid_amount_rows": (
            valid_amount_rows
        ),

        "amount_column": (
            amount_column
        ),

        "amount": amount_stats,

        "operational": {
            "failure": failure,
            "refund": refund,
        },

        "categories": (
            categories
        ),

        "merchants": (
            merchants
        ),

        "transaction_types": (
            transaction_types
        ),

        "entities": (
            entities
        ),

        "temporal": (
            temporal
        ),

        "currency_quality": (
            currency_quality
        ),

        "readiness": {
            "minimum_history_rows": (
                int(
                    minimum_history_rows
                )
            ),

            "enough_rows": (
                enough_rows
            ),

            "normalization_good": (
                normalization_good
            ),

            "baseline_ready": (
                baseline_ready
            ),
        },
    }

    return baseline