#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/backend"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ".env yaratildi. Kerak bo'lsa GEMINI_API_KEY ni backend/.env ichiga qo'ying."
fi

echo "AI Lung Scan ishga tushmoqda..."
echo "Sayt: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
