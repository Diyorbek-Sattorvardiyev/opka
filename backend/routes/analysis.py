from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, get_optional_current_user
from models.analysis import Analysis
from models.user import User
from schemas.analysis_schema import DISCLAIMER
from services.ensemble_service import EnsemblePrediction, build_dynamic_ensemble
from services.gemini_service import generate_ai_summary
from services.heatmap_service import create_heatmap
from services.image_preprocess_service import validate_and_save_upload
from services.model_loader import model_loader
from services.prediction_service import ModelPrediction, best_prediction_for_heatmap, predict_all


router = APIRouter(prefix="/analysis", tags=["analysis"])


def ok(message: str, data):
    return {"success": True, "message": message, "data": data}


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    if not model_loader.available_models():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tahlil uchun real model topilmadi. Kamida bitta .h5 model faylini backend/trained_model ichiga joylang.",
        )

    _, original_url, rgb_image = await validate_and_save_upload(file)
    model_results = predict_all(rgb_image)
    ensemble_result = build_dynamic_ensemble(model_results)

    best_model_result = best_prediction_for_heatmap(model_results)
    selected_model = model_loader.get(best_model_result.key) if best_model_result else None
    _, heatmap_url = create_heatmap(rgb_image, selected_model)

    unavailable_models = [item.key for item in model_results if not item.available]
    summary = generate_ai_summary(model_results, ensemble_result, unavailable_models)
    created_at = datetime.now(timezone.utc)

    analysis = Analysis(
        user_id=(current_user.id if current_user else _guest_user_id(db)),
        original_image_path=original_url,
        heatmap_image_path=heatmap_url,
        pneumonia_detected=ensemble_result.pneumonia_detected,
        confidence=ensemble_result.confidence,
        risk_level=ensemble_result.risk_level,
        ai_summary=summary,
        model_name=selected_model.name if selected_model else "dynamic_ensemble",
        final_probability=ensemble_result.probability,
        final_confidence=ensemble_result.confidence,
        final_detected=ensemble_result.pneumonia_detected,
        ensemble_method=ensemble_result.method,
        available_models_count=sum(1 for item in model_results if item.available),
        unavailable_models=unavailable_models,
        model_results=[item.to_dict() for item in model_results],
        ensemble_probability=ensemble_result.probability,
        ensemble_confidence=ensemble_result.confidence,
        ensemble_detected=ensemble_result.pneumonia_detected,
        selected_model_for_heatmap=selected_model.name if selected_model else None,
        created_at=created_at,
    )
    _fill_legacy_columns(analysis, model_results)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    data = _response_payload(
        analysis_id=analysis.id,
        original_url=original_url,
        heatmap_url=heatmap_url,
        model_results=model_results,
        ensemble_result=ensemble_result,
        summary=summary,
        created_at=analysis.created_at,
    )
    return ok("Tahlil yakunlandi", data)


@router.get("/history")
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Analysis).where(Analysis.user_id == current_user.id).order_by(desc(Analysis.created_at))
    ).all()
    return ok("Tahlillar tarixi", [_analysis_to_response(row) for row in rows])


@router.get("/{analysis_id}")
def detail(analysis_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.scalar(select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id))
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tahlil topilmadi")
    return ok("Tahlil ma'lumotlari", _analysis_to_response(analysis))


@router.delete("/{analysis_id}")
def delete(analysis_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.scalar(select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id))
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tahlil topilmadi")

    db.delete(analysis)
    db.commit()
    return ok("Tahlil o'chirildi", {"id": analysis_id})


def _response_payload(
    analysis_id: int,
    original_url: str,
    heatmap_url: str,
    model_results: list[ModelPrediction],
    ensemble_result: EnsemblePrediction,
    summary: str,
    created_at: datetime,
) -> dict:
    unavailable_models = [item.key for item in model_results if not item.available]
    return {
        "analysis_id": analysis_id,
        "id": analysis_id,
        "final_result": ensemble_result.to_dict(),
        "models": [item.to_dict() for item in model_results],
        "available_models_count": sum(1 for item in model_results if item.available),
        "unavailable_models": unavailable_models,
        "original_image_url": original_url,
        "heatmap_image_url": heatmap_url,
        "ai_summary": summary,
        "medical_disclaimer": DISCLAIMER,
        "created_at": created_at.isoformat(),
        "ensemble_result": ensemble_result.to_dict(),
    }


