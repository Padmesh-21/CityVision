"""License plate localization interface.

`PlateDetector` is the contract. `YoloPlateDetector` uses a YOLOv8 model
fine-tuned specifically on license plate images (unlike
`YoloVehicleDetector`'s COCO weights, which have no "license plate"
class at all -- COCO simply never labeled plates, so no COCO-pretrained
model can find one no matter how it's called). See camera_node/README.md
for where this weight file comes from and how to (re-)download it.
"""

from abc import ABC, abstractmethod

import numpy as np

from detector import BoundingBox


class PlateDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray, vehicle_box: BoundingBox) -> BoundingBox | None:
        """Return the plate's bounding box within `vehicle_box`, or None
        if no plate-like region could be located."""


class YoloPlateDetector(PlateDetector):
    """Runs only within the vehicle's box (not the whole frame): smaller
    search area, less scene clutter to confuse it."""

    def __init__(
        self,
        model_path: str = "models/license_plate_yolov8n.pt",
        confidence_threshold: float = 0.4,
    ):
        from ultralytics import YOLO  # imported lazily: heavy (torch) and optional

        self._model = YOLO(model_path)
        self._confidence_threshold = confidence_threshold

    def detect(self, frame: np.ndarray, vehicle_box: BoundingBox) -> BoundingBox | None:
        x, y, w, h = vehicle_box.x, vehicle_box.y, vehicle_box.width, vehicle_box.height
        if w <= 0 or h <= 0:
            return None

        roi = frame[y : y + h, x : x + w]
        if roi.size == 0:
            return None

        results = self._model.predict(roi, conf=self._confidence_threshold, verbose=False)[0]
        if len(results.boxes) == 0:
            return None

        # A vehicle should only have one plate in view -- if more than one
        # box came back (e.g. a reflection, or a second vehicle poking
        # into the ROI), keep only the most confident one.
        best_idx = int(results.boxes.conf.argmax())
        x1, y1, x2, y2 = (int(v) for v in results.boxes.xyxy[best_idx].tolist())
        confidence = float(results.boxes.conf[best_idx])
        # Box coordinates are relative to `roi` -- offset back to the
        # full frame's coordinate space, the convention everything
        # downstream (the crop in main.py) expects.
        return BoundingBox(x + x1, y + y1, x2 - x1, y2 - y1, confidence)
