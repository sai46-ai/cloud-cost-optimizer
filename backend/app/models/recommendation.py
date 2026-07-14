"""Recommendation model with savings estimates and priority."""

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # EC2, RDS, S3, EBS, ELB, EIP
    category: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # rightsizing, reserved, savings_plan, lifecycle, migration
    recommendation: Mapped[str] = mapped_column(String(2000), nullable=False)
    current_cost: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_cost: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_savings: Mapped[float] = mapped_column(Float, default=0.0)
    annual_savings: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, accepted, dismissed, implemented
    difficulty: Mapped[str] = mapped_column(
        String(20), default="easy"
    )  # easy, moderate, complex

    # Relationships
    user = relationship("User", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation {self.service} save=${self.monthly_savings:.2f}/mo>"


class DemoRecommendation(Base, TimestampMixin):
    __tablename__ = "demo_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    recommendation: Mapped[str] = mapped_column(String(2000), nullable=False)
    current_cost: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_cost: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_savings: Mapped[float] = mapped_column(Float, default=0.0)
    annual_savings: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")

    # Relationships
    user = relationship("User", back_populates="demo_recommendations", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DemoRecommendation {self.service} save=${self.monthly_savings:.2f}/mo>"


class AWSRecommendation(Base, TimestampMixin):
    __tablename__ = "aws_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    recommendation: Mapped[str] = mapped_column(String(2000), nullable=False)
    current_cost: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_cost: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_savings: Mapped[float] = mapped_column(Float, default=0.0)
    annual_savings: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")

    # Relationships
    user = relationship("User", back_populates="aws_recommendations", lazy="selectin")

    def __repr__(self) -> str:
        return f"<AWSRecommendation {self.service} save=${self.monthly_savings:.2f}/mo>"
