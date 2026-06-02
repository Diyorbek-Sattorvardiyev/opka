import cv2
import numpy as np

from core.config import get_settings
from services.model_loader import LoadedModel


settings = get_settings()


def infer_input_size(loaded_model: LoadedModel | None) -> int:
    if loaded_model is None:
        return settings.image_size
    return loaded_model.input_size


def preprocess_for_model(rgb_image: np.ndarray, loaded_model: LoadedModel | None = None) -> np.ndarray:
    image_size = infer_input_size(loaded_model)
    resized = cv2.resize(rgb_image, (image_size, image_size))
    expected_channels = _expected_channels(loaded_model)

    if expected_channels == 1:
        resized = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        resized = np.expand_dims(resized, axis=-1)

    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=0)


def _expected_channels(loaded_model: LoadedModel | None) -> int:
    shape = getattr(getattr(loaded_model, "model", None), "input_shape", None)
    if isinstance(shape, list) and shape:
        shape = shape[0]
    if shape and len(shape) >= 4 and isinstance(shape[-1], int):
        return int(shape[-1])
    return 3
