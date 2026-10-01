from typing import Any, Dict, Optional

import re

import pandas as pd

from app.services.fx_service import (
    fx_service,
)


BASE_CURRENCY = "MAD"


CURRENCY_ALIASES = {
    # MAD
    "mad": "MAD",
    "dh": "MAD",
    "dhs": "MAD",
    "dirham": "MAD",
    "dirhams": "MAD",

    # USD
    "usd": "USD",
    "us$": "USD",
    "dollar": "USD",
    "dollars": "USD",

    # EUR
    "eur": "EUR",
    "€": "EUR",
    "euro": "EUR",
    "euros": "EUR",

    # GBP
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
}


# ============================================================
# HELPERS
# ============================================================

def _is_missing(
    value: Any,
) -> bool:

    if value is None:
        return True

    try:
        return bool(
            pd.isna(value)
        )

    except Exception:
        return False


# ============================================================
# CURRENCY NORMALIZATION
# ============================================================

def normalize_currency(
    value: Any,
) -> Optional[str]:

    if _is_missing(
        value
    ):
        return None

    text = (
        str(value)
        .strip()
        .lower()
    )

    if not text:
        return None

    if text in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[
            text
        ]

    # ISO currency code
    if re.fullmatch(
        r"[A-Za-z]{3}",
        text,
    ):

        return text.upper()

    return None


# ============================================================
# CURRENCY DETECTION INSIDE AMOUNT TEXT
# ============================================================

def detect_currency_from_text(
    value: Any,
) -> Optional[str]:

    if _is_missing(
        value
    ):
        return None

    text = (
        str(value)
        .strip()
        .lower()
    )

    if not text:
        return None

    # EUR is considered sufficiently explicit.
    if "€" in text:
        return "EUR"

    # IMPORTANT:
    #
    # "$" alone can represent multiple currencies.
    # "£" can also be ambiguous.
    #
    # Therefore FinGuard does NOT automatically
    # interpret bare $ as USD or bare £ as GBP.

    patterns = {
        "MAD": [
            r"\bmad\b",
            r"\bdh\b",
            r"\bdhs\b",
            r"\bdirham\b",
            r"\bdirhams\b",
        ],

        "USD": [
            r"\busd\b",
            r"\bus\$\b",
            r"\bus dollars?\b",
        ],

        "EUR": [
            r"\beur\b",
            r"\beuros?\b",
        ],

        "GBP": [
            r"\bgbp\b",
            r"\bpounds?\b",
            r"\bpound sterling\b",
        ],
    }

    for (
        currency,
        currency_patterns,
    ) in patterns.items():

        for pattern in (
            currency_patterns
        ):

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):

                return currency

    return None


# ============================================================
# AMOUNT PARSER
# ============================================================

def parse_numeric_amount(
    value: Any,
) -> Optional[float]:

    if _is_missing(
        value
    ):
        return None

    if isinstance(
        value,
        (int, float),
    ):

        try:
            return float(value)

        except Exception:
            return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    # Accounting negative:
    #
    # (1,250.50)
    # =
    # -1250.50

    negative_parentheses = (
        text.startswith("(")
        and text.endswith(")")
    )

    cleaned = text

    replacements = [
        "MAD",
        "mad",
        "DHS",
        "dhs",
        "DH",
        "dh",
        "USD",
        "usd",
        "EUR",
        "eur",
        "GBP",
        "gbp",

        "dirhams",
        "dirham",

        "dollars",
        "dollar",

        "euros",
        "euro",

        "pounds",
        "pound",

        "$",
        "€",
        "£",
    ]

    for replacement in (
        replacements
    ):

        cleaned = (
            cleaned.replace(
                replacement,
                "",
            )
        )

    # Spaces are often thousand separators.
    cleaned = (
        cleaned
        .replace(
            "\u00A0",
            "",
        )
        .replace(
            " ",
            "",
        )
    )

    cleaned = re.sub(
        r"[^0-9,.\-]",
        "",
        cleaned,
    )

    if not cleaned:
        return None

    # ========================================================
    # 1,234.56
    # 1.234,56
    # 1234,56
    # 1,234
    # ========================================================

    if (
        "," in cleaned
        and "." in cleaned
    ):

        last_comma = (
            cleaned.rfind(",")
        )

        last_dot = (
            cleaned.rfind(".")
        )

        if last_comma > last_dot:

            cleaned = (
                cleaned
                .replace(".", "")
                .replace(",", ".")
            )

        else:

            cleaned = (
                cleaned
                .replace(",", "")
            )

    elif "," in cleaned:

        parts = (
            cleaned.split(",")
        )

        if (
            len(parts) == 2
            and len(parts[1]) <= 2
        ):

            cleaned = (
                cleaned
                .replace(",", ".")
            )

        else:

            cleaned = (
                cleaned
                .replace(",", "")
            )

    try:

        result = float(
            cleaned
        )

        if negative_parentheses:
            result = -abs(
                result
            )

        return result

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# MAIN NORMALIZER
# ============================================================

