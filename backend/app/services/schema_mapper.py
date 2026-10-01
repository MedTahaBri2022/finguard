from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# ============================================================
# CANONICAL FIELDS
# ============================================================

CANONICAL_FIELDS = {
    "transaction_id",
    "entity_id",
    "amount",
    "currency",
    "timestamp",
    "status",
    "transaction_type",
    "category",
    "balance",
    "merchant",
}


# ============================================================
# COLUMN ALIASES
#
# These are suggestions only.
# Client-confirmed mapping always has priority.
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {

    "transaction_id": [
        "transaction_id",
        "transactionid",
        "txn_id",
        "tx_id",
        "payment_id",
        "paymentid",
        "operation_id",
        "operationid",
        "reference",
        "reference_id",
        "transaction_reference",
        "payment_reference",
        "payment_ref",
        "operation_reference",
        "ref",
        "id_transaction",
        "id_operation",
    ],

    "entity_id": [
        "entity_id",
        "customer_id",
        "customerid",
        "client_id",
        "clientid",
        "account_id",
        "accountid",
        "account_number",
        "account_no",
        "user_id",
        "userid",
        "card_id",
        "card_number",
        "customer",
        "client",
        "account",
        "compte",
        "numero_compte",
        "num_compte",
    ],

    "amount": [
        "amount",
        "transaction_amount",
        "payment_amount",
        "operation_amount",
        "total_amount",
        "total",
        "value",
        "transaction_value",
        "payment_value",
        "montant",
        "montant_transaction",
        "montant_operation",
        "valeur",
    ],

    "currency": [
        "currency",
        "currency_code",
        "currencycode",
        "devise",
        "monnaie",
        "ccy",
    ],

    "timestamp": [
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
        "date_paiement",
    ],

    "status": [
        "status",
        "transaction_status",
        "payment_status",
        "operation_status",
        "state",
        "etat",
        "statut",
    ],

    "transaction_type": [
        "transaction_type",
        "payment_type",
        "operation_type",
        "type",
        "type_transaction",
        "type_operation",
        "nature",
    ],

    "category": [
        "category",
        "merchant_category",
        "transaction_category",
        "payment_category",
        "operation_category",
        "categorie",
        "catégorie",
        "category_name",
        "merchant_category_name",
    ],

    "balance": [
        "balance",
        "balance_after",
        "account_balance",
        "available_balance",
        "new_balance",
        "solde",
        "solde_apres",
        "solde_après",
    ],

    "merchant": [
        "merchant",
        "merchant_name",
        "merchant_id",
        "vendor",
        "vendor_name",
        "supplier",
        "supplier_name",
        "commercant",
        "commerçant",
        "fournisseur",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def _normalize_column_name(
    value: Any,
) -> str:

    text = str(
        value
    ).strip().lower()

    replacements = {
        "-": "_",
        " ": "_",
        ".": "_",
        "/": "_",
        "\\": "_",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    while "__" in text:
        text = text.replace(
            "__",
            "_",
        )

    return text.strip("_")


def _build_normalized_column_lookup(
    df: pd.DataFrame,
) -> Dict[str, str]:

    return {
        _normalize_column_name(
            column
        ): column

        for column
        in df.columns
    }


# ============================================================
# AUTOMATIC MAPPING
# ============================================================

def detect_schema_mapping(
    df: pd.DataFrame,
) -> Dict[str, str]:
    """
    Automatically proposes a mapping:

        source column -> canonical field

    Example:
        {
            "payment_ref": "transaction_id",
            "customer_id": "entity_id",
            "montant": "amount"
        }

    This is a proposal only.
    In production the client/admin should confirm it.
    """

    if df is None or df.empty:
        return {}

    normalized_lookup = (
        _build_normalized_column_lookup(
            df
        )
    )

    mapping: Dict[str, str] = {}

    already_used_source_columns = set()

    for (
        canonical_field,
        aliases,
    ) in COLUMN_ALIASES.items():

        candidates = [
            canonical_field,
            *aliases,
        ]

        for candidate in candidates:

            normalized_candidate = (
                _normalize_column_name(
                    candidate
                )
            )

            if (
                normalized_candidate
                in normalized_lookup
            ):

                real_source_column = (
                    normalized_lookup[
                        normalized_candidate
                    ]
                )

                if (
                    real_source_column
                    not in already_used_source_columns
                ):

                    mapping[
                        real_source_column
                    ] = canonical_field

                    already_used_source_columns.add(
                        real_source_column
                    )

                    break

    return mapping


# ============================================================
# VALIDATION
# ============================================================

def validate_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, str],
) -> Dict[str, Any]:

    errors: List[str] = []

    warnings: List[str] = []

    if df is None:
        return {
            "valid": False,
            "errors": [
                "DataFrame is missing."
            ],
            "warnings": [],
        }

    if not mapping:
        return {
            "valid": False,
            "errors": [
                "No schema mapping was provided."
            ],
            "warnings": [],
        }

    canonical_targets = set()

    for (
        source_column,
        canonical_field,
    ) in mapping.items():

        if source_column not in df.columns:

            errors.append(
                f"Source column '{source_column}' "
                f"does not exist in the dataset."
            )

        if (
            canonical_field
            not in CANONICAL_FIELDS
        ):

            errors.append(
                f"'{canonical_field}' is not "
                f"a supported FinGuard canonical field."
            )

        if (
            canonical_field
            in canonical_targets
        ):

            errors.append(
                f"Canonical field "
                f"'{canonical_field}' is mapped "
                f"more than once."
            )

        canonical_targets.add(
            canonical_field
        )

    # Amount is the only strongly required
    # financial field for current detector.

    if "amount" not in canonical_targets:

        errors.append(
            "The dataset must have a column "
            "mapped to the canonical 'amount' field."
        )

    if "transaction_id" not in canonical_targets:

        warnings.append(
            "No transaction ID was mapped. "
            "FinGuard will have reduced ability "
            "to detect duplicates and track findings."
        )

    if "currency" not in canonical_targets:

        warnings.append(
            "No currency column was mapped. "
            "Currency detection may rely on "
            "embedded values or client defaults."
        )

    if "timestamp" not in canonical_targets:

        warnings.append(
            "No timestamp column was mapped. "
            "Historical FX and temporal analysis "
            "may be limited."
        )

    if "entity_id" not in canonical_targets:

        warnings.append(
            "No customer/account/entity field "
            "was mapped. Entity-level behavioral "
            "analysis will be unavailable."
        )

    return {
        "valid":
            len(
                errors
            )
            == 0,

        "errors":
            errors,

        "warnings":
            warnings,
    }


# ============================================================
# APPLY MAPPING
# ============================================================

def apply_schema_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    keep_unmapped_columns: bool = True,
) -> pd.DataFrame:
    """
    Renames client columns to FinGuard canonical names.

    Example:
        payment_ref -> transaction_id
        customer    -> entity_id
        montant     -> amount
    """

    validation = (
        validate_mapping(
            df,
            mapping,
        )
    )

    if not validation[
        "valid"
    ]:

        raise ValueError(
            "Invalid schema mapping: "
            + "; ".join(
                validation[
                    "errors"
                ]
            )
        )

    renamed = df.rename(
        columns=mapping
    ).copy()

    if not keep_unmapped_columns:

        available_canonical_columns = [
            column

            for column
            in renamed.columns

            if column
            in CANONICAL_FIELDS
        ]

        renamed = renamed[
            available_canonical_columns
        ].copy()

    return renamed


