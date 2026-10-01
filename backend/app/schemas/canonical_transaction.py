from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class CanonicalTransaction:
    """
    Internal normalized transaction representation used by FinGuard.

    External client files may have different column names.
    SchemaMapper converts them into this canonical structure.
    """

    transaction_id: Optional[str] = None
    entity_id: Optional[str] = None

    amount: Optional[float] = None
    currency: Optional[str] = None

    timestamp: Optional[datetime] = None

    status: Optional[str] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None

    balance: Optional[float] = None
    merchant: Optional[str] = None

    # Optional original source metadata.
    source_row_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)