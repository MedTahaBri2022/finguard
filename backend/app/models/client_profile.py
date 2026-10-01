from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    business_type = Column(
        String(100),
        nullable=True,
    )

    base_currency = Column(
        String(10),
        nullable=False,
        default="MAD",
    )

    risk_tolerance = Column(
        String(50),
        nullable=False,
        default="medium",
    )

    column_mapping_json = Column(
        Text,
        nullable=True,
    )

    business_rules_json = Column(
        Text,
        nullable=True,
    )

    failure_rate_warning = Column(
        Float,
        nullable=True,
    )

    refund_rate_warning = Column(
        Float,
        nullable=True,
    )

    high_amount_multiplier = Column(
        Float,
        nullable=True,
        default=3.0,
    )

    baseline_ready = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    minimum_history_rows = Column(
        Integer,
        nullable=False,
        default=500,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    analyses = relationship(
        "Analysis",
        back_populates="client_profile",
    )

    baselines = relationship(
        "ClientBaseline",
        back_populates="client_profile",
    )

    users = relationship(
        "User",
        back_populates="client_profile",
    )