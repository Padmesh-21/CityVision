"""Vehicle detection interface.

`VehicleDetector` is the contract the rest of the pipeline depends on.
`YoloVehicleDetector` uses a COCO-pretrained YOLOv8 model, filtered to
vehicle classes -- no training required, since "is this a
car/bus/truck/motorcycle" transfers well from COCO's general object set.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

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