def _analysis_to_response(analysis: Analysis) -> dict:
    model_results = analysis.model_results or _legacy_model_results(analysis)
    ensemble = EnsemblePrediction(
        pneumonia_detected=bool(analysis.final_detected if analysis.final_detected is not None else analysis.pneumonia_detected),
        confidence=float(analysis.final_confidence if analysis.final_confidence is not None else analysis.confidence),
        probability=float(analysis.final_probability if analysis.final_probability is not None else (analysis.confidence / 100)),
        risk_level=analysis.risk_level,
        method=analysis.ensemble_method or "dynamic_ensemble",
    )
    return {
        "analysis_id": analysis.id,
        "id": analysis.id,
        "final_result": ensemble.to_dict(),
        "models": model_results,
        "available_models_count": analysis.available_models_count or sum(1 for item in model_results if item.get("available")),
        "unavailable_models": analysis.unavailable_models or [item["key"] for item in model_results if not item.get("available")],
        "original_image_url": analysis.original_image_path,
        "heatmap_image_url": analysis.heatmap_image_path,
        "ai_summary": analysis.ai_summary,
        "medical_disclaimer": DISCLAIMER,
        "created_at": analysis.created_at.isoformat(),
        "model_name": analysis.model_name,
        "pneumonia_detected": ensemble.pneumonia_detected,
        "confidence": ensemble.confidence,
        "risk_level": ensemble.risk_level,
        "model_prediction": "PNEUMONIA" if ensemble.pneumonia_detected else "NORMAL",
        "ensemble_result": ensemble.to_dict(),
    }


def _fill_legacy_columns(analysis: Analysis, model_results: list[ModelPrediction]) -> None:
    by_key = {item.key: item for item in model_results if item.available}
    cnn = by_key.get("cnn")
    tensorflow = by_key.get("tensorflow")
    if cnn:
        analysis.cnn_probability = cnn.probability
        analysis.cnn_confidence = cnn.confidence
        analysis.cnn_detected = cnn.pneumonia_detected
    if tensorflow:
        analysis.covxnet_probability = tensorflow.probability
        analysis.covxnet_confidence = tensorflow.confidence
        analysis.covxnet_detected = tensorflow.pneumonia_detected


def _legacy_model_results(analysis: Analysis) -> list[dict]:
    results = []
    if analysis.cnn_probability is not None:
        results.append(
            {
                "key": "cnn",
                "name": "CNN Model",
                "available": True,
                "pneumonia_detected": bool(analysis.cnn_detected),
                "probability": round(float(analysis.cnn_probability), 4),
                "confidence": round(float(analysis.cnn_confidence or 0), 2),
                "risk_level": _risk_level(float(analysis.cnn_probability)),
            }
        )
    if analysis.covxnet_probability is not None:
        results.append(
            {
                "key": "tensorflow",
                "name": "TensorFlow Pneumonia Model",
                "available": True,
                "pneumonia_detected": bool(analysis.covxnet_detected),
                "probability": round(float(analysis.covxnet_probability), 4),
                "confidence": round(float(analysis.covxnet_confidence or 0), 2),
                "risk_level": _risk_level(float(analysis.covxnet_probability)),
            }
        )
    return results


def _risk_level(probability: float) -> str:
    if probability < 0.5:
        return "NORMAL"
    if probability < 0.75:
        return "RISK"
    return "CRITICAL"


def _guest_user_id(db: Session) -> int:
    guest = db.scalar(select(User).where(User.email == "guest@local.invalid"))
    if guest is None:
        guest = User(full_name="Guest User", email="guest@local.invalid", hashed_password="disabled")
        db.add(guest)
        db.flush()
    return guest.id
