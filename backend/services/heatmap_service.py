import logging
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from core.config import get_settings
from services.file_service import public_url
from services.model_loader import LoadedModel, tf
from services.preprocess_service import preprocess_for_model


settings = get_settings()
logger = logging.getLogger("ai-lung-scan.heatmap")


def create_heatmap(rgb_image: np.ndarray, selected_model: LoadedModel | None) -> tuple[Path, str]:
    heatmap = None
    if selected_model and selected_model.available and selected_model.model is not None and tf is not None:
        try:
            heatmap = _grad_cam_heatmap(rgb_image, selected_model)
        except Exception as exc:
            logger.warning("Grad-CAM failed for %s; using fallback overlay: %s", selected_model.key, exc)

    if heatmap is None:
        heatmap = _opencv_attention_heatmap(rgb_image)

    overlay = _overlay_heatmap(rgb_image, heatmap)
    bgr_overlay = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    target_dir = settings.uploads_dir / "heatmaps"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"xray_{uuid4().hex}_heatmap.png"
    cv2.imwrite(str(target_path), bgr_overlay)
    return target_path, public_url(target_path)


def find_last_conv_layer_name(model) -> str:
    for layer in reversed(model.layers):
        output_shape = getattr(layer, "output_shape", None) or getattr(getattr(layer, "output", None), "shape", None)
        if output_shape is not None and len(output_shape) == 4:
            return layer.name
    raise ValueError("Grad-CAM uchun konvolyutsion qatlam topilmadi")


def _grad_cam_heatmap(rgb_image: np.ndarray, selected_model: LoadedModel) -> np.ndarray:
    model = selected_model.model
    layer_name = find_last_conv_layer_name(model)
    batch = preprocess_for_model(rgb_image, selected_model)
    model_output = model.outputs[0] if getattr(model, "outputs", None) else model.output
    grad_model = tf.keras.models.Model(model.inputs, [model.get_layer(layer_name).output, model_output])

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(batch)
        if len(predictions.shape) > 1 and predictions.shape[-1] > 1:
            loss = predictions[:, 1]
        else:
            loss = predictions[:, 0]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def _opencv_attention_heatmap(rgb_image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, (settings.image_size, settings.image_size))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(resized)
    blur = cv2.GaussianBlur(clahe, (15, 15), 0)
    edges = cv2.Canny(clahe, 35, 120)
    attention = cv2.addWeighted(cv2.absdiff(clahe, blur), 0.7, edges, 0.3, 0)
    attention = cv2.GaussianBlur(attention, (21, 21), 0)
    heat = cv2.normalize(attention, None, 0, 1, cv2.NORM_MINMAX)
    return heat.astype("float32")


def _overlay_heatmap(rgb_image: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
    heatmap = cv2.resize(heatmap, (rgb_image.shape[1], rgb_image.shape[0]))
    heatmap_uint8 = np.uint8(255 * np.clip(heatmap, 0, 1))
    colored_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)
    return cv2.addWeighted(rgb_image, 0.62, colored_rgb, 0.38, 0)
