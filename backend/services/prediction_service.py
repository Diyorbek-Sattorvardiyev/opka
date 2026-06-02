from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from services.model_loader import LoadedModel, model_loader
from services.preprocess_service import preprocess_for_model


@dataclass
class ModelPrediction:
    key: str
    name: str
    available: bool
    pneumonia_detected: bool | None = None
    probability: float | None = None
    confidence: float | None = None
    risk_level: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def predict_all(rgb_image: np.ndarray) -> list[ModelPrediction]:
    results: list[ModelPrediction] = []
    for loaded_model in model_loader.all_models():
        if not loaded_model.available or loaded_model.model is None:
            results.append(
                ModelPrediction(
                    key=loaded_model.key,
                    name=loaded_model.name,
                    available=False,
                    message=loaded_model.message or "Model hali ulanmagan",
                )
            )
            continue
        results.append(_predict_one(loaded_model, rgb_image))
    return results


def available_predictions(results: list[ModelPrediction]) -> list[ModelPrediction]:
    return [result for result in results if result.available and result.probability is not None]


def best_prediction_for_heatmap(results: list[ModelPrediction]) -> ModelPrediction | None:
    available = available_predictions(results)
    if not available:
        return None
    return max(available, key=lambda item: float(item.confidence or 0.0))


def calculate_risk_level(probability: float) -> str:
    if probability < 0.5:
        return "NORMAL"
    if probability < 0.75:
        return "RISK"
    return "CRITICAL"


def confidence_from_probability(probability: float, detected: bool) -> float:
    confidence = probability * 100 if detected else (1 - probability) * 100
    return round(float(confidence), 2)


def _predict_one(loaded_model: LoadedModel, rgb_image: np.ndarray) -> ModelPrediction:
    batch = preprocess_for_model(rgb_image, loaded_model)
    raw_prediction = loaded_model.model.predict(batch, verbose=0)
    probability = round(_pneumonia_probability(raw_prediction), 4)
    detected = probability >= 0.5
    return ModelPrediction(
        key=loaded_model.key,
        name=loaded_model.name,
        available=True,
        pneumonia_detected=detected,
        probability=probability,
        confidence=confidence_from_probability(probability, detected),
        risk_level=calculate_risk_level(probability),
    )


def _pneumonia_probability(prediction: Any) -> float:
    array = np.asarray(prediction, dtype="float32")
    if array.ndim == 0:
        probability = float(array)
    elif array.shape[-1] == 1:
        probability = float(array.reshape(-1)[0])
    elif array.shape[-1] >= 2:
        probability = float(array.reshape((-1, array.shape[-1]))[0][1])
    else:
        probability = float(array.reshape(-1)[0])
    return float(max(0.0, min(1.0, probability)))
