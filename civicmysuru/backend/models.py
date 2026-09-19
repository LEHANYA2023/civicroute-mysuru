from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(30), primary_key=True, index=True)

    citizen_name = Column(String(100), nullable=False)
    area = Column(String(120), nullable=False)
    issue_type = Column(String(80), nullable=False)
    location = Column(String(300), nullable=True)
    description = Column(Text, nullable=False)

    authority = Column(String(150), nullable=False)
    department = Column(String(150), nullable=False)
    jurisdiction = Column(String(150), nullable=False)
    routing_reason = Column(String(500), nullable=True)
    routing_mode = Column(String(50), nullable=False, default="Standard")
    jurisdiction_match_quality = Column(String(30), nullable=False, default="matched")

    reused_evidence_flag = Column(Boolean, nullable=False, default=False)
    reused_evidence_reason = Column(String(255), nullable=True)

    priority = Column(String(30), nullable=False)
    priority_score = Column(Integer, nullable=False, default=0)

    verification_score = Column(Integer, nullable=False, default=0)
    verification_status = Column(String(50), nullable=False, default="Needs Review")

    duplicate = Column(Boolean, nullable=False, default=False)

    status = Column(String(30), nullable=False, default="Open")
    image_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )

