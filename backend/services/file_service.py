from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from core.config import get_settings


settings = get_settings()


def public_url(path: Path) -> str:
    return "/" + path.relative_to(settings.uploads_dir.parent).as_posix()


async def save_upload_image(file: UploadFile) -> tuple[Path, np.ndarray]:
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPG and PNG images are accepted")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size must be 10MB or less")

    image_array = np.frombuffer(content, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")

    ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
    filename = f"xray_{uuid4().hex}{ext}"
    target_dir = settings.uploads_dir / "originals"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename

    if not cv2.imwrite(str(target_path), image):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save uploaded image")
    return target_path, image
