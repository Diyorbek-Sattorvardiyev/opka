from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    original_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    heatmap_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    pneumonia_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    final_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ensemble_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    available_models_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unavailable_models: Mapped[list | None] = mapped_column(JSON, nullable=True)
    model_results: Mapped[list | None] = mapped_column(JSON, nullable=True)
    covxnet_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    covxnet_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    covxnet_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    cnn_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    cnn_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cnn_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ensemble_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    ensemble_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ensemble_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    selected_model_for_heatmap: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="analyses")