def normalize_transaction_amount(
    amount_value: Any,
    currency_value: Any = None,
    inferred_currency: Optional[
        str
    ] = None,
    transaction_date: Any = None,
) -> Dict[str, Any]:

    original_amount = (
        parse_numeric_amount(
            amount_value
        )
    )

    if original_amount is None:

        return {
            "success":
                False,

            "original_amount":
                None,

            "original_currency":
                None,

            "normalized_amount_mad":
                None,

            "fx_rate":
                None,

            "fx_rate_date":
                None,

            "fx_provider":
                None,

            "currency_confidence":
                0.0,

            "currency_source":
                "unknown",

            "currency_conflict":
                False,

            "conversion_applied":
                False,

            "normalization_status":
                "invalid_amount",

            "base_currency":
                BASE_CURRENCY,
        }

    # ========================================================
    # CURRENCY SIGNALS
    # ========================================================

    explicit_currency = (
        normalize_currency(
            currency_value
        )
    )

    embedded_currency = (
        detect_currency_from_text(
            amount_value
        )
    )

    # ========================================================
    # CONFLICT
    # ========================================================

    currency_conflict = (
        explicit_currency is not None
        and embedded_currency is not None
        and explicit_currency
        != embedded_currency
    )

    if currency_conflict:

        return {
            "success":
                False,

            "original_amount":
                float(
                    original_amount
                ),

            "original_currency":
                None,

            "explicit_currency":
                explicit_currency,

            "embedded_currency":
                embedded_currency,

            "normalized_amount_mad":
                None,

            "fx_rate":
                None,

            "fx_rate_date":
                None,

            "fx_provider":
                None,

            "currency_confidence":
                0.0,

            "currency_source":
                "conflict",

            "currency_conflict":
                True,

            "conversion_applied":
                False,

            "normalization_status":
                "currency_conflict",

            "base_currency":
                BASE_CURRENCY,
        }

    # ========================================================
    # CURRENCY PRIORITY
    # ========================================================

    currency = None
    confidence = 0.0
    source = "unknown"

    if explicit_currency:

        currency = (
            explicit_currency
        )

        confidence = 1.0

        source = (
            "currency_column"
        )

    elif embedded_currency:

        currency = (
            embedded_currency
        )

        confidence = 0.98

        source = (
            "amount_text"
        )

    elif inferred_currency:

        normalized_inferred = (
            normalize_currency(
                inferred_currency
            )
        )

        if normalized_inferred:

            currency = (
                normalized_inferred
            )

            confidence = 0.80

            source = (
                "dataset_inference"
            )

    # ========================================================
    # UNKNOWN != MAD
    # ========================================================

    if currency is None:

        return {
            "success":
                True,

            "original_amount":
                float(
                    original_amount
                ),

            "original_currency":
                "UNKNOWN",

            "normalized_amount_mad":
                None,

            "fx_rate":
                None,

            "fx_rate_date":
                None,

            "fx_provider":
                None,

            "currency_confidence":
                0.0,

            "currency_source":
                "unknown",

            "currency_conflict":
                False,

            "conversion_applied":
                False,

            "normalization_status":
                "unknown_currency",

            "base_currency":
                BASE_CURRENCY,
        }

    # ========================================================
    # MAD
    #
    # No external FX request needed.
    # ========================================================

    if currency == BASE_CURRENCY:

        return {
            "success":
                True,

            "original_amount":
                float(
                    original_amount
                ),

            "original_currency":
                "MAD",

            "normalized_amount_mad":
                float(
                    original_amount
                ),

            "fx_rate":
                1.0,

            "fx_rate_date":
                None,

            "fx_provider":
                "identity",

            "currency_confidence":
                confidence,

            "currency_source":
                source,

            "currency_conflict":
                False,

            "conversion_applied":
                False,

            "normalization_status":
                "normalized",

            "base_currency":
                BASE_CURRENCY,
        }

    # ========================================================
    # FOREIGN CURRENCY REQUIRES TRANSACTION DATE
    # ========================================================

    if _is_missing(
        transaction_date
    ):

        return {
            "success":
                False,

            "original_amount":
                float(
                    original_amount
                ),

            "original_currency":
                currency,

            "normalized_amount_mad":
                None,

            "fx_rate":
                None,

            "fx_rate_date":
                None,

            "fx_provider":
                None,

            "currency_confidence":
                confidence,

            "currency_source":
                source,

            "currency_conflict":
                False,

            "conversion_applied":
                False,

            "normalization_status":
                "missing_fx_date",

            "base_currency":
                BASE_CURRENCY,
        }

    # ========================================================
    # HISTORICAL FX
    # ========================================================

    fx_result = (
        fx_service.convert_to_mad(
            amount=(
                original_amount
            ),

            currency=(
                currency
            ),

            transaction_date=(
                transaction_date
            ),
        )
    )

    if not fx_result.get(
        "success"
    ):

        return {
            "success":
                False,

            "original_amount":
                float(
                    original_amount
                ),

            "original_currency":
                currency,

            "normalized_amount_mad":
                None,

            "fx_rate":
                None,

            "fx_rate_date":
                None,

            "fx_provider":
                None,

            "fx_error":
                fx_result.get(
                    "error"
                ),

            "currency_confidence":
                confidence,

            "currency_source":
                source,

            "currency_conflict":
                False,

            "conversion_applied":
                False,

            "normalization_status":
                "fx_unavailable",

            "base_currency":
                BASE_CURRENCY,
        }

    return {
        "success":
            True,

        "original_amount":
            float(
                original_amount
            ),

        "original_currency":
            currency,

        "normalized_amount_mad":
            float(
                fx_result[
                    "normalized_amount_mad"
                ]
            ),

        "fx_rate":
            float(
                fx_result[
                    "rate"
                ]
            ),

        "fx_rate_date":
            fx_result.get(
                "effective_date"
            ),

        "fx_provider":
            fx_result.get(
                "provider"
            ),

        "currency_confidence":
            confidence,

        "currency_source":
            source,

        "currency_conflict":
            False,

        "conversion_applied":
            True,

        "normalization_status":
            "normalized_historical_fx",

        "base_currency":
            BASE_CURRENCY,
    }