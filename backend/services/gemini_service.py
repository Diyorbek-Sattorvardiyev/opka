import logging

from core.config import get_settings
from schemas.analysis_schema import DISCLAIMER
from services.ensemble_service import EnsemblePrediction
from services.prediction_service import ModelPrediction


settings = get_settings()
logger = logging.getLogger("ai-lung-scan.gemini")

FALLBACK_SUMMARY = (
    "AI modellari rentgen tasvirini tahlil qildi. Natija yordamchi tahlil sifatida ko'rsatiladi. "
    "Yakuniy tashxis uchun shifokorga murojaat qiling."
)


def generate_ai_summary(
    model_results: list[ModelPrediction],
    ensemble_result: EnsemblePrediction,
    unavailable_models: list[str],
) -> str:
    if not settings.gemini_api_key:
        return FALLBACK_SUMMARY

    try:
        return _generate_with_gemini(model_results, ensemble_result, unavailable_models)
    except Exception:
        logger.exception("Gemini summary generation failed")
        return FALLBACK_SUMMARY


def _generate_with_gemini(
    model_results: list[ModelPrediction],
    ensemble_result: EnsemblePrediction,
    unavailable_models: list[str],
) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = f"""
Sen o'zbek tilida yozadigan tibbiy AI yordamchi tizimisan. Quyidagi AI model natijalariga tayangan holda 4-6 jumladan iborat qisqa, ehtiyotkor xulosa yoz.

Muhim qoidalar:
- Hech qachon aniq tashxis qo'yma.
- Natijani faqat AI yordamchi tahlili sifatida ifodala.
- Yakuniy tashxis va davolash uchun shifokorga murojaat qilish kerakligini ayt.
- Heatmapdagi qizil/sariq hududlar model e'tibor bergan zonalar ekanini, kasallik joylashuvi sifatida qabul qilinmasligini tushuntir.
- Agar model unavailable bo'lsa, ayniqsa MobileNet hali ulanmagan bo'lishi mumkinligini yumshoq ayt.

Mavjud model natijalari soni: {sum(1 for item in model_results if item.available)}
Unavailable models: {unavailable_models}
Model natijalari: {[item.to_dict() for item in model_results]}
Yakuniy ensemble: {ensemble_result.to_dict()}
Majburiy disclaimer: {DISCLAIMER}
"""
    response = model.generate_content(prompt)
    text = getattr(response, "text", "").strip()
    return _ensure_disclaimer(text or FALLBACK_SUMMARY)


def _ensure_disclaimer(text: str) -> str:
    if DISCLAIMER not in text:
        return f"{text} {DISCLAIMER}"
    return text
