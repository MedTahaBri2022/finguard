from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from typing import Any, Dict, Optional

import requests


FRANKFURTER_BASE_URL = (
    "https://api.frankfurter.dev/v2"
)

BASE_CURRENCY = "MAD"

REQUEST_TIMEOUT_SECONDS = 8


class FXService:
    def __init__(self):
        self.base_url = FRANKFURTER_BASE_URL

    # ========================================================
    # DATE NORMALIZATION
    # ========================================================

    def _normalize_date(
        self,
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date().isoformat()

        if isinstance(value, date):
            return value.isoformat()

        text = str(value).strip()

        if not text:
            return None

        try:
            parsed = datetime.fromisoformat(
                text[:10]
            )

            return parsed.date().isoformat()

        except ValueError:
            return None

    # ========================================================
    # GET HISTORICAL RATE
    # ========================================================

    @lru_cache(maxsize=10000)
    def get_historical_rate(
        self,
        from_currency: str,
        transaction_date: str,
    ) -> Dict[str, Any]:

        currency = (
            str(from_currency)
            .strip()
            .upper()
        )

        normalized_date = self._normalize_date(
            transaction_date
        )

        # MAD → MAD
        if currency == BASE_CURRENCY:
            return {
                "success": True,
                "from_currency": "MAD",
                "to_currency": "MAD",
                "rate": 1.0,
                "requested_date":
                    normalized_date,
                "effective_date":
                    normalized_date,
                "provider":
                    "identity",
                "historical":
                    True,
            }

        if not normalized_date:
            return {
                "success": False,
                "rate": None,
                "error":
                    "Transaction date is missing or invalid.",
            }

        try:
            url = (
                f"{self.base_url}/rate/"
                f"{currency}/{BASE_CURRENCY}"
            )

            params = {
                "date": normalized_date,

                # Bank Al-Maghrib source when available.
                "providers": "BAM",
            }

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            # ------------------------------------------------
            # First attempt:
            # Bank Al-Maghrib
            # ------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                rate = self._extract_rate(
                    data
                )

                if rate is not None:

                    effective_date = (
                        self._extract_date(
                            data
                        )
                        or normalized_date
                    )

                    return {
                        "success": True,
                        "from_currency":
                            currency,
                        "to_currency":
                            BASE_CURRENCY,
                        "rate":
                            rate,
                        "requested_date":
                            normalized_date,
                        "effective_date":
                            effective_date,
                        "provider":
                            "BAM",
                        "historical":
                            True,
                    }

            # ------------------------------------------------
            # Second attempt:
            # blended providers
            # ------------------------------------------------

            params = {
                "date": normalized_date,
            }

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "rate": None,
                    "error": (
                        "FX provider returned "
                        f"HTTP {response.status_code}."
                    ),
                }

            data = response.json()

            rate = self._extract_rate(
                data
            )

            if rate is None:
                return {
                    "success": False,
                    "rate": None,
                    "error":
                        "FX rate was not found.",
                }

            effective_date = (
                self._extract_date(
                    data
                )
                or normalized_date
            )

            return {
                "success": True,
                "from_currency":
                    currency,
                "to_currency":
                    BASE_CURRENCY,
                "rate":
                    rate,
                "requested_date":
                    normalized_date,
                "effective_date":
                    effective_date,
                "provider":
                    "Frankfurter",
                "historical":
                    True,
            }

        except requests.RequestException as error:

            return {
                "success": False,
                "rate": None,
                "error": (
                    f"FX provider unavailable: "
                    f"{error}"
                ),
            }

        except Exception as error:

            return {
                "success": False,
                "rate": None,
                "error": (
                    f"Unexpected FX error: "
                    f"{error}"
                ),
            }

    # ========================================================
    # RESPONSE PARSER
    # ========================================================

    def _extract_rate(
        self,
        data: Any,
    ) -> Optional[float]:

        if data is None:
            return None

        # Frankfurter v2 /rate response may be
        # represented as a single object or list.

        if isinstance(data, list):

            if not data:
                return None

            candidate = data[0]

            if not isinstance(
                candidate,
                dict,
            ):
                return None

            value = (
                candidate.get("rate")
                or candidate.get("value")
            )

        elif isinstance(
            data,
            dict,
        ):

            value = (
                data.get("rate")
                or data.get("value")
            )

        else:
            return None

        try:
            rate = float(value)

            if rate <= 0:
                return None

            return rate

        except (
            TypeError,
            ValueError,
        ):
            return None

    def _extract_date(
        self,
        data: Any,
    ) -> Optional[str]:

        if isinstance(data, list):

            if not data:
                return None

            data = data[0]

        if not isinstance(
            data,
            dict,
        ):
            return None

        value = (
            data.get("date")
            or data.get("effective_date")
        )

        if not value:
            return None

        return str(value)[:10]

    # ========================================================
    # CONVERSION
    # ========================================================

    def convert_to_mad(
        self,
        amount: float,
        currency: str,
        transaction_date: str,
    ) -> Dict[str, Any]:

        try:
            numeric_amount = float(
                amount
            )

        except (
            TypeError,
            ValueError,
        ):
            return {
                "success": False,
                "normalized_amount_mad":
                    None,
                "rate":
                    None,
                "error":
                    "Invalid amount.",
            }

        if numeric_amount < 0:
            return {
                "success": False,
                "normalized_amount_mad":
                    None,
                "rate":
                    None,
                "error":
                    "Negative amount cannot be converted.",
            }

        rate_result = (
            self.get_historical_rate(
                from_currency=currency,
                transaction_date=(
                    transaction_date
                ),
            )
        )

        if not rate_result.get(
            "success"
        ):
            return {
                **rate_result,
                "normalized_amount_mad":
                    None,
            }

        rate = float(
            rate_result["rate"]
        )

        normalized_amount = (
            numeric_amount
            * rate
        )

        return {
            **rate_result,
            "original_amount":
                numeric_amount,
            "normalized_amount_mad":
                float(
                    normalized_amount
                ),
        }


fx_service = FXService()