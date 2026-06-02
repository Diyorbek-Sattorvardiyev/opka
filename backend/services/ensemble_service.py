from dataclasses import asdict, dataclass

from services.prediction_service import ModelPrediction, available_predictions, calculate_risk_level, confidence_from_probability


@dataclass
class EnsemblePrediction:
    pneumonia_detected: bool
    confidence: float
    probability: float
    risk_level: str
    method: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_dynamic_ensemble(results: list[ModelPrediction]) -> EnsemblePrediction:
    available = available_predictions(results)
    if not available:
        raise ValueError("Tahlil uchun mavjud model topilmadi")

    probabilities = [float(result.probability or 0.0) for result in available]
    average_probability = round(sum(probabilities) / len(probabilities), 4)

    if len(available) == 1:
        single = available[0]
        detected = bool(single.pneumonia_detected)
        probability = float(single.probability or 0.0)
        method = "single_model"
    elif len(available) == 2:
        detected = average_probability >= 0.5
        probability = average_probability
        method = "two_model_average"
    else:
        votes = sum(1 for result in available if result.pneumonia_detected)
        detected = votes >= 2
        probability = average_probability
        method = "majority_vote_average"

    return EnsemblePrediction(
        pneumonia_detected=detected,
        confidence=confidence_from_probability(probability, detected),
        probability=round(probability, 4),
        risk_level=calculate_risk_level(probability),
        method=method,
    )
