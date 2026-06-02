from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from core.config import get_settings
from services.file_service import public_url


settings = get_settings()


async def validate_and_save_upload(file: UploadFile) -> tuple[Path, str, np.ndarray]:
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faqat JPG, JPEG yoki PNG rasm qabul qilinadi")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yuklangan fayl bo'sh")
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Fayl hajmi 10MB dan oshmasin")

    image_array = np.frombuffer(content, dtype=np.uint8)
    bgr_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if bgr_image is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rasm fayli noto'g'ri yoki o'qilmadi")

    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    _validate_chest_xray_like(rgb_image)

    suffix = ".png" if file.content_type == "image/png" else ".jpg"
    target_dir = settings.uploads_dir / "originals"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"xray_{uuid4().hex}{suffix}"

    if not cv2.imwrite(str(target_path), bgr_image):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Original rasmni saqlab bo'lmadi")

    return target_path, public_url(target_path), rgb_image


def preprocess_for_model(rgb_image: np.ndarray, image_size: int = 224) -> np.ndarray:
    resized = cv2.resize(rgb_image, (image_size, image_size))
    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=0)


def _validate_chest_xray_like(rgb_image: np.ndarray) -> None:
    height, width = rgb_image.shape[:2]
    if height < 180 or width < 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rasm sifati past. Kamida 180x180 o'lchamdagi ko'krak qafasi rentgen tasvirini yuklang",
        )

    hsv_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
    saturation = hsv_image[:, :, 1]
    gray_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

    mean_saturation = float(np.mean(saturation))
    high_saturation_ratio = float(np.mean(saturation > 60))
    low_percentile, high_percentile = np.percentile(gray_image, [5, 95])
    contrast_range = float(high_percentile - low_percentile)

    if mean_saturation > 35 and high_saturation_ratio > 0.08:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu rasm rentgen tasviriga o'xshamaydi. Faqat ko'krak qafasi rentgen tasvirini yuklang",
        )

    if contrast_range < 35:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rentgen tasviri juda xira yoki noto'g'ri. Aniqroq ko'krak qafasi rentgen tasvirini yuklang",
        )
