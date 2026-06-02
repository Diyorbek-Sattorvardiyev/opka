import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import get_settings


settings = get_settings()
logger = logging.getLogger("ai-lung-scan.models")

try:
    import tensorflow as tf
except Exception:  # pragma: no cover
    tf = None


@dataclass(frozen=True)
class ModelSpec:
    key: str
    name: str
    path: Path


@dataclass
class LoadedModel:
    key: str
    name: str
    path: Path
    model: Any | None = None
    available: bool = False
    message: str | None = None

    @property
    def input_size(self) -> int:
        shape = getattr(self.model, "input_shape", None)
        if isinstance(shape, list) and shape:
            shape = shape[0]
        if not shape or len(shape) < 3:
            return settings.image_size

        height = shape[1] if len(shape) == 4 else shape[0]
        width = shape[2] if len(shape) == 4 else shape[1]
        if isinstance(height, int) and isinstance(width, int) and height > 0 and width > 0:
            return int(max(height, width))
        return settings.image_size


class ModelLoader:
    def __init__(self) -> None:
        self.models: dict[str, LoadedModel] = {}

    def specs(self) -> list[ModelSpec]:
        return [
            ModelSpec("cnn", "CNN Model", settings.resolve_model_path(settings.cnn_model_path)),
            ModelSpec(
                "tensorflow",
                "TensorFlow Pneumonia Model",
                settings.resolve_model_path(settings.tensorflow_model_path),
            ),
            ModelSpec("mobilenet", "MobileNetV2 Model", settings.resolve_model_path(settings.mobilenet_model_path)),
        ]

    def load_models(self) -> None:
        self.models = {}
        for spec in self.specs():
            self.models[spec.key] = self._load_one(spec)

        available = [model.key for model in self.available_models()]
        unavailable = [model.key for model in self.unavailable_models()]
        logger.info("Available models: %s", available or "none")
        if unavailable:
            logger.info("Unavailable models: %s", unavailable)

    def all_models(self) -> list[LoadedModel]:
        if not self.models:
            self.load_models()
        return list(self.models.values())

    def available_models(self) -> list[LoadedModel]:
        return [model for model in self.all_models() if model.available and model.model is not None]

    def unavailable_models(self) -> list[LoadedModel]:
        return [model for model in self.all_models() if not model.available]

    def get(self, key: str) -> LoadedModel | None:
        if not self.models:
            self.load_models()
        return self.models.get(key)

    def _load_one(self, spec: ModelSpec) -> LoadedModel:
        if not spec.path.exists():
            return LoadedModel(
                key=spec.key,
                name=spec.name,
                path=spec.path,
                available=False,
                message="Model fayli topilmadi",
            )

        if tf is None:
            return LoadedModel(
                key=spec.key,
                name=spec.name,
                path=spec.path,
                available=False,
                message="TensorFlow o'rnatilmagan",
            )

        try:
            model = tf.keras.models.load_model(spec.path, compile=False)
        except Exception as exc:
            logger.warning("Standard load failed for %s; trying legacy H5 fallback: %s", spec.key, exc)
            try:
                model = _load_legacy_h5_model(spec.path)
            except Exception as fallback_exc:
                logger.exception("Could not load model %s from %s", spec.key, spec.path)
                return LoadedModel(
                    key=spec.key,
                    name=spec.name,
                    path=spec.path,
                    available=False,
                    message=f"Model yuklanmadi: {fallback_exc}",
                )

        return LoadedModel(key=spec.key, name=spec.name, path=spec.path, model=model, available=True)


model_loader = ModelLoader()


def _load_legacy_h5_model(path: Path):
    import h5py

    with h5py.File(path, "r") as h5_file:
        raw_config = h5_file.attrs["model_config"]
        if isinstance(raw_config, bytes):
            raw_config = raw_config.decode("utf-8")
        model_config = json.loads(raw_config)

    layers = model_config.get("config", {}).get("layers", [])
    if layers:
        first_config = layers[0].get("config", {})
        batch_input_shape = first_config.pop("batch_input_shape", None)
        if batch_input_shape and "input_shape" not in first_config:
            first_config["input_shape"] = batch_input_shape[1:]

    if model_config.get("class_name") == "Sequential":
        model = tf.keras.Sequential.from_config(model_config["config"])
    else:
        model = tf.keras.models.model_from_json(json.dumps(model_config))
    model.load_weights(path)
    return model
