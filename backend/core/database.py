from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from models.analysis import Analysis  # noqa: F401
    from models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_analysis_columns()


def _ensure_analysis_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "analyses" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("analyses")}
    columns = {
        "final_probability": "FLOAT",
        "final_confidence": "FLOAT",
        "final_detected": "BOOLEAN",
        "ensemble_method": "VARCHAR(80)",
        "available_models_count": "INTEGER",
        "unavailable_models": "JSON",
        "model_results": "JSON",
        "covxnet_probability": "FLOAT",
        "covxnet_confidence": "FLOAT",
        "covxnet_detected": "BOOLEAN",
        "cnn_probability": "FLOAT",
        "cnn_confidence": "FLOAT",
        "cnn_detected": "BOOLEAN",
        "ensemble_probability": "FLOAT",
        "ensemble_confidence": "FLOAT",
        "ensemble_detected": "BOOLEAN",
        "selected_model_for_heatmap": "VARCHAR(120)",
    }

    with engine.begin() as connection:
        for name, column_type in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE analyses ADD COLUMN {name} {column_type}"))
