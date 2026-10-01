from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ========================================================
    # CLIENT PROFILE
    # ========================================================

    client_profile_id = Column(
        Integer,
        ForeignKey(
            "client_profiles.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # FILE / DATASET
    # ========================================================

    filename = Column(
        String(255),
        nullable=False,
    )

    rows = Column(
        Integer,
        nullable=False,
    )

    columns = Column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # RISK RESULT
    # ========================================================

    risk_score = Column(
        Float,
        nullable=False,
    )

    risk_level = Column(
        String(50),
        nullable=False,
    )

    # ========================================================
    # FINDINGS DISTRIBUTION
    # ========================================================

    total_findings = Column(
        Integer,
        nullable=False,
    )

    high_risk = Column(
        Integer,
        nullable=False,
    )

    medium_risk = Column(
        Integer,
        nullable=False,
    )

    low_risk = Column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # FINANCIAL EXPOSURE
    # ========================================================

    money_at_risk = Column(
        Float,
        nullable=False,
    )

    # ========================================================
    # AI SUMMARY
    # ========================================================

    ai_summary = Column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    client_profile = relationship(
        "ClientProfile",
        back_populates="analyses",
    )

    findings = relationship(
        "Finding",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )