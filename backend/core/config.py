from functools import lru_cache
from pathlib import Path
from secrets import token_urlsafe

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI Lung Scan API"
    api_prefix: str = "/api"
    environment: str = "development"

    database_url: str = f"sqlite:///{BASE_DIR / 'app.db'}"
    jwt_secret_key: str | None = Field(default=None, min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"
    frontend_origin: str = "http://localhost:5500"
    max_upload_size: int = 10 * 1024 * 1024
    allowed_image_types: set[str] = {"image/jpeg", "image/jpg", "image/png"}

    uploads_dir: Path = BASE_DIR / "uploads"
    cnn_model_path: Path = BASE_DIR / "trained_model" / "cnn_pneumonia_model.h5"
    tensorflow_model_path: Path = BASE_DIR / "trained_model" / "tensorflow_pneumonia_model.h5"
    mobilenet_model_path: Path = BASE_DIR / "trained_model" / "mobilenet_pneumonia_model.h5"
    image_size: int = 224
    allow_demo_model: bool = False

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.frontend_origin and self.frontend_origin not in origins:
            origins.append(self.frontend_origin)
        return origins

    def resolve_model_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        parts = path.parts
        if parts and parts[0] == "backend":
            return BASE_DIR.parent / path
        return BASE_DIR / path

    @model_validator(mode="after")
    def ensure_jwt_secret_key(self) -> "Settings":
        if self.jwt_secret_key:
            return self
        if self.environment.lower() == "production":
            raise ValueError("JWT_SECRET_KEY is required when ENVIRONMENT=production")
        self.jwt_secret_key = token_urlsafe(32)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
