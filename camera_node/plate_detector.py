"""License plate localization interface.

`PlateDetector` is the contract. `LocalPlateDetector` implements the
classic blackhat + Sobel-gradient + morphological-close technique: it
isolates small, high-contrast rectangular regions with dense vertical
edges within the vehicle box -- exactly what a plate's text produces
against its background -- and scores candidates by aspect ratio, size
and vertical position. No trained model or dataset required, and it
generalizes across plate styles/countries reasonably well since it
depends on geometry and contrast, not font. A `YoloPlateDetector` can be
added behind the same interface later if a labeled Indian-plate dataset
becomes available and this proves insufficient.
"""

from abc import ABC, abstractmethod

import cv2
import numpy as np

from detector import BoundingBox

# Detection targets the dense text row itself (not the full plastic
# plate border), which is visually tighter/wider than the plate as a
# whole -- so the aspect-ratio band is wider than a raw plate's ~2:1
# (two-line) to ~5:1 (single-line) shape.
_MIN_ASPECT_RATIO = 1.5
_MAX_ASPECT_RATIO = 10.0
_MIN_AREA_RATIO = 0.01
_MAX_AREA_RATIO = 0.35

# Padding applied to the detected text-row box so the returned crop
# includes the plate's border/background, not just the glyphs -- OCR
# engines generally do better with a little breathing room.
_WIDTH_PADDING_RATIO = 0.15
_HEIGHT_PADDING_RATIO = 0.6


class PlateDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray, vehicle_box: BoundingBox) -> BoundingBox | None:
        """Return the plate's bounding box within `vehicle_box`, or None
        if no plate-like region could be located."""


class LocalPlateDetector(PlateDetector):
    def __init__(self, rect_kernel_size=(45, 9)):
        self._rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, rect_kernel_size)

    def detect(self, frame: np.ndarray, vehicle_box: BoundingBox) -> BoundingBox | None:
        x, y, w, h = vehicle_box.x, vehicle_box.y, vehicle_box.width, vehicle_box.height
        if w <= 0 or h <= 0:
            return None

        roi = frame[y : y + h, x : x + w]
        if roi.size == 0:
            return None

        candidate = self._find_plate_like_region(roi)
        if candidate is not None:
            cx, cy, cw, ch = self._pad(*candidate, roi_w=w, roi_h=h)
            return BoundingBox(x + cx, y + cy, cw, ch, vehicle_box.confidence)

        return self._fallback_lower_center(x, y, w, h, vehicle_box.confidence)

    def _find_plate_like_region(self, roi: np.ndarray) -> tuple[int, int, int, int] | None:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi

        # Blackhat highlights small dark regions (plate text) against a
        # lighter background.
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, self._rect_kernel)

        grad_x = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        grad_x = np.absolute(grad_x)
        min_val, max_val = grad_x.min(), grad_x.max()
        grad_x = 255 * (grad_x - min_val) / (max_val - min_val + 1e-6)
        grad_x = grad_x.astype(np.uint8)

        grad_x = cv2.GaussianBlur(grad_x, (5, 5), 0)
        # Closing with a wide horizontal kernel bridges the gaps between
        # individual characters/letter-groups so the whole plate string
        # becomes one connected blob rather than one contour per glyph.
        grad_x = cv2.morphologyEx(grad_x, cv2.MORPH_CLOSE, self._rect_kernel)
        thresh = cv2.threshold(grad_x, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        thresh = cv2.erode(thresh, None, iterations=1)
        thresh = cv2.dilate(thresh, None, iterations=1)

        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        roi_h, roi_w = gray.shape[:2]
        roi_area = roi_w * roi_h

        best_box = None
        best_score = -1.0
        for contour in contours:
            cx, cy, cw, ch = cv2.boundingRect(contour)
            if ch == 0:
                continue
            aspect_ratio = cw / float(ch)
            area_ratio = (cw * ch) / float(roi_area)
            if not (_MIN_ASPECT_RATIO <= aspect_ratio <= _MAX_ASPECT_RATIO):
                continue
            if not (_MIN_AREA_RATIO <= area_ratio <= _MAX_AREA_RATIO):
                continue

            # Plates sit in the lower portion of a frontal/rear vehicle crop.
            vertical_position_score = cy / float(roi_h)
            score = area_ratio * 2 + vertical_position_score
            if score > best_score:
                best_score = score
                best_box = (cx, cy, cw, ch)

        return best_box

    @staticmethod
    def _pad(cx: int, cy: int, cw: int, ch: int, roi_w: int, roi_h: int) -> tuple[int, int, int, int]:
        """Expands the detected text-row box to include some of the
        plate's border/background, clamped to the vehicle ROI."""
        pad_w = int(cw * _WIDTH_PADDING_RATIO)
        pad_h = int(ch * _HEIGHT_PADDING_RATIO)
        px = max(cx - pad_w, 0)
        py = max(cy - pad_h, 0)
        pw = min(cw + 2 * pad_w, roi_w - px)
        ph = min(ch + 2 * pad_h, roi_h - py)
        return px, py, pw, ph

    @staticmethod
    def _fallback_lower_center(x: int, y: int, w: int, h: int, confidence: float) -> BoundingBox:
        """No confident plate-shaped contour found -- common when the
        upstream 'vehicle' box came from a motion detector rather than a
        real vehicle. Falls back to a lower-center crop so the pipeline
        still has something to preprocess/OCR."""
        plate_w = max(int(w * 0.5), 1)
        plate_h = max(int(h * 0.18), 1)
        plate_x = x + (w - plate_w) // 2
        plate_y = y + int(h * 0.7)
        return BoundingBox(plate_x, plate_y, plate_w, plate_h, confidence * 0.5)
