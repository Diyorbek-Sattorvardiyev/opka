# AI Lung Scan Backend

FastAPI backend for chest X-ray pneumonia assistant analysis. It supports up to three Keras `.h5` models, dynamic ensemble prediction, Grad-CAM heatmaps with a fallback overlay, Gemini summaries, upload validation, SQLite/PostgreSQL, SQLAlchemy, CORS, and JSON API errors.

Medical warning: this system is not a diagnostic device. Every response includes: `Bu natija AI yordamchi tahlilidir, yakuniy tibbiy tashxis emas. Yakuniy tashxis uchun shifokorga murojaat qiling.`

## Setup


```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd ..
./run.sh
```

API docs: `http://localhost:8000/docs`

## Model Files

Put available real models in:

```text
backend/trained_model/cnn_pneumonia_model.h5
backend/trained_model/tensorflow_pneumonia_model.h5
backend/trained_model/mobilenet_pneumonia_model.h5
```

Missing models are skipped. If MobileNet is missing, the API still works with the available models and returns `unavailable_models: ["mobilenet"]`. Demo predictions are disabled; if no real model is found, `/api/analysis/predict` returns a clear `503` JSON error.

## Main Endpoint

`POST /api/analysis/predict`

Request: `multipart/form-data` with `file`.

Success response:

```json
{
  "success": true,
  "message": "Tahlil yakunlandi",
  "data": {
    "final_result": {
      "pneumonia_detected": true,
      "confidence": 82.4,
      "probability": 0.824,
      "risk_level": "CRITICAL",
      "method": "two_model_average"
    },
    "models": [],
    "available_models_count": 2,
    "unavailable_models": ["mobilenet"],
    "original_image_url": "/uploads/originals/example.png",
    "heatmap_image_url": "/uploads/heatmaps/example_heatmap.png",
    "ai_summary": "...",
    "medical_disclaimer": "Bu natija AI yordamchi tahlilidir, yakuniy tibbiy tashxis emas. Yakuniy tashxis uchun shifokorga murojaat qiling.",
    "created_at": "2026-05-02T12:30:00+00:00"
  }
}
```

## Environment

```env
ALLOW_DEMO_MODEL=false
CNN_MODEL_PATH=backend/trained_model/cnn_pneumonia_model.h5
TENSORFLOW_MODEL_PATH=backend/trained_model/tensorflow_pneumonia_model.h5
MOBILENET_MODEL_PATH=backend/trained_model/mobilenet_pneumonia_model.h5
GEMINI_API_KEY=your_key
FRONTEND_ORIGIN=http://localhost:5500
```

## Frontend

See `../frontend/ensemble-api-example.js` and `frontend_examples/api-client.js` for FormData upload, loading state, image previews, per-model cards, unavailable model status, AI summary, and disclaimer rendering.
