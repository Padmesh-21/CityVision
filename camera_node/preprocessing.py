"""Plate crop preprocessing, applied before OCR regardless of which OCR
engine is behind ocr.OCRModel.

Plate Crop -> Resize -> Grayscale -> Contrast Enhancement (CLAHE)

This used to also hard-threshold the image to pure black/white and
deskew the result, on the assumption that a clean binary "OCR-ready"
image would help. Empirically (tested against a real Indian plate photo
with known ground truth, comparing exact preprocessing variants through
the real EasyOCR model -- see camera_node/README.md) that assumption was
wrong for this OCR engine: hard binarization consistently made readings
*worse*, sometimes catastrophically (a correct-looking crop reading as a
single stray character). EasyOCR's underlying model was trained on
natural scene text and already does its own robust internal
preprocessing -- handing it a clean, well-resized, contrast-enhanced
*grayscale* image outperformed handing it a hand-thresholded binary mask
in every configuration tested. Deskewing was implemented on top of that
binary mask and removed along with it, since it has nothing to measure
an angle from without one.
"""

import cv2
import numpy as np


def preprocess_plate(plate_crop: np.ndarray, target_width: int = 600) -> np.ndarray:
    if plate_crop.size == 0:
        return plate_crop

    h, w = plate_crop.shape[:2]
    scale = target_width / max(w, 1)
    resized = cv2.resize(
        plate_crop, (target_width, max(int(h * scale), 1)), interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if resized.ndim == 3 else resized

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)
