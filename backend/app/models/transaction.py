from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
)

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    transaction_id = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    category = Column(
        String(100),
        nullable=True,
    )

    description = Column(
        String(500),
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=True,
    )

    customer = Column(
        String(255),
        nullable=True,
    )

    transaction_date = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<Transaction("
            f"id={self.id}, "
            f"transaction_id={self.transaction_id}, "
            f"amount={self.amount}"
            f")>"
        )