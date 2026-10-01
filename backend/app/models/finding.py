from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    analysis_id = Column(
        Integer,
        ForeignKey(
            "analyses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    type = Column(
        String(100),
        nullable=False,
    )

    severity = Column(
        String(50),
        nullable=False,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    amount_at_risk = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    transaction_id = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    analysis = relationship(
        "Analysis",
        back_populates="findings",
    )

    def __repr__(self):
        return (
            f"<Finding("
            f"id={self.id}, "
            f"analysis_id={self.analysis_id}, "
            f"type={self.type}, "
            f"severity={self.severity}"
            f")>"
        )