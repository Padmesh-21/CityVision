"""OCR interface.

`OCRModel` is the contract. `EasyOCRModel` wraps EasyOCR, a pretrained
general scene-text recognizer -- it was not fine-tuned on license plates
specifically, and Indian plates in particular have two known failure
modes it wasn't trained for: two-line motorcycle plates and
stylized/non-standard fonts. See camera_node/README.md for measured
real-world accuracy (evaluate.py) and what's been done to work around
these failure modes without retraining the model.
"""

import re
from abc import ABC, abstractmethod

import numpy as np


class OCRModel(ABC):
    @abstractmethod
    def read_plate(self, preprocessed_plate: np.ndarray) -> tuple[str, float]:
        """Returns (plate_text, confidence in [0, 1])."""


_ALLOWED_PLATE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class EasyOCRModel(OCRModel):
    def __init__(self, languages: list[str] | None = None, gpu: bool = False):
        import easyocr  # imported lazily: heavy (torch) and optional

        self._reader = easyocr.Reader(languages or ["en"], gpu=gpu, verbose=False)

    def read_plate(self, preprocessed_plate: np.ndarray) -> tuple[str, float]:
        if preprocessed_plate.size == 0:
            return "", 0.0

        results = self._reader.readtext(
            preprocessed_plate, detail=1, allowlist=_ALLOWED_PLATE_CHARS
        )
        if not results:
            return "", 0.0

        # A plate can come back as more than one text region (e.g. the
        # state/district code separate from the number) -- order them
        # left-to-right by their box's leftmost x-coordinate and
        # concatenate, weighting overall confidence by fragment length.
        results.sort(key=lambda r: r[0][0][0])
        text = re.sub(r"[^A-Z0-9]", "", "".join(r[1] for r in results).upper())

        total_len = sum(len(r[1]) for r in results) or 1
        confidence = sum(r[2] * len(r[1]) for r in results) / total_len
        return text, float(confidence)
