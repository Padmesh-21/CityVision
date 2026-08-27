"""Plate crop preprocessing, applied before OCR regardless of which OCR
engine is behind ocr.OCRModel.

Plate Crop -> Resize -> Grayscale -> Noise Reduction -> Contrast
Enhancement -> Adaptive Thresholding -> Deskew
"""

import cv2
import numpy as np


def preprocess_plate(plate_crop: np.ndarray, target_width: int = 300) -> np.ndarray:
    if plate_crop.size == 0:
        return plate_crop

    h, w = plate_crop.shape[:2]
    scale = target_width / max(w, 1)
    resized = cv2.resize(
        plate_crop, (target_width, max(int(h * scale), 1)), interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if resized.ndim == 3 else resized
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)

    thresholded = cv2.adaptiveThreshold(
        contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )

    return _deskew(thresholded)


def _deskew(binary_img: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(binary_img < 255))
    if coords.shape[0] < 10:
        return binary_img

    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.5:
        return binary_img

    h, w = binary_img.shape[:2]
    rotation_matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        binary_img, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
