import pandas as pd

from app.services.leak_detector import detect_financial_leaks
from app.services.risk_engine import calculate_risk_score
from app.services.schema_mapper import detect_schema_mapping, validate_mapping


def transactions(extra=()):
    rows = [
        {
            "transaction_id": f"T{i:03d}",
            "amount": 100 + (i % 7),
            "category": "Retail",
            "status": "completed",
            "entity_id": f"C{i % 5}",
            "transaction_date": f"2026-08-{1 + i % 27:02d}",
            "currency": "MAD",
        }
        for i in range(60)
    ]
    return pd.DataFrame(rows + list(extra))


def findings_by_type(result):
    grouped = {}
    for finding in result["findings"]:
        grouped.setdefault(finding["type"], []).append(finding)
    return grouped


def test_a_regular_batch_raises_no_alarm():
    result = detect_financial_leaks(transactions())

    assert result["total_findings"] == 0
    assert result["risk_level"] == "LOW"
    assert result["money_at_risk"] == 0


def test_an_extreme_amount_is_flagged_with_its_evidence():
    outlier = {
        "transaction_id": "T999",
        "amount": 250000,
        "category": "Retail",
        "status": "completed",
        "entity_id": "C1",
        "transaction_date": "2026-08-15",
        "currency": "MAD",
    }
    result = detect_financial_leaks(transactions([outlier]))

    anomalies = findings_by_type(result)["amount_anomaly"]
    assert [finding["transaction_id"] for finding in anomalies] == ["T999"]
    assert anomalies[0]["severity"] == "high"
    assert anomalies[0]["confidence"] > 0.8
    # A finding explains itself: the signals that led to it are listed.
    assert "extreme_batch_global" in anomalies[0]["signals"]
    assert result["money_at_risk"] > 0


def test_a_repeated_transaction_is_reported_as_a_duplicate():
    base = transactions()
    duplicate = base.iloc[3].to_dict()
    result = detect_financial_leaks(transactions([duplicate]))

    duplicates = findings_by_type(result)["duplicate_transaction"]
    assert duplicates[0]["transaction_id"] == "T003"
    assert duplicates[0]["evidence"]["occurrences"] == 2


def test_risk_score_without_findings_is_zero():
    result = calculate_risk_score([], {"total_rows": 100})

    assert result["score"] == 0.0
    assert result["level"] == "LOW"


def test_risk_score_stays_within_bounds():
    outliers = [
        {
            "transaction_id": f"X{i}",
            "amount": 500000 + i,
            "category": "Retail",
            "status": "failed",
            "entity_id": "C1",
            "transaction_date": "2026-08-15",
            "currency": "MAD",
        }
        for i in range(10)
    ]
    result = detect_financial_leaks(transactions(outliers))

    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_french_column_names_are_mapped_to_the_canonical_schema():
    frame = pd.DataFrame(
        {
            "payment_ref": ["A1", "A2"],
            "montant": [10.0, 20.0],
            "client": ["x", "y"],
            "date_operation": ["2026-01-01", "2026-01-02"],
            "statut": ["completed", "failed"],
        }
    )
    mapping = detect_schema_mapping(frame)

    assert mapping == {
        "payment_ref": "transaction_id",
        "montant": "amount",
        "client": "entity_id",
        "date_operation": "timestamp",
        "statut": "status",
    }
    assert validate_mapping(frame, mapping)["valid"] is True


def test_an_empty_mapping_is_invalid():
    frame = pd.DataFrame({"a": [1]})
    assert validate_mapping(frame, {})["valid"] is False