# ============================================================
# AUTO MAP + APPLY
# ============================================================

def automatically_map_dataframe(
    df: pd.DataFrame,
    keep_unmapped_columns: bool = True,
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any],
]:
    """
    Convenience method for development/testing.

    In final client onboarding:
    detect -> show proposal -> confirm -> save ClientProfile
    """

    mapping = (
        detect_schema_mapping(
            df
        )
    )

    validation = (
        validate_mapping(
            df,
            mapping,
        )
    )

    if not validation[
        "valid"
    ]:

        return (
            df.copy(),
            {
                "mapping":
                    mapping,

                "valid":
                    False,

                "errors":
                    validation[
                        "errors"
                    ],

                "warnings":
                    validation[
                        "warnings"
                    ],
            },
        )

    mapped_df = (
        apply_schema_mapping(
            df,
            mapping,
            keep_unmapped_columns=(
                keep_unmapped_columns
            ),
        )
    )

    return (
        mapped_df,
        {
            "mapping":
                mapping,

            "valid":
                True,

            "errors":
                [],

            "warnings":
                validation[
                    "warnings"
                ],

            "canonical_fields_detected":
                sorted(
                    mapping.values()
                ),

            "source_columns_mapped":
                sorted(
                    mapping.keys()
                ),
        },
    )