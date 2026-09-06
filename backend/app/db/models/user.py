from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User table. Real authentication is not implemented yet; a single
    static/mock user row is seeded on startup and used for all requests."""

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    documents = relationship("LegalDocument", back_populates="user", cascade="all, delete-orphan")
    resolution_plan_generations = relationship(
        "ResolutionPlanGeneration", back_populates="user", cascade="all, delete-orphan"
    )
