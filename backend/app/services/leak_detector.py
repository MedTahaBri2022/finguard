import math
from collections import defaultdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


# ============================================================
# FinGuard Risk Detector V5.0 Architectural Correction
# Context Override + Semantic Risk Detection + Tail Protection
# ============================================================

ENGINE_VERSION = "5.0-architectural-correction"
BASE_CURRENCY = "MAD"


# ============================================================
# Context maturity
# ============================================================

MIN_HISTORICAL_MERCHANT_COUNT = 10
MIN_HISTORICAL_CATEGORY_COUNT = 30
MIN_HISTORICAL_TRANSACTION_TYPE_COUNT = 30
MIN_HISTORICAL_ENTITY_COUNT = 25

MIN_BATCH_MERCHANT_COUNT = 10
MIN_BATCH_CATEGORY_COUNT = 20
MIN_BATCH_TRANSACTION_TYPE_COUNT = 20
MIN_BATCH_ENTITY_COUNT = 12


# ============================================================
# Historical contextual shrinkage
# ============================================================

CONTEXT_PRIOR_STRENGTH = 50.0


# ============================================================
# Robust anomaly thresholds
#
# Kept from previous architecture family.
# V4.6 does NOT tune these against V5.
# ============================================================

STRONG_Z = 5.0
EXTREME_Z = 8.0
MIN_MEDIAN_RATIO = 2.5


# ============================================================
# ML support
# ============================================================

ML_SUPPORT_THRESHOLD = 0.80
ML_STRONG_THRESHOLD = 0.92


# ============================================================
# Economic materiality
#
# IMPORTANT V4.6 CHANGE:
#
# Materiality is derived from historical/business behavior.
# Current-batch p95 is NOT allowed to become a hard floor.
# ============================================================

MATERIALITY_P95_MULTIPLIER = 2.0
MATERIALITY_MEDIAN_MULTIPLIER = 5.5

LARGE_AMOUNT_MULTIPLIER = 1.75


# ============================================================
# Current-batch robust reference
# ============================================================

BATCH_REFERENCE_UPPER_QUANTILE = 0.98

MIN_BATCH_REFERENCE_ROWS = 30
MIN_BATCH_CONTEXT_REFERENCE_ROWS = 12


# ============================================================
# Drift telemetry
#
# Drift itself is not a finding.
# ============================================================

DRIFT_MEDIAN_RATIO = 1.75
DRIFT_DISPERSION_RATIO = 1.75


# ============================================================
# General helpers
# ============================================================


def _safe_float(
    value: Any,
    default: Optional[float] = None,
) -> Optional[float]:

    try:

        if value is None:
            return default

        if pd.isna(value):
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except Exception:
        return default


def _safe_text(
    value: Any,
) -> Optional[str]:

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    text = str(value).strip()

    if not text:
        return None

    return text


def _normalize_text(
    value: Any,
) -> str:

    text = _safe_text(value)

    if not text:
        return ""

    return text.lower().strip()


def _ratio(
    numerator: Optional[float],
    denominator: Optional[float],
) -> Optional[float]:

    if numerator is None:
        return None

    if denominator is None:
        return None

    if denominator <= 0:
        return None

    return numerator / denominator


def _transaction_id(
    row: pd.Series,
    fallback_index: int,
) -> str:

    value = _safe_text(
        row.get("transaction_id")
    )

    if value:
        return value

    return f"row_{fallback_index}"


def _normalized_amount(
    row: pd.Series,
) -> Optional[float]:

    for column in [
        "_normalized_amount_mad",
        "amount",
    ]:

        if column not in row.index:
            continue

        value = _safe_float(
            row.get(column)
        )

        if value is not None:
            return value

    return None


def _baseline_section(
    baseline: Optional[Dict[str, Any]],
    key: str,
) -> Dict[str, Any]:

    if not baseline:
        return {}

    value = baseline.get(key)

    if isinstance(value, dict):
        return value

    return {}


def _find_context_stats(
    section: Dict[str, Any],
    key: Optional[str],
) -> Dict[str, Any]:

    if not section:
        return {}

    if not key:
        return {}

    direct = section.get(key)

    if isinstance(direct, dict):
        return direct

    normalized_key = _normalize_text(key)

    for candidate_key, value in section.items():

        if (
            _normalize_text(candidate_key)
            == normalized_key
            and isinstance(value, dict)
        ):
            return value

    return {}


# ============================================================
# Robust statistics
# ============================================================


def _calculate_mad(
    values: np.ndarray,
    median: float,
) -> float:

    if len(values) == 0:
        return 0.0

    return float(
        np.median(
            np.abs(
                values - median
            )
        )
    )


def _stats_from_values(
    values: List[float],
    trim_upper_tail: bool = False,
) -> Dict[str, Any]:

    clean_values: List[float] = []

    for value in values:

        safe_value = _safe_float(value)

        if safe_value is None:
            continue

        if safe_value < 0:
            continue

        clean_values.append(
            safe_value
        )

    clean = np.asarray(
        clean_values,
        dtype=float,
    )

    if len(clean) == 0:

        return {
            "count": 0,
            "reference_count": 0,
            "median": None,
            "mad": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
        }

    full_count = len(clean)

    reference = clean

    if (
        trim_upper_tail
        and len(clean)
        >= MIN_BATCH_REFERENCE_ROWS
    ):

        cutoff = float(
            np.quantile(
                clean,
                BATCH_REFERENCE_UPPER_QUANTILE,
            )
        )

        candidate = clean[
            clean <= cutoff
        ]

        if len(candidate) >= 20:
            reference = candidate

    median = float(
        np.median(reference)
    )

    mad = _calculate_mad(
        reference,
        median,
    )

    return {
        "count": int(full_count),
        "reference_count": int(
            len(reference)
        ),
        "median": median,
        "mad": mad,
        "p75": float(
            np.quantile(
                reference,
                0.75,
            )
        ),
        "p90": float(
            np.quantile(
                reference,
                0.90,
            )
        ),
        "p95": float(
            np.quantile(
                reference,
                0.95,
            )
        ),
        "p99": float(
            np.quantile(
                reference,
                0.99,
            )
        ),
        "max": float(
            np.max(reference)
        ),
    }


def _robust_z(
    amount: float,
    median: Optional[float],
    mad: Optional[float],
) -> Optional[float]:

    if median is None:
        return None

    if mad is None:
        return None

    if mad <= 0:
        return None

    return (
        0.6745
        * (
            amount - median
        )
        / mad
    )


def _classify_distribution(
    amount: float,
    median: Optional[float],
    mad: Optional[float],
) -> Dict[str, Any]:

    z_score = _robust_z(
        amount,
        median,
        mad,
    )

    median_ratio = _ratio(
        amount,
        median,
    )

    strong = False
    extreme = False

    if (
        z_score is not None
        and median_ratio is not None
        and z_score >= EXTREME_Z
        and median_ratio >= MIN_MEDIAN_RATIO
    ):

        strong = True
        extreme = True

    elif (
        z_score is not None
        and median_ratio is not None
        and z_score >= STRONG_Z
        and median_ratio >= MIN_MEDIAN_RATIO
    ):

        strong = True

    return {
        "robust_z": (
            round(z_score, 4)
            if z_score is not None
            else None
        ),
        "median_ratio": (
            round(median_ratio, 4)
            if median_ratio is not None
            else None
        ),
        "strong": strong,
        "extreme": extreme,
    }


# ============================================================
# Historical global reference
# ============================================================


def _historical_global_stats(
    baseline: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    section = _baseline_section(
        baseline,
        "amount",
    )

    return {
        "count": int(
            section.get("count")
            or 0
        ),
        "reference_count": int(
            section.get("count")
            or 0
        ),
        "median": _safe_float(
            section.get("median")
        ),
        "mad": _safe_float(
            section.get("mad")
        ),
        "p75": _safe_float(
            section.get("p75")
        ),
        "p90": _safe_float(
            section.get("p90")
        ),
        "p95": _safe_float(
            section.get("p95")
        ),
        "p99": _safe_float(
            section.get("p99")
        ),
        "max": _safe_float(
            section.get("max")
        ),
    }


# ============================================================
# Current-batch reference
# ============================================================


def _build_batch_reference(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    global_values: List[float] = []

    merchant_values: Dict[str, List[float]] = defaultdict(list)
    category_values: Dict[str, List[float]] = defaultdict(list)
    transaction_type_values: Dict[str, List[float]] = defaultdict(list)
    entity_values: Dict[str, List[float]] = defaultdict(list)

    for _, row in df.iterrows():
        amount = _normalized_amount(row)

        if amount is None or amount < 0:
            continue

        global_values.append(amount)

        merchant = _normalize_text(row.get("merchant"))
        if merchant:
            merchant_values[merchant].append(amount)

        category = _normalize_text(row.get("category"))
        if category:
            category_values[category].append(amount)

        transaction_type = _normalize_text(row.get("transaction_type"))
        if transaction_type:
            transaction_type_values[transaction_type].append(amount)

        entity_id = _normalize_text(row.get("entity_id"))
        if entity_id:
            entity_values[entity_id].append(amount)

    global_stats = _stats_from_values(
        global_values,
        trim_upper_tail=True,
    )

    def build_group_stats(
        groups: Dict[str, List[float]],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for key, values in groups.items():
            if len(values) < MIN_BATCH_CONTEXT_REFERENCE_ROWS:
                continue

            result[key] = _stats_from_values(
                values,
                trim_upper_tail=True,
            )

        return result

    return {
        "amount": global_stats,
        "merchants": build_group_stats(merchant_values),
        "categories": build_group_stats(category_values),
        "transaction_types": build_group_stats(transaction_type_values),
        "entities": build_group_stats(entity_values),
    }


# ============================================================
# Economic materiality
# ============================================================


def _historical_materiality(
    historical_stats: Dict[str, Any],
) -> Dict[str, Any]:

    median = _safe_float(
        historical_stats.get(
            "median"
        )
    )

    p95 = _safe_float(
        historical_stats.get(
            "p95"
        )
    )

    p95_component = None
    median_component = None

    candidates: List[float] = []

    if p95 is not None:

        p95_component = (
            p95
            * MATERIALITY_P95_MULTIPLIER
        )

        candidates.append(
            p95_component
        )

    if median is not None:

        median_component = (
            median
            * MATERIALITY_MEDIAN_MULTIPLIER
        )

        candidates.append(
            median_component
        )

    normal_floor = (
        max(candidates)
        if candidates
        else None
    )

    large_floor = None

    if normal_floor is not None:

        large_floor = (
            normal_floor
            * LARGE_AMOUNT_MULTIPLIER
        )

    return {
        "normal_floor": normal_floor,
        "large_floor": large_floor,
        "p95_component": p95_component,
        "median_component": (
            median_component
        ),
    }


# ============================================================
# Historical global evidence
# ============================================================


def _historical_global_evidence(
    amount: float,
    baseline: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    stats = _historical_global_stats(
        baseline
    )

    distribution = (
        _classify_distribution(
            amount,
            stats.get("median"),
            stats.get("mad"),
        )
    )

    above_p99 = bool(
        stats.get("p99") is not None
        and amount > stats["p99"]
    )

    signals: List[str] = []

    if distribution["extreme"]:

        signals.append(
            "extreme_historical_global"
        )

    elif distribution["strong"]:

        signals.append(
            "strong_historical_global"
        )

    if above_p99:

        signals.append(
            "above_historical_p99"
        )

    return {
        "available": bool(
            stats.get("count", 0) > 0
            and stats.get("median")
            is not None
        ),
        **stats,
        **distribution,
        "above_p99": above_p99,
        "signals": signals,
    }


# ============================================================
# Current batch global rarity
# ============================================================


def _batch_global_evidence(
    amount: float,
    batch_reference: Dict[str, Any],
) -> Dict[str, Any]:

    stats = batch_reference.get(
        "amount",
        {},
    )

    distribution = (
        _classify_distribution(
            amount,
            _safe_float(
                stats.get("median")
            ),
            _safe_float(
                stats.get("mad")
            ),
        )
    )

    p95 = _safe_float(
        stats.get("p95")
    )

    p99 = _safe_float(
        stats.get("p99")
    )

    above_p95 = bool(
        p95 is not None
        and amount > p95
    )

    above_p99 = bool(
        p99 is not None
        and amount > p99
    )

    signals: List[str] = []

    if distribution["extreme"]:

        signals.append(
            "extreme_batch_global"
        )

    elif distribution["strong"]:

        signals.append(
            "strong_batch_global"
        )

    if above_p99:

        signals.append(
            "above_batch_p99"
        )

    elif above_p95:

        signals.append(
            "above_batch_p95"
        )

    return {
        "available": bool(
            stats.get(
                "reference_count",
                0,
            )
            >= MIN_BATCH_REFERENCE_ROWS
            and stats.get("median")
            is not None
        ),
        **stats,
        **distribution,
        "above_p95": above_p95,
        "above_p99": above_p99,
        "signals": signals,
    }


# ============================================================
# Historical contextual shrinkage
# ============================================================


def _shrink_historical_context(
    context_stats: Dict[str, Any],
    global_stats: Dict[str, Any],
) -> Dict[str, Any]:

    count = int(
        context_stats.get(
            "count"
        )
        or 0
    )

    local_median = _safe_float(
        context_stats.get(
            "median"
        )
    )

    local_mad = _safe_float(
        context_stats.get(
            "mad"
        )
    )

    global_median = _safe_float(
        global_stats.get(
            "median"
        )
    )

    global_mad = _safe_float(
        global_stats.get(
            "mad"
        )
    )

    reliability = (
        count
        / (
            count
            + CONTEXT_PRIOR_STRENGTH
        )
        if count > 0
        else 0.0
    )

    if (
        local_median is not None
        and global_median is not None
    ):

        adjusted_median = (
            reliability
            * local_median
            + (
                1.0
                - reliability
            )
            * global_median
        )

    else:

        adjusted_median = (
            local_median
            if local_median is not None
            else global_median
        )

    if (
        local_mad is not None
        and global_mad is not None
    ):

        adjusted_mad = (
            reliability
            * local_mad
            + (
                1.0
                - reliability
            )
            * global_mad
        )

    else:

        adjusted_mad = (
            local_mad
            if local_mad is not None
            else global_mad
        )

    return {
        "count": count,
        "reliability": round(
            reliability,
            4,
        ),
        "raw_median": local_median,
        "raw_mad": local_mad,
        "median": adjusted_median,
        "mad": adjusted_mad,
        "p95": _safe_float(
            context_stats.get(
                "p95"
            )
        ),
        "p99": _safe_float(
            context_stats.get(
                "p99"
            )
        ),
        "max": _safe_float(
            context_stats.get(
                "max"
            )
        ),
    }


# ============================================================
# Historical contextual evidence
# ============================================================


def _historical_context_evidence(
    amount: float,
    key: Optional[str],
    section_name: str,
    minimum_count: int,
    baseline: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    empty = {
        "available": False,
        "mature": False,
        "strong": False,
        "extreme": False,
        "above_p95": False,
        "above_p99": False,
        "normal_tail": False,
        "signals": [],
    }

    if not key:
        return empty

    section = _baseline_section(baseline, section_name)
    raw_stats = _find_context_stats(section, key)

    if not raw_stats:
        return {**empty, "key": key}

    global_stats = _historical_global_stats(baseline)
    stats = _shrink_historical_context(raw_stats, global_stats)
    mature = bool(stats["count"] >= minimum_count)

    distribution = _classify_distribution(
        amount,
        stats.get("median"),
        stats.get("mad"),
    )

    p95 = _safe_float(stats.get("p95"))
    p99 = _safe_float(stats.get("p99"))
    above_p95 = bool(mature and p95 is not None and amount > p95)
    above_p99 = bool(mature and p99 is not None and amount > p99)

    strong = bool(mature and distribution["strong"])
    extreme = bool(mature and distribution["extreme"])

    # A mature context may have a legitimate high-value tail.  We treat
    # this as protective evidence only when the amount remains inside the
    # historically observed range and is not an extreme robust deviation.
    # It is evidence, not a universal threshold and never creates a finding.
    historical_max = _safe_float(stats.get("max"))
    normal_tail = bool(
        mature
        and p95 is not None
        and amount > p95
        and historical_max is not None
        and amount <= historical_max
        and not extreme
    )

    label = (
        section_name
        .replace("transaction_types", "transaction_type")
        .replace("categories", "category")
        .replace("merchants", "merchant")
        .replace("entities", "entity")
    )

    signals: List[str] = []
    if extreme:
        signals.append(f"extreme_historical_{label}")
    elif strong:
        signals.append(f"strong_historical_{label}")

    if above_p99:
        signals.append(f"above_historical_{label}_p99")
    elif above_p95:
        signals.append(f"above_historical_{label}_p95")

    if normal_tail:
        signals.append(f"historical_{label}_normal_tail")

    return {
        "available": True,
        "mature": mature,
        "key": key,
        **stats,
        "robust_z": distribution["robust_z"],
        "median_ratio": distribution["median_ratio"],
        "strong": strong,
        "extreme": extreme,
        "above_p95": above_p95,
        "above_p99": above_p99,
        "normal_tail": normal_tail,
        "signals": signals,
    }


# ============================================================
# Batch contextual evidence
# ============================================================


def _batch_context_evidence(
    amount: float,
    key: Optional[str],
    section_name: str,
    minimum_count: int,
    batch_reference: Dict[str, Any],
) -> Dict[str, Any]:

    empty = {
        "available": False,
        "mature": False,
        "strong": False,
        "extreme": False,
        "above_p95": False,
        "above_p99": False,
        "signals": [],
    }

    if not key:
        return empty

    section = batch_reference.get(section_name, {})
    normalized_key = _normalize_text(key)
    stats = section.get(normalized_key)

    if not isinstance(stats, dict):
        return {**empty, "key": key}

    count = int(stats.get("count") or 0)
    mature = bool(count >= minimum_count)

    distribution = _classify_distribution(
        amount,
        _safe_float(stats.get("median")),
        _safe_float(stats.get("mad")),
    )

    p95 = _safe_float(stats.get("p95"))
    p99 = _safe_float(stats.get("p99"))
    above_p95 = bool(mature and p95 is not None and amount > p95)
    above_p99 = bool(mature and p99 is not None and amount > p99)

    strong = bool(mature and distribution["strong"])
    extreme = bool(mature and distribution["extreme"])

    label = (
        section_name
        .replace("transaction_types", "transaction_type")
        .replace("categories", "category")
        .replace("merchants", "merchant")
        .replace("entities", "entity")
    )

    signals: List[str] = []
    if extreme:
        signals.append(f"extreme_batch_{label}")
    elif strong:
        signals.append(f"strong_batch_{label}")

    if above_p99:
        signals.append(f"above_batch_{label}_p99")
    elif above_p95:
        signals.append(f"above_batch_{label}_p95")

    return {
        "available": True,
        "mature": mature,
        "key": key,
        **stats,
        "robust_z": distribution["robust_z"],
        "median_ratio": distribution["median_ratio"],
        "strong": strong,
        "extreme": extreme,
        "above_p95": above_p95,
        "above_p99": above_p99,
        "signals": signals,
    }


# ============================================================
# Isolation Forest
# ============================================================


def _isolation_scores(
    df: pd.DataFrame,
) -> Dict[int, float]:

    features: List[
        List[float]
    ] = []

    indexes: List[int] = []

    for position, (_, row) in enumerate(
        df.iterrows()
    ):

        amount = _normalized_amount(
            row
        )

        if amount is None:
            continue

        features.append(
            [
                math.log1p(
                    max(
                        amount,
                        0.0,
                    )
                )
            ]
        )

        indexes.append(
            position
        )

    if len(features) < 20:
        return {}

    X = np.asarray(
        features,
        dtype=float,
    )

    try:

        model = IsolationForest(
            n_estimators=250,
            contamination="auto",
            random_state=42,
        )

        model.fit(X)

        raw_scores = (
            -model.score_samples(X)
        )

        minimum = float(
            raw_scores.min()
        )

        maximum = float(
            raw_scores.max()
        )

        result: Dict[
            int,
            float,
        ] = {}

        for position, raw_score in zip(
            indexes,
            raw_scores,
        ):

            if maximum > minimum:

                score = (
                    float(raw_score)
                    - minimum
                ) / (
                    maximum
                    - minimum
                )

            else:
                score = 0.0

            result[position] = round(
                score,
                4,
            )

        return result

    except Exception:
        return {}


# ============================================================
# Drift
# ============================================================


def _drift_metrics(
    historical_stats: Dict[str, Any],
    batch_stats: Dict[str, Any],
) -> Dict[str, Any]:

    historical_median = _safe_float(
        historical_stats.get(
            "median"
        )
    )

    batch_median = _safe_float(
        batch_stats.get(
            "median"
        )
    )

    historical_mad = _safe_float(
        historical_stats.get(
            "mad"
        )
    )

    batch_mad = _safe_float(
        batch_stats.get(
            "mad"
        )
    )

    median_ratio = None
    dispersion_ratio = None

    if (
        historical_median is not None
        and historical_median > 0
        and batch_median is not None
    ):

        median_ratio = (
            batch_median
            / historical_median
        )

    if (
        historical_mad is not None
        and historical_mad > 0
        and batch_mad is not None
    ):

        dispersion_ratio = (
            batch_mad
            / historical_mad
        )

    upward_median_shift = bool(
        median_ratio is not None
        and median_ratio
        >= DRIFT_MEDIAN_RATIO
    )

    dispersion_shift = bool(
        dispersion_ratio is not None
        and dispersion_ratio
        >= DRIFT_DISPERSION_RATIO
    )

    return {
        "distribution_shift_detected": bool(
            upward_median_shift
            or dispersion_shift
        ),
        "upward_median_shift": (
            upward_median_shift
        ),
        "dispersion_shift": (
            dispersion_shift
        ),
        "historical_median": (
            historical_median
        ),
        "batch_median": (
            batch_median
        ),
        "median_shift_ratio": (
            round(
                median_ratio,
                4,
            )
            if median_ratio is not None
            else None
        ),
        "historical_mad": (
            historical_mad
        ),
        "batch_mad": (
            batch_mad
        ),
        "dispersion_shift_ratio": (
            round(
                dispersion_ratio,
                4,
            )
            if dispersion_ratio is not None
            else None
        ),
    }


# ============================================================
# Baseline trust
#
# A historical baseline is business memory, not an immutable truth.
# Trust is reduced when the current business distribution has moved
# materially away from the historical regime. Drift itself never
# creates a finding.
# ============================================================


def _baseline_trust(
    historical_stats: Dict[str, Any],
    batch_stats: Dict[str, Any],
    drift: Dict[str, Any],
) -> Dict[str, Any]:

    historical_count = int(
        historical_stats.get("count") or 0
    )
    batch_count = int(
        batch_stats.get("reference_count") or 0
    )

    if historical_count <= 0:
        return {
            "score": 0.0,
            "level": "unavailable",
            "historical_primary": False,
            "reason": "no_historical_baseline",
        }

    median_ratio = _safe_float(
        drift.get("median_shift_ratio")
    )
    dispersion_ratio = _safe_float(
        drift.get("dispersion_shift_ratio")
    )

    # Small historical samples are useful, but should not dominate
    # a mature current batch. This is a reliability adjustment, not
    # an anomaly threshold.
    sample_reliability = min(
        1.0,
        historical_count / 500.0,
    )

    severe_median_shift = bool(
        median_ratio is not None
        and median_ratio >= 3.0
    )
    severe_dispersion_shift = bool(
        dispersion_ratio is not None
        and dispersion_ratio >= 3.0
    )

    moderate_median_shift = bool(
        median_ratio is not None
        and median_ratio >= DRIFT_MEDIAN_RATIO
    )
    moderate_dispersion_shift = bool(
        dispersion_ratio is not None
        and dispersion_ratio >= DRIFT_DISPERSION_RATIO
    )

    if severe_median_shift and severe_dispersion_shift:
        regime_score = 0.25
        level = "low"
        reason = "major_location_and_dispersion_shift"

    elif severe_median_shift or severe_dispersion_shift:
        regime_score = 0.45
        level = "low"
        reason = "major_distribution_shift"

    elif moderate_median_shift and moderate_dispersion_shift:
        regime_score = 0.60
        level = "moderate"
        reason = "location_and_dispersion_shift"

    elif moderate_median_shift or moderate_dispersion_shift:
        regime_score = 0.75
        level = "moderate"
        reason = "partial_distribution_shift"

    else:
        regime_score = 0.95
        level = "high"
        reason = "historical_regime_representative"

    # Do not let a tiny current batch downgrade a historical baseline
    # aggressively; current-batch evidence is not mature enough yet.
    if batch_count < MIN_BATCH_REFERENCE_ROWS:
        regime_score = max(regime_score, 0.75)
        level = "moderate"
        reason = "current_batch_too_small_for_strong_drift_judgement"

    score = round(
        regime_score * sample_reliability,
        4,
    )

    if score >= 0.75:
        effective_level = "high"
    elif score >= 0.45:
        effective_level = "moderate"
    else:
        effective_level = "low"

    return {
        "score": score,
        "level": effective_level,
        "historical_primary": bool(score >= 0.45),
        "reason": reason,
        "historical_sample_size": historical_count,
        "current_reference_size": batch_count,
        "sample_reliability": round(sample_reliability, 4),
    }


def _business_context_family(
    merchant_evidence: Dict[str, Any],
    category_evidence: Dict[str, Any],
    type_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Use the most specific mature business context.

    Merchant/vendor behavior is most specific, then category. A generic
    transaction type is only a fallback. This is intentionally business-led
    rather than global-distribution-led.
    """

    for name, evidence in [
        ("merchant", merchant_evidence),
        ("category", category_evidence),
        ("transaction_type", type_evidence),
    ]:
        if evidence.get("mature"):
            return {
                "name": name,
                "strong": bool(evidence.get("strong")),
                "extreme": bool(evidence.get("extreme")),
                "above_p95": bool(evidence.get("above_p95")),
                "above_p99": bool(evidence.get("above_p99")),
                "available": True,
            }

    return {
        "name": None,
        "strong": False,
        "extreme": False,
        "above_p95": False,
        "above_p99": False,
        "available": False,
    }


def _contextual_contradiction(
    merchant_evidence: Dict[str, Any],
    category_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Identify strong evidence that an amount is normal in its business context.

    A mature merchant is the preferred contradiction source. If merchant
    history is unavailable, a mature category can provide the contradiction.
    We only call it normal when the amount is neither a robust anomaly nor
    above that context's p99. This prevents generic global/entity rarity from
    overriding a stable supplier/category pattern.
    """

    for name, evidence in [
        ("merchant", merchant_evidence),
        ("category", category_evidence),
    ]:
        if not evidence.get("mature"):
            continue

        normal = bool(
            not evidence.get("strong")
            and not evidence.get("extreme")
            and not evidence.get("above_p99")
        )

        return {
            "available": True,
            "source": name,
            "normal": normal,
        }

    return {
        "available": False,
        "source": None,
        "normal": False,
    }


# ============================================================
# Architectural correction: contextual override / tail protection
# ============================================================


def _context_materiality_override(
    historical_evidence: Dict[str, Any],
    batch_evidence: Dict[str, Any],
    *,
    historical_primary: bool,
    ml_support: bool,
) -> bool:
    """Allow specific merchant/category evidence to bypass global materiality.

    Materiality is company-wide evidence, not an absolute veto.  A specific
    business context can override it through either of two general paths:

    1) dual-reference agreement: the same mature historical and batch context
       are both anomalous, with at least one side extreme; or
    2) trusted-history agreement: a trusted historical context is itself an
       extreme/upper-tail anomaly and is corroborated by either current-context
       evidence or independent ML support.

    A historical normal-tail pattern can never create an override.
    """

    if historical_evidence.get("normal_tail"):
        return False

    historical_mature = bool(historical_evidence.get("mature"))
    batch_mature = bool(batch_evidence.get("mature"))

    historical_strong = bool(
        historical_evidence.get("strong")
        or historical_evidence.get("extreme")
    )
    batch_strong = bool(
        batch_evidence.get("strong")
        or batch_evidence.get("extreme")
    )

    # Path A: two independent contextual references agree.
    if (
        historical_mature
        and batch_mature
        and historical_strong
        and batch_strong
        and (
            historical_evidence.get("extreme")
            or batch_evidence.get("extreme")
        )
    ):
        return True

    # Path B: a representative historical baseline provides a strong specific
    # context signal.  This is especially important for small/current batches
    # where the local merchant/category reference may not yet be mature.
    historical_specific_tail = bool(
        historical_mature
        and (
            historical_evidence.get("extreme")
            or (
                historical_evidence.get("strong")
                and historical_evidence.get("above_p99")
            )
        )
    )

    current_corroboration = bool(batch_strong or ml_support)

    return bool(
        historical_primary
        and historical_specific_tail
        and current_corroboration
    )


def _historical_normal_tail_protection(
    merchant_evidence: Dict[str, Any],
    category_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Protect legitimate high-value historical behavior from false positives.

    Merchant history is the most specific signal.  Category tail evidence is
    used as a fallback.  This protection can block generic/global routes but
    does not block a dual-reference contextual override.
    """

    for name, evidence in [
        ("merchant", merchant_evidence),
        ("category", category_evidence),
    ]:
        if evidence.get("mature") and evidence.get("normal_tail"):
            return {
                "protected": True,
                "source": name,
            }

    return {
        "protected": False,
        "source": None,
    }


# ============================================================
# Evidence helpers
# ============================================================


def _strongest_context(
    candidates: List[tuple],
) -> Dict[str, Any]:

    best_name = None
    best_evidence = None
    best_strength = -1

    for name, evidence in candidates:

        strength = 0

        if evidence.get("extreme"):
            strength = 2

        elif evidence.get("strong"):
            strength = 1

        if strength > best_strength:

            best_strength = strength
            best_name = name
            best_evidence = evidence

    if best_evidence is None:

        best_evidence = {
            "strong": False,
            "extreme": False,
        }

    return {
        "name": best_name,
        "strong": bool(
            best_evidence.get(
                "strong"
            )
        ),
        "extreme": bool(
            best_evidence.get(
                "extreme"
            )
        ),
    }


# ============================================================
# V4.6 Amount Decision
# ============================================================


def _amount_decision(
    amount: float,
    entity_id: Optional[str],
    merchant: Optional[str],
    category: Optional[str],
    transaction_type: Optional[str],
    ml_score: Optional[float],
    historical_baseline: Optional[Dict[str, Any]],
    batch_reference: Dict[str, Any],
    baseline_trust: Dict[str, Any],
) -> Dict[str, Any]:

    historical_global = _historical_global_evidence(amount, historical_baseline)
    batch_global = _batch_global_evidence(amount, batch_reference)

    historical_merchant = _historical_context_evidence(
        amount=amount,
        key=merchant,
        section_name="merchants",
        minimum_count=MIN_HISTORICAL_MERCHANT_COUNT,
        baseline=historical_baseline,
    )
    historical_category = _historical_context_evidence(
        amount=amount,
        key=category,
        section_name="categories",
        minimum_count=MIN_HISTORICAL_CATEGORY_COUNT,
        baseline=historical_baseline,
    )
    historical_type = _historical_context_evidence(
        amount=amount,
        key=transaction_type,
        section_name="transaction_types",
        minimum_count=MIN_HISTORICAL_TRANSACTION_TYPE_COUNT,
        baseline=historical_baseline,
    )
    historical_entity = _historical_context_evidence(
        amount=amount,
        key=entity_id,
        section_name="entities",
        minimum_count=MIN_HISTORICAL_ENTITY_COUNT,
        baseline=historical_baseline,
    )

    batch_merchant = _batch_context_evidence(
        amount=amount,
        key=merchant,
        section_name="merchants",
        minimum_count=MIN_BATCH_MERCHANT_COUNT,
        batch_reference=batch_reference,
    )
    batch_category = _batch_context_evidence(
        amount=amount,
        key=category,
        section_name="categories",
        minimum_count=MIN_BATCH_CATEGORY_COUNT,
        batch_reference=batch_reference,
    )
    batch_type = _batch_context_evidence(
        amount=amount,
        key=transaction_type,
        section_name="transaction_types",
        minimum_count=MIN_BATCH_TRANSACTION_TYPE_COUNT,
        batch_reference=batch_reference,
    )
    batch_entity = _batch_context_evidence(
        amount=amount,
        key=entity_id,
        section_name="entities",
        minimum_count=MIN_BATCH_ENTITY_COUNT,
        batch_reference=batch_reference,
    )

    historical_context = _business_context_family(
        historical_merchant,
        historical_category,
        historical_type,
    )
    batch_context = _business_context_family(
        batch_merchant,
        batch_category,
        batch_type,
    )

    contradiction = _contextual_contradiction(
        batch_merchant,
        batch_category,
    )
    context_says_normal = bool(contradiction.get("normal"))

    historical_stats = _historical_global_stats(historical_baseline)
    materiality = _historical_materiality(historical_stats)
    normal_floor = materiality.get("normal_floor")
    large_floor = materiality.get("large_floor")

    passes_normal = bool(normal_floor is None or amount >= normal_floor)
    passes_large = bool(large_floor is None or amount >= large_floor)

    ml_support = bool(ml_score is not None and ml_score >= ML_SUPPORT_THRESHOLD)
    ml_strong = bool(ml_score is not None and ml_score >= ML_STRONG_THRESHOLD)

    historical_strong = bool(historical_global.get("strong"))
    historical_extreme = bool(historical_global.get("extreme"))
    batch_strong = bool(batch_global.get("strong"))
    batch_extreme = bool(batch_global.get("extreme"))
    batch_above_p95 = bool(batch_global.get("above_p95"))
    batch_above_p99 = bool(batch_global.get("above_p99"))

    historical_context_strong = bool(historical_context.get("strong"))
    historical_context_extreme = bool(historical_context.get("extreme"))
    batch_context_strong = bool(batch_context.get("strong"))
    batch_context_extreme = bool(batch_context.get("extreme"))
    batch_context_above_p99 = bool(batch_context.get("above_p99"))

    historical_entity_extreme = bool(historical_entity.get("extreme"))
    batch_entity_extreme = bool(batch_entity.get("extreme"))

    # Business-specific context can establish an anomaly even if the whole
    # batch is not globally extreme. Merchant is preferred; category follows.
    specific_batch_extreme = bool(
        batch_merchant.get("extreme")
        or batch_category.get("extreme")
    )
    specific_batch_strong_tail = bool(
        (batch_merchant.get("strong") and batch_merchant.get("above_p99"))
        or (batch_category.get("strong") and batch_category.get("above_p99"))
    )
    specific_historical_extreme = bool(
        historical_merchant.get("extreme")
        or historical_category.get("extreme")
    )
    specific_historical_strong_tail = bool(
        (historical_merchant.get("strong") and historical_merchant.get("above_p99"))
        or (historical_category.get("strong") and historical_category.get("above_p99"))
    )

    trust_score = _safe_float(baseline_trust.get("score"), 0.0) or 0.0
    trust_level = baseline_trust.get("level", "unavailable")
    historical_primary = bool(baseline_trust.get("historical_primary"))

    # Architectural correction #1: the company-wide materiality floor is
    # evidence, not a universal veto.  Mature merchant/category behavior may
    # override it when the specific context is anomalous and independently
    # corroborated.
    merchant_context_override = _context_materiality_override(
        historical_merchant,
        batch_merchant,
        historical_primary=historical_primary,
        ml_support=ml_support,
    )
    category_context_override = _context_materiality_override(
        historical_category,
        batch_category,
        historical_primary=historical_primary,
        ml_support=ml_support,
    )
    context_materiality_override = bool(
        merchant_context_override
        or category_context_override
    )

    # Architectural correction #3: known legitimate high-value historical
    # behavior can protect generic/global routes from producing false positives.
    tail_protection = _historical_normal_tail_protection(
        historical_merchant,
        historical_category,
    )
    historical_normal_tail = bool(
        tail_protection.get("protected")
    )

    severity = None
    confidence = 0.0
    decision_rule = None
    rejection_reason = None

    # --------------------------------------------------------
    # 1) CONTEXT-FIRST BUSINESS ANOMALIES
    # --------------------------------------------------------
    # This path intentionally does not require global p95/p99 rarity. A payment
    # can be abnormal for a supplier/category while still looking ordinary in
    # a heterogeneous company-wide distribution.
    #
    # The dual-reference override is deliberately narrow: historical and
    # current-batch evidence must agree in the same merchant/category context.
    if context_materiality_override:
        severity = "high"
        confidence = 0.97 if ml_support else 0.94
        decision_rule = "dual_reference_context_override"

    elif passes_normal and specific_batch_extreme and not historical_normal_tail:
        severity = "high"
        confidence = 0.96 if ml_support else 0.93
        decision_rule = "context_primary_extreme"

    elif (
        passes_normal
        and specific_batch_strong_tail
        and ml_support
        and not historical_normal_tail
    ):
        severity = "high"
        confidence = 0.95 if ml_strong else 0.92
        decision_rule = "context_primary_strong_tail_ml"

    elif (
        historical_primary
        and passes_normal
        and (specific_historical_extreme or specific_historical_strong_tail)
        and (batch_context_strong or ml_support)
        and not historical_normal_tail
    ):
        severity = "high"
        confidence = 0.96 if ml_support else 0.93
        decision_rule = "trusted_historical_context_primary"

    # --------------------------------------------------------
    # 2) GLOBAL / ENTITY ROUTES
    # --------------------------------------------------------
    # A mature merchant/category that says the amount is normal blocks these
    # generic routes. This is the contextual contradiction safeguard.
    if severity is None and not context_says_normal and not historical_normal_tail:
        if historical_primary:
            if (
                passes_large
                and historical_extreme
                and batch_extreme
                and batch_above_p99
            ):
                severity = "high"
                confidence = 0.99 if ml_strong else (0.98 if ml_support else 0.96)
                decision_rule = "trusted_dual_global_extreme"

            elif (
                passes_large
                and historical_strong
                and batch_strong
                and (
                    historical_context_strong
                    or batch_context_strong
                    or batch_entity_extreme
                )
            ):
                severity = "high"
                confidence = 0.98 if ml_support else 0.94
                decision_rule = "trusted_large_contextual"

            elif (
                passes_normal
                and not passes_large
                and historical_extreme
                and batch_extreme
                and (
                    historical_context_extreme
                    or batch_context_extreme
                    or batch_entity_extreme
                )
                and ml_support
            ):
                severity = "high"
                confidence = 0.97 if ml_strong else 0.93
                decision_rule = "trusted_moderate_multi_evidence"

            elif (
                passes_normal
                and historical_strong
                and batch_strong
                and historical_entity_extreme
                and (batch_context_strong or ml_support)
            ):
                severity = "high"
                confidence = 0.98 if ml_support else 0.95
                decision_rule = "trusted_entity_corroborated"

        else:
            if (
                passes_normal
                and batch_extreme
                and batch_above_p99
                and (
                    batch_context_extreme
                    or batch_entity_extreme
                    or ml_strong
                )
            ):
                severity = "high"
                confidence = 0.97 if ml_strong else 0.95
                decision_rule = "drift_current_extreme"

            elif (
                passes_normal
                and batch_extreme
                and batch_above_p95
                and batch_context_extreme
                and ml_support
            ):
                severity = "high"
                confidence = 0.95 if ml_strong else 0.92
                decision_rule = "drift_contextual_ml"

            elif (
                passes_normal
                and batch_strong
                and batch_entity_extreme
                and (batch_context_strong or ml_support)
            ):
                severity = "high"
                confidence = 0.96 if ml_support else 0.93
                decision_rule = "drift_entity_corroborated"

    if severity is None:
        if historical_normal_tail:
            rejection_reason = "historical_context_normal_tail"
        elif not passes_normal and not context_materiality_override:
            rejection_reason = "below_business_materiality"
        elif context_says_normal:
            rejection_reason = "contextual_contradiction_normal"
        elif not batch_strong and not specific_batch_extreme and not specific_batch_strong_tail:
            rejection_reason = "not_rare_in_current_business_regime"
        elif not historical_primary and not (
            batch_context_extreme
            or batch_entity_extreme
            or ml_support
        ):
            rejection_reason = "stale_baseline_without_current_corroboration"
        elif historical_primary and not historical_strong and not specific_historical_extreme:
            rejection_reason = "insufficient_trusted_historical_evidence"
        elif not (
            batch_context_strong
            or historical_context_strong
            or batch_entity_extreme
            or historical_entity_extreme
            or ml_support
        ):
            rejection_reason = "missing_business_corroboration"
        else:
            rejection_reason = "contextual_stabilization_gate_rejected"

    signals: List[str] = []
    for evidence in [
        historical_global,
        batch_global,
        historical_merchant,
        historical_category,
        historical_type,
        historical_entity,
        batch_merchant,
        batch_category,
        batch_type,
        batch_entity,
    ]:
        signals.extend(evidence.get("signals", []))

    signals.append(f"baseline_trust_{trust_level}")
    if context_says_normal:
        signals.append(
            f"normal_{contradiction.get('source')}_context_contradiction"
        )

    if context_materiality_override:
        signals.append("context_materiality_override")

    if historical_normal_tail:
        signals.append(
            f"historical_{tail_protection.get('source')}_normal_tail_protection"
        )

    if ml_strong:
        signals.append("strong_ml_support")
    elif ml_support:
        signals.append("ml_support")

    evidence_families: List[str] = []
    if historical_strong:
        evidence_families.append("historical_distribution")
    if batch_strong:
        evidence_families.append("current_batch_rarity")
    if (
        historical_context_strong
        or batch_context_strong
        or specific_batch_extreme
        or specific_batch_strong_tail
    ):
        evidence_families.append("business_context")
    if batch_merchant.get("mature") or historical_merchant.get("mature"):
        evidence_families.append("merchant_context")
    if historical_entity_extreme or batch_entity_extreme:
        evidence_families.append("entity_history")
    if ml_support:
        evidence_families.append("machine_learning")
    if passes_normal:
        evidence_families.append("economic_materiality")

    return {
        "severity": severity,
        "confidence": round(confidence, 4),
        "decision_rule": decision_rule,
        "rejection_reason": rejection_reason,
        "signals": signals,
        "evidence_families": evidence_families,
        "evidence": {
            "baseline_trust": baseline_trust,
            "historical_global": historical_global,
            "batch_global": batch_global,
            "historical_merchant": historical_merchant,
            "batch_merchant": batch_merchant,
            "historical_category": historical_category,
            "batch_category": batch_category,
            "historical_transaction_type": historical_type,
            "batch_transaction_type": batch_type,
            "historical_entity": historical_entity,
            "batch_entity": batch_entity,
            "historical_business_context": historical_context,
            "batch_business_context": batch_context,
            "contextual_contradiction": contradiction,
            "ml": {
                "isolation_score": ml_score,
                "support": ml_support,
                "strong_support": ml_strong,
            },
            "materiality": {
                "source": "historical_business_baseline",
                "normal_floor": normal_floor,
                "large_floor": large_floor,
                "p95_component": materiality.get("p95_component"),
                "median_component": materiality.get("median_component"),
                "amount": amount,
                "passes_normal_floor": passes_normal,
                "passes_large_floor": passes_large,
            },
            "current_batch_rarity": {
                "above_p95": batch_above_p95,
                "above_p99": batch_above_p99,
                "strong": batch_strong,
                "extreme": batch_extreme,
            },
            "decision": {
                "rule": decision_rule,
                "final_severity": severity,
                "rejection_reason": rejection_reason,
                "evidence_families": evidence_families,
                "baseline_trust_level": trust_level,
                "baseline_trust_score": trust_score,
            },
        },
    }


# ============================================================
# Amount finding
# ============================================================


def _amount_finding(
    txid: str,
    amount: float,
    evaluation: Dict[str, Any],
) -> Dict[str, Any]:

    confidence = (
        evaluation[
            "confidence"
        ]
    )

    amount_at_risk = (
        amount
        * 0.30
        * confidence
    )

    families = ", ".join(
        evaluation.get(
            "evidence_families",
            [],
        )
    )

    signals = ", ".join(
        evaluation.get(
            "signals",
            [],
        )
    )

    return {
        "type": "amount_anomaly",
        "severity": "high",
        "title": (
            "High-confidence financial "
            "amount anomaly"
        ),
        "message": (
            f"Transaction {txid} has a "
            f"normalized amount of "
            f"{amount:.2f} {BASE_CURRENCY}. "
            f"Evidence families: {families}. "
            f"Signals: {signals}."
        ),
        "amount_at_risk": round(
            amount_at_risk,
            2,
        ),
        "transaction_id": txid,
        "confidence": confidence,
        "decision_rule": (
            evaluation.get(
                "decision_rule"
            )
        ),
        "signals": (
            evaluation.get(
                "signals",
                [],
            )
        ),
        "evidence_families": (
            evaluation.get(
                "evidence_families",
                [],
            )
        ),
        "evidence": (
            evaluation["evidence"]
        ),
    }


# ============================================================
# Duplicate detector
# ============================================================


def _duplicate_findings(
    df: pd.DataFrame,
) -> List[Dict[str, Any]]:

    findings: List[
        Dict[str, Any]
    ] = []

    if (
        "transaction_id"
        not in df.columns
    ):
        return findings

    grouped = df.groupby(
        "transaction_id",
        dropna=True,
    )

    for txid, group in grouped:

        txid_text = _safe_text(
            txid
        )

        if not txid_text:
            continue

        if len(group) < 2:
            continue

        amounts: List[float] = []

        for _, row in group.iterrows():

            amount = _normalized_amount(
                row
            )

            if amount is not None:

                amounts.append(
                    amount
                )

        if not amounts:
            continue

        minimum = min(amounts)
        maximum = max(amounts)

        denominator = max(
            abs(minimum),
            abs(maximum),
            1.0,
        )

        difference_ratio = (
            abs(
                maximum
                - minimum
            )
            / denominator
        )

        if difference_ratio > 0.01:
            continue

        matching_context_count = 0

        for column in [
            "entity_id",
            "category",
            "transaction_type",
        ]:

            if column not in group.columns:
                continue

            values = {
                _normalize_text(value)
                for value
                in group[column]
                if _normalize_text(value)
            }

            if len(values) == 1:
                matching_context_count += 1

        if matching_context_count < 1:
            continue

        confidence = (
            0.97
            if matching_context_count >= 2
            else 0.94
        )

        representative_amount = (
            sum(amounts)
            / len(amounts)
        )

        findings.append(
            {
                "type": (
                    "duplicate_transaction"
                ),
                "severity": "high",
                "title": (
                    "Probable duplicate "
                    "transaction"
                ),
                "message": (
                    f"Transaction ID "
                    f"{txid_text} appears "
                    f"{len(group)} times with "
                    f"nearly identical amounts "
                    f"and matching transaction "
                    f"context."
                ),
                "amount_at_risk": round(
                    representative_amount
                    * 0.50
                    * confidence,
                    2,
                ),
                "transaction_id": (
                    txid_text
                ),
                "confidence": confidence,
                "evidence": {
                    "occurrences": len(
                        group
                    ),
                    "amount_difference_ratio": (
                        round(
                            difference_ratio,
                            4,
                        )
                    ),
                    "matching_context_count": (
                        matching_context_count
                    ),
                },
            }
        )

    return findings


# ============================================================
# Suspicious category detector
# ============================================================


def _suspicious_semantic_findings(
    df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Detect explicit suspicious semantics across canonical business fields.

    Different client exports place fraud/authorization semantics in different
    columns.  The detector therefore inspects category, transaction_type and
    status instead of assuming that category is the only valid location.
    """

    findings: List[Dict[str, Any]] = []

    suspicious_terms = {
        "chargeback",
        "unauthorized",
        "fraud",
        "fraudulent",
        "reversal_fraud",
    }

    semantic_fields = [
        "category",
        "transaction_type",
        "status",
    ]

    available_fields = [
        field
        for field in semantic_fields
        if field in df.columns
    ]

    if not available_fields:
        return findings

    for position, (_, row) in enumerate(df.iterrows()):
        matches: List[Dict[str, str]] = []

        for field in available_fields:
            value = _normalize_text(row.get(field))
            if value in suspicious_terms:
                matches.append({
                    "field": field,
                    "value": value,
                })

        if not matches:
            continue

        txid = _transaction_id(row, position)
        amount = _normalized_amount(row) or 0.0

        matched_fields = ", ".join(
            f"{item['field']}='{item['value']}'"
            for item in matches
        )

        findings.append({
            "type": "suspicious_transaction",
            "severity": "high",
            "title": "Suspicious transaction semantics",
            "message": (
                f"Transaction {txid} contains explicit suspicious "
                f"semantics: {matched_fields}."
            ),
            "amount_at_risk": round(amount * 0.50, 2),
            "transaction_id": txid,
            "confidence": 0.95,
            "evidence": {
                "matches": matches,
            },
        })

    return findings


# ============================================================
# Operational failure rate
# ============================================================


def _failure_rate_finding(
    df: pd.DataFrame,
    baseline: Optional[
        Dict[str, Any]
    ],
    business_rules: Optional[
        Dict[str, Any]
    ],
) -> Optional[Dict[str, Any]]:

    if "status" not in df.columns:
        return None

    values = [
        _normalize_text(value)
        for value in df["status"]
    ]

    values = [
        value
        for value in values
        if value
    ]

    if not values:
        return None

    failure_terms = {
        "failed",
        "failure",
        "declined",
        "rejected",
        "error",
    }

    failed_count = sum(
        1
        for value in values
        if value in failure_terms
    )

    total_count = len(values)

    rate = (
        failed_count
        / total_count
    )

    historical_rate = 0.0

    operational = (
        _baseline_section(
            baseline,
            "operational",
        )
    )

    if operational:

        failure_section = (
            operational.get(
                "failure",
                {},
            )
        )

        if isinstance(
            failure_section,
            dict,
        ):

            historical_rate = (
                _safe_float(
                    failure_section.get(
                        "rate"
                    ),
                    0.0,
                )
                or 0.0
            )

        elif (
            "failure_rate"
            in operational
        ):

            historical_rate = (
                _safe_float(
                    operational.get(
                        "failure_rate"
                    ),
                    0.0,
                )
                or 0.0
            )

    configured = 0.05

    if business_rules:

        configured = (
            _safe_float(
                business_rules.get(
                    "failure_rate_warning"
                ),
                0.05,
            )
            or 0.05
        )

    threshold = max(
        0.05,
        configured,
        historical_rate * 1.75,
    )

    if rate < threshold:
        return None

    high_threshold = max(
        0.10,
        threshold * 1.50,
    )

    severity = (
        "high"
        if rate >= high_threshold
        else "medium"
    )

    return {
        "type": (
            "operational_failure_rate"
        ),
        "severity": severity,
        "title": (
            "Elevated transaction "
            "failure rate"
        ),
        "message": (
            f"Current failure rate is "
            f"{rate:.2%}, above threshold "
            f"{threshold:.2%}."
        ),
        "amount_at_risk": 0.0,
        "transaction_id": None,
        "confidence": 0.90,
        "evidence": {
            "failed_count": failed_count,
            "total_count": total_count,
            "current_rate": round(
                rate,
                6,
            ),
            "historical_rate": (
                historical_rate
            ),
            "threshold": round(
                threshold,
                6,
            ),
        },
    }


# ============================================================
# Currency quality
# ============================================================


def _currency_quality_finding(
    df: pd.DataFrame,
) -> Optional[Dict[str, Any]]:

    columns = {
        "fx_unavailable": (
            "_fx_unavailable"
        ),
        "currency_conflict": (
            "_currency_conflict"
        ),
        "unknown_currency": (
            "_unknown_currency"
        ),
    }

    affected_rows = set()

    counts: Dict[
        str,
        int,
    ] = {}

    for name, column in columns.items():

        if column not in df.columns:
            continue

        indexes = [
            position
            for position, value
            in enumerate(
                df[column].tolist()
            )
            if bool(value)
        ]

        if indexes:

            counts[name] = len(
                indexes
            )

            affected_rows.update(
                indexes
            )

    if not affected_rows:
        return None

    row_count = len(df)

    if row_count <= 0:
        return None

    rate = (
        len(affected_rows)
        / row_count
    )

    if (
        len(affected_rows) < 5
        and rate < 0.02
    ):
        return None

    return {
        "type": (
            "currency_data_quality"
        ),
        "severity": "low",
        "title": (
            "Currency normalization "
            "data quality issue"
        ),
        "message": (
            f"{len(affected_rows)} of "
            f"{row_count} rows have "
            f"currency normalization issues."
        ),
        "amount_at_risk": 0.0,
        "transaction_id": None,
        "confidence": 0.90,
        "evidence": {
            "problem_rate": round(
                rate,
                6,
            ),
            "problem_counts": counts,
        },
    }


# ============================================================
# Money at risk
# ============================================================


def _unique_money_at_risk(
    findings: List[Dict[str, Any]],
) -> float:

    transaction_exposure: Dict[
        str,
        float,
    ] = defaultdict(float)

    aggregate = 0.0

    for finding in findings:

        amount = (
            _safe_float(
                finding.get(
                    "amount_at_risk"
                ),
                0.0,
            )
            or 0.0
        )

        txid = _safe_text(
            finding.get(
                "transaction_id"
            )
        )

        if txid:

            transaction_exposure[
                txid
            ] = max(
                transaction_exposure[
                    txid
                ],
                amount,
            )

        else:

            aggregate += amount

    return round(
        sum(
            transaction_exposure.values()
        )
        + aggregate,
        2,
    )


# ============================================================
# Risk score
# ============================================================


def _risk_score(
    findings: List[Dict[str, Any]],
    row_count: int,
) -> Dict[str, Any]:

    financial_types = {
        "amount_anomaly",
        "duplicate_transaction",
        "suspicious_category",
        "suspicious_transaction",
        "refund_pattern",
        "high_customer_exposure",
    }

    financial_findings = [
        finding
        for finding in findings
        if finding.get("type")
        in financial_types
    ]

    unique_transactions = {
        finding.get(
            "transaction_id"
        )
        for finding
        in financial_findings
        if finding.get(
            "transaction_id"
        )
    }

    density = (
        len(unique_transactions)
        / max(
            row_count,
            1,
        )
    )

    density_component = min(
        25.0,
        density * 200.0,
    )

    severity_weights = {
        "high": 1.0,
        "medium": 0.45,
        "low": 0.10,
    }

    severity_total = sum(
        severity_weights.get(
            _normalize_text(
                finding.get(
                    "severity"
                )
            ),
            0.0,
        )
        for finding
        in financial_findings
    )

    severity_component = min(
        45.0,
        severity_total * 3.0,
    )

    operational = 0.0

    for finding in findings:

        if (
            finding.get("type")
            != "operational_failure_rate"
        ):
            continue

        if (
            _normalize_text(
                finding.get(
                    "severity"
                )
            )
            == "high"
        ):

            operational = max(
                operational,
                10.0,
            )

        else:

            operational = max(
                operational,
                5.0,
            )

    data_quality = (
        2.0
        if any(
            finding.get(
                "type"
            )
            == "currency_data_quality"
            for finding in findings
        )
        else 0.0
    )

    score = min(
        100.0,
        density_component
        + severity_component
        + operational
        + data_quality,
    )

    score = round(
        score,
        2,
    )

    if score >= 70:
        level = "HIGH"

    elif score >= 35:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_breakdown": {
            "financial_density": round(
                density_component,
                2,
            ),
            "financial_severity": round(
                severity_component,
                2,
            ),
            "operational": round(
                operational,
                2,
            ),
            "data_quality": round(
                data_quality,
                2,
            ),
            "unique_financial_transactions": (
                len(
                    unique_transactions
                )
            ),
            "high_financial_findings": sum(
                1
                for finding
                in financial_findings
                if _normalize_text(
                    finding.get(
                        "severity"
                    )
                )
                == "high"
            ),
            "medium_financial_findings": sum(
                1
                for finding
                in financial_findings
                if _normalize_text(
                    finding.get(
                        "severity"
                    )
                )
                == "medium"
            ),
        },
    }


# ============================================================
# Main detector
# ============================================================


def detect_financial_leaks(
    df: pd.DataFrame,
    client_baseline: Optional[
        Dict[str, Any]
    ] = None,
    business_rules: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    working_df = (
        df.reset_index(
            drop=True
        )
        .copy()
    )

    # --------------------------------------------------------
    # Robust current batch reference
    # --------------------------------------------------------

    batch_reference = (
        _build_batch_reference(
            working_df
        )
    )

    historical_stats = (
        _historical_global_stats(
            client_baseline
        )
    )

    batch_stats = (
        batch_reference.get(
            "amount",
            {},
        )
    )

    drift = _drift_metrics(
        historical_stats,
        batch_stats,
    )

    baseline_trust = _baseline_trust(
        historical_stats,
        batch_stats,
        drift,
    )

    materiality = (
        _historical_materiality(
            historical_stats
        )
    )

    ml_scores = (
        _isolation_scores(
            working_df
        )
    )

    findings: List[
        Dict[str, Any]
    ] = []

    historical_candidates = 0
    batch_candidates = 0
    dual_candidates = 0

    accepted_amount_findings = 0

    rejection_counts: Dict[
        str,
        int,
    ] = defaultdict(int)

    decision_rule_counts: Dict[
        str,
        int,
    ] = defaultdict(int)

    # --------------------------------------------------------
    # Amount analysis
    # --------------------------------------------------------

    for position, row in (
        working_df.iterrows()
    ):

        amount = _normalized_amount(
            row
        )

        if amount is None:
            continue

        if amount < 0:
            continue

        evaluation = _amount_decision(
            amount=amount,
            entity_id=_safe_text(
                row.get(
                    "entity_id"
                )
            ),
            merchant=_safe_text(
                row.get(
                    "merchant"
                )
            ),
            category=_safe_text(
                row.get(
                    "category"
                )
            ),
            transaction_type=_safe_text(
                row.get(
                    "transaction_type"
                )
            ),
            ml_score=ml_scores.get(
                position
            ),
            historical_baseline=(
                client_baseline
            ),
            batch_reference=(
                batch_reference
            ),
            baseline_trust=(
                baseline_trust
            ),
        )

        evidence = (
            evaluation["evidence"]
        )

        historical_global = (
            evidence.get(
                "historical_global",
                {},
            )
        )

        batch_global = (
            evidence.get(
                "batch_global",
                {},
            )
        )

        if historical_global.get(
            "strong"
        ):

            historical_candidates += 1

        if batch_global.get(
            "strong"
        ):

            batch_candidates += 1

        if (
            historical_global.get(
                "strong"
            )
            and batch_global.get(
                "strong"
            )
        ):

            dual_candidates += 1

        if evaluation.get(
            "severity"
        ):

            txid = _transaction_id(
                row,
                position,
            )

            findings.append(
                _amount_finding(
                    txid=txid,
                    amount=amount,
                    evaluation=evaluation,
                )
            )

            accepted_amount_findings += 1

            rule = (
                evaluation.get(
                    "decision_rule"
                )
                or "unknown"
            )

            decision_rule_counts[
                rule
            ] += 1

        else:

            reason = (
                evaluation.get(
                    "rejection_reason"
                )
                or "unknown"
            )

            rejection_counts[
                reason
            ] += 1

    # --------------------------------------------------------
    # Independent detectors
    # --------------------------------------------------------

    findings.extend(
        _duplicate_findings(
            working_df
        )
    )

    findings.extend(
        _suspicious_semantic_findings(
            working_df
        )
    )

    failure = _failure_rate_finding(
        working_df,
        client_baseline,
        business_rules,
    )

    if failure:
        findings.append(failure)

    currency_issue = (
        _currency_quality_finding(
            working_df
        )
    )

    if currency_issue:
        findings.append(
            currency_issue
        )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    risk = _risk_score(
        findings,
        len(working_df),
    )

    high_risk = sum(
        1
        for finding in findings
        if _normalize_text(
            finding.get(
                "severity"
            )
        )
        == "high"
    )

    medium_risk = sum(
        1
        for finding in findings
        if _normalize_text(
            finding.get(
                "severity"
            )
        )
        == "medium"
    )

    low_risk = sum(
        1
        for finding in findings
        if _normalize_text(
            finding.get(
                "severity"
            )
        )
        == "low"
    )

    return {
        "engine_version": (
            ENGINE_VERSION
        ),
        "baseline_used": bool(
            client_baseline
        ),
        "risk_score": (
            risk["risk_score"]
        ),
        "risk_level": (
            risk["risk_level"]
        ),
        "risk_breakdown": (
            risk["risk_breakdown"]
        ),
        "total_findings": (
            len(findings)
        ),
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "money_at_risk": (
            _unique_money_at_risk(
                findings
            )
        ),
        "findings": findings,
        "metrics": {
            "rows_analyzed": (
                len(working_df)
            ),

            "architecture": (
                "dual-reference-context-override-tail-protected"
            ),

            "historical_baseline_used": bool(
                client_baseline
            ),

            "batch_reference_used": True,

            "batch_materiality_is_hard_gate": (
                False
            ),

            "historical_amount_candidates": (
                historical_candidates
            ),

            "batch_rarity_candidates": (
                batch_candidates
            ),

            "dual_reference_candidates": (
                dual_candidates
            ),

            "accepted_amount_findings": (
                accepted_amount_findings
            ),

            "rejection_counts": dict(
                rejection_counts
            ),

            "decision_rule_counts": dict(
                decision_rule_counts
            ),

            "ml_rows_scored": len(
                ml_scores
            ),

            "correlated_contexts_combined": (
                True
            ),

            "historical_context_shrinkage": (
                True
            ),

            "batch_context_enabled": (
                True
            ),

            "merchant_context_enabled": True,

            "historical_merchant_baseline_available": bool(
                _baseline_section(client_baseline, "merchants")
            ),

            "transaction_type_context_enabled": (
                True
            ),

            "entity_context_enabled": (
                True
            ),

            "historical_materiality_floor": (
                materiality.get(
                    "normal_floor"
                )
            ),

            "historical_large_amount_floor": (
                materiality.get(
                    "large_floor"
                )
            ),

            "materiality_source": (
                "historical_business_baseline"
            ),

            "batch_reference_upper_quantile": (
                BATCH_REFERENCE_UPPER_QUANTILE
            ),

            "baseline_trust": baseline_trust,

            "historical_global_is_primary": (
                baseline_trust.get(
                    "historical_primary"
                )
            ),

            "merchant_context_preferred": True,

            "category_context_preferred": True,

            "drift": drift,

            "batch_reference": {
                "count": (
                    batch_stats.get(
                        "count"
                    )
                ),
                "reference_count": (
                    batch_stats.get(
                        "reference_count"
                    )
                ),
                "median": (
                    batch_stats.get(
                        "median"
                    )
                ),
                "mad": (
                    batch_stats.get(
                        "mad"
                    )
                ),
                "p75": (
                    batch_stats.get(
                        "p75"
                    )
                ),
                "p90": (
                    batch_stats.get(
                        "p90"
                    )
                ),
                "p95": (
                    batch_stats.get(
                        "p95"
                    )
                ),
                "p99": (
                    batch_stats.get(
                        "p99"
                    )
                ),
            },
        },
    }


# ============================================================
# Compatibility aliases
# ============================================================


def detect_leaks(
    df: pd.DataFrame,
    client_baseline: Optional[
        Dict[str, Any]
    ] = None,
    business_rules: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    return detect_financial_leaks(
        df=df,
        client_baseline=(
            client_baseline
        ),
        business_rules=(
            business_rules
        ),
    )


def analyze(
    df: pd.DataFrame,
    client_baseline: Optional[
        Dict[str, Any]
    ] = None,
    business_rules: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    return detect_financial_leaks(
        df=df,
        client_baseline=(
            client_baseline
        ),
        business_rules=(
            business_rules
        ),
    )