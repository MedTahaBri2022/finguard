from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):

    __tablename__ = "alerts"

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
        nullable=True,
        index=True,
    )

    client_profile_id = Column(
        Integer,
        ForeignKey(
            "client_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    alert_type = Column(
        String(100),
        nullable=False,
    )

    severity = Column(
        String(50),
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

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    analysis = relationship(
        "Analysis",
    )

    client_profile = relationship(
        "ClientProfile",
    )