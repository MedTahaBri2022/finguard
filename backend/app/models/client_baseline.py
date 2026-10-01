from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class ClientBaseline(Base):
    __tablename__ = "client_baselines"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ========================================================
    # CLIENT
    # ========================================================

    client_profile_id = Column(
        Integer,
        ForeignKey(
            "client_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # BASELINE VERSION
    # ========================================================

    version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    # Number of historical transactions used
    # to calculate this baseline.
    sample_size = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # BASELINE DATA
    # ========================================================

    # JSON containing statistical behaviour.
    #
    # Example:
    #
    # {
    #   "amount": {
    #       "median": 250.0,
    #       "p95": 1200.0,
    #       "p99": 3200.0,
    #       "mad": 150.0
    #   },
    #
    #   "failure_rate": 0.025,
    #   "refund_rate": 0.018,
    #
    #   "categories": {
    #       "restaurant": {
    #           "median": 180,
    #           "p95": 600,
    #           "count": 350
    #       }
    #   }
    # }

    baseline_json = Column(
        Text,
        nullable=False,
    )

    # ========================================================
    # STATUS
    # ========================================================

    # Only one baseline should normally be active
    # for a given client.
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ========================================================
    # CREATED DATE
    # ========================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # ========================================================
    # RELATIONSHIP
    # ========================================================

    client_profile = relationship(
        "ClientProfile",
        back_populates="baselines",
    )