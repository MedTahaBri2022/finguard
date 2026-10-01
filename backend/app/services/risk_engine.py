from typing import Any, Dict, List


SEVERITY_WEIGHTS = {
    "high": 1.0,
    "medium": 0.45,
    "low": 0.10,
}


FINANCIAL_FINDING_TYPES = {
    "amount_anomaly",
    "duplicate_transaction",
    "suspicious_category",
    "refund_pattern",
    "high_customer_exposure",
}


OPERATIONAL_FINDING_TYPES = {
    "operational_failure_rate",
}


DATA_QUALITY_FINDING_TYPES = {
    "currency_data_quality",
    "currency_conflict",
    "low_value_anomaly",
}


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def calculate_risk_score(
    findings: List[
        Dict[str, Any]
    ],
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:

    if context is None:
        context = {}

    total_rows = max(
        int(
            context.get(
                "total_rows",
                0,
            )
            or 0
        ),
        1,
    )

    failure_rate = _safe_float(
        context.get(
            "failure_rate",
            0,
        )
    )

    duplicate_rate = _safe_float(
        context.get(
            "duplicate_rate",
            0,
        )
    )

    invalid_rate = _safe_float(
        context.get(
            "invalid_rate",
            0,
        )
    )

    exposure_ratio = _safe_float(
        context.get(
            "exposure_ratio",
            0,
        )
    )

    anomaly_rate = _safe_float(
        context.get(
            "anomaly_rate",
            0,
        )
    )

    # ========================================================
    # UNIQUE TRANSACTION EVIDENCE
    #
    # Avoid counting multiple findings on same transaction
    # as independent financial evidence.
    # ========================================================

    transaction_evidence: Dict[
        str,
        float,
    ] = {}

    independent_financial_evidence = 0.0

    strong_high_transactions = set()

    operational_evidence = 0.0

    data_quality_evidence = 0.0

    for finding in findings:

        finding_type = str(
            finding.get(
                "type",
                "",
            )
        ).lower()

        severity = str(
            finding.get(
                "severity",
                "low",
            )
        ).lower()

        confidence = _safe_float(
            finding.get(
                "confidence",
                0.70,
            ),
            0.70,
        )

        confidence = max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

        severity_weight = (
            SEVERITY_WEIGHTS.get(
                severity,
                0.10,
            )
        )

        evidence_score = (
            severity_weight
            * confidence
        )

        transaction_id = (
            finding.get(
                "transaction_id"
            )
        )

        # ====================================================
        # FINANCIAL EVIDENCE
        # ====================================================

        if (
            finding_type
            in FINANCIAL_FINDING_TYPES
        ):

            if transaction_id:

                transaction_key = str(
                    transaction_id
                )

                previous = (
                    transaction_evidence.get(
                        transaction_key,
                        0.0,
                    )
                )

                transaction_evidence[
                    transaction_key
                ] = max(
                    previous,
                    evidence_score,
                )

                if (
                    severity == "high"
                    and confidence >= 0.85
                ):
                    strong_high_transactions.add(
                        transaction_key
                    )

            else:

                independent_financial_evidence += (
                    evidence_score
                )

        # ====================================================
        # OPERATIONAL EVIDENCE
        # ====================================================

        elif (
            finding_type
            in OPERATIONAL_FINDING_TYPES
        ):

            operational_evidence += (
                evidence_score
            )

        # ====================================================
        # DATA QUALITY
        #
        # Small contribution only.
        # ====================================================

        elif (
            finding_type
            in DATA_QUALITY_FINDING_TYPES
        ):

            data_quality_evidence += (
                evidence_score
                * 0.15
            )

    unique_financial_evidence = (
        sum(
            transaction_evidence.values()
        )
        + independent_financial_evidence
    )

    # ========================================================
    # COMPONENT 1:
    # FINDING EVIDENCE
    #
    # 0 → 30 points
    # ========================================================

    financial_density = (
        unique_financial_evidence
        / total_rows
    )

    findings_component = min(
        financial_density
        / 0.08,
        1.0,
    ) * 30.0

    # ========================================================
    # COMPONENT 2:
    # ANOMALY RATE
    #
    # 0 → 25 points
    #
    # 8% strong anomaly rate = max component.
    # ========================================================

    anomaly_component = min(
        anomaly_rate
        / 0.08,
        1.0,
    ) * 25.0

    # ========================================================
    # COMPONENT 3:
    # FINANCIAL EXPOSURE
    #
    # 0 → 25 points
    #
    # 25% exposure ratio = max component.
    # ========================================================

    exposure_component = min(
        exposure_ratio
        / 0.25,
        1.0,
    ) * 25.0

    # ========================================================
    # COMPONENT 4:
    # OPERATIONAL RISK
    #
    # Failure rate matters progressively.
    #
    # <5% should stay relatively small.
    # ========================================================

    if failure_rate < 0.05:

        failure_component = (
            failure_rate
            / 0.05
        ) * 3.0

    elif failure_rate < 0.10:

        failure_component = (
            3.0
            + (
                (
                    failure_rate
                    - 0.05
                )
                / 0.05
            )
            * 5.0
        )

    else:

        failure_component = min(
            8.0
            + (
                (
                    failure_rate
                    - 0.10
                )
                / 0.10
            )
            * 4.0,
            12.0,
        )

    duplicate_component = min(
        duplicate_rate
        / 0.05,
        1.0,
    ) * 5.0

    operational_component = (
        failure_component
        + duplicate_component
    )

    # ========================================================
    # COMPONENT 5:
    # DATA QUALITY
    #
    # Maximum only 3 points.
    # ========================================================

    data_quality_component = min(
        (
            invalid_rate
            * 10.0
        )
        + data_quality_evidence,
        3.0,
    )

    # ========================================================
    # TOTAL SCORE
    # ========================================================

    score = (
        findings_component
        + anomaly_component
        + exposure_component
        + operational_component
        + data_quality_component
    )

    # ========================================================
    # STRONG-EVIDENCE FLOOR
    #
    # Conservative:
    # one HIGH finding does NOT force overall MEDIUM/HIGH.
    #
    # Multiple independent high-risk transactions can prevent
    # underestimating a genuinely risky dataset.
    # ========================================================

    high_count = len(
        strong_high_transactions
    )

    if high_count >= 5:
        score = max(
            score,
            55.0,
        )

    elif high_count >= 3:
        score = max(
            score,
            45.0,
        )

    score = round(
        _clamp(
            score
        ),
        2,
    )

    # ========================================================
    # LEVELS V3
    # ========================================================

    if score >= 70:
        level = "HIGH"

    elif score >= 35:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "score":
            score,

        "level":
            level,

        "breakdown": {
            "findings":
                round(
                    findings_component,
                    2,
                ),

            "statistical_anomalies":
                round(
                    anomaly_component,
                    2,
                ),

            "financial_exposure":
                round(
                    exposure_component,
                    2,
                ),

            "operational_risk":
                round(
                    operational_component,
                    2,
                ),

            "data_quality":
                round(
                    data_quality_component,
                    2,
                ),
        },

        "metrics": {
            "failure_rate":
                round(
                    failure_rate,
                    4,
                ),

            "duplicate_rate":
                round(
                    duplicate_rate,
                    4,
                ),

            "invalid_rate":
                round(
                    invalid_rate,
                    4,
                ),

            "anomaly_rate":
                round(
                    anomaly_rate,
                    4,
                ),

            "exposure_ratio":
                round(
                    exposure_ratio,
                    4,
                ),

            "strong_high_transactions":
                high_count,

            "unique_financial_findings":
                len(
                    transaction_evidence
                ),
        },
    }