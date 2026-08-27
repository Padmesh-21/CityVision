"""Vehicle detection interface.

`VehicleDetector` is the contract the rest of the pipeline depends on.
`YoloVehicleDetector` (Step 4) uses a COCO-pretrained YOLOv8 model,
filtered to vehicle classes -- no training required, since "is this a
car/bus/truck/motorcycle" transfers well from COCO's general object set.
`MotionVehicleDetector` (Step 2) remains as a zero-dependency fallback
for environments without ultralytics/torch installed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import cv2
import numpy as np

# COCO class ids for vehicle categories YOLOv8 is pretrained on.
_COCO_VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    confidence: float


class VehicleDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray) -> list[BoundingBox]:
        """Return one bounding box per vehicle found in `frame`."""


class MotionVehicleDetector(VehicleDetector):
    """Flags any sufficiently large moving foreground blob as a 'vehicle'.

    This has no idea what a vehicle looks like -- it only reacts to
    motion -- but it is enough to exercise the whole node end-to-end
    (including against a real Django server) without a trained model.
    """

    def __init__(self, min_area: int = 6000, history: int = 300, var_threshold: int = 32):
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=var_threshold, detectShadows=False
        )
        self._min_area = min_area

    def detect(self, frame: np.ndarray) -> list[BoundingBox]:
        fg_mask = self._bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        frame_area = frame.shape[0] * frame.shape[1]
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self._min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            confidence = min(1.0, area / frame_area * 4)
            boxes.append(BoundingBox(x, y, w, h, confidence))
        return boxes


class YoloVehicleDetector(VehicleDetector):
    """Real vehicle detection using a COCO-pretrained YOLOv8 model.

    Only car/motorcycle/bus/truck detections are kept. This is a
    pretrained model used as-is -- no fine-tuning needed, since
    recognizing "this is a vehicle" is a general-object-detection skill
    that transfers directly from COCO.
    """

    def __init__(self, model_path: str = "models/yolov8n.pt", confidence_threshold: float = 0.4):
        from ultralytics import YOLO  # imported lazily: heavy (torch) and optional

        self._model = YOLO(model_path)
        self._confidence_threshold = confidence_threshold

    def detect(self, frame: np.ndarray) -> list[BoundingBox]:
        results = self._model.predict(
            frame,
            classes=list(_COCO_VEHICLE_CLASSES.keys()),
            conf=self._confidence_threshold,
            verbose=False,
        )[0]

        boxes = []
        for xyxy, conf in zip(results.boxes.xyxy.tolist(), results.boxes.conf.tolist()):
            x1, y1, x2, y2 = (int(v) for v in xyxy)
            boxes.append(BoundingBox(x1, y1, x2 - x1, y2 - y1, float(conf)))
        return boxes
