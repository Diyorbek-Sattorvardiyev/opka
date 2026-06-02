from datetime import datetime

from pydantic import BaseModel


DISCLAIMER = "Bu natija AI yordamchi tahlilidir, yakuniy tibbiy tashxis emas. Yakuniy tashxis uchun shifokorga murojaat qiling."


class AnalysisOut(BaseModel):
    id: int
    pneumonia_detected: bool
    confidence: float
    risk_level: str
    model_prediction: str
    ai_summary: str
    original_image_url: str
    heatmap_image_url: str
    created_at: datetime
    disclaimer: str = DISCLAIMER

    model_config = {"protected_namespaces": ()}


class ModelResultOut(BaseModel):
    model_name: str
    pneumonia_detected: bool
    confidence: float
    probability: float
    risk_level: str

    model_config = {"protected_namespaces": ()}


class EnsembleResultOut(BaseModel):
    method: str
    pneumonia_detected: bool
    confidence: float
    probability: float
    risk_level: str
    selected_model_for_heatmap: str


class EnsembleAnalysisOut(BaseModel):
    analysis_id: int
    original_image_url: str
    heatmap_image_url: str
    covxnet_result: ModelResultOut
    cnn_result: ModelResultOut
    ensemble_result: EnsembleResultOut
    ai_summary: str
    medical_disclaimer: str = DISCLAIMER
    created_at: datetime

    model_config = {"protected_namespaces": ()}


class AnalysisHistoryItem(BaseModel):
    id: int
    pneumonia_detected: bool
    confidence: float
    risk_level: str
    ai_summary: str
    original_image_url: str
    heatmap_image_url: str
    model_name: str
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class DashboardStats(BaseModel):
    total_scans: int
    pneumonia_detected_count: int
    normal_count: int
    average_confidence: float
    last_7_days_chart: list[dict[str, int | str]]
    risk_distribution: dict[str, int]
