"""HTTP client for POST /api/detections/ on the Django backend.

Authenticates with the per-camera API key (X-API-Key header) issued when
the camera was created via POST /api/cameras/ in Step 1 -- see
cameras.authentication.CameraAPIKeyAuthentication on the server side.
"""

import logging

import cv2
import numpy as np
import requests

logger = logging.getLogger(__name__)


class DetectionAPIClient:
    def __init__(self, server_url: str, camera_id: str, api_key: str, timeout: float = 5.0):
        self._detections_url = server_url.rstrip("/") + "/api/detections/"
        self._camera_id = camera_id
        self._headers = {"X-API-Key": api_key}
        self._timeout = timeout

    def send_detection(
        self,
        plate_number: str,
        ocr_confidence: float,
        timestamp: str,
        latitude: float,
        longitude: float,
        direction: str = "",
        vehicle_type: str | None = None,
        plate_image: np.ndarray | None = None,
    ) -> dict | None:
        data = {
            "camera_id": self._camera_id,
            "plate_number": plate_number,
            "ocr_confidence": ocr_confidence,
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "direction": direction,
        }
        if vehicle_type:
            data["vehicle_type"] = vehicle_type

        files = None
        if plate_image is not None and plate_image.size > 0:
            ok, buffer = cv2.imencode(".jpg", plate_image)
            if ok:
                files = {"plate_image": ("plate.jpg", buffer.tobytes(), "image/jpeg")}

        try:
            response = requests.post(
                self._detections_url, data=data, files=files, headers=self._headers, timeout=self._timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error("Failed to send detection to %s: %s", self._detections_url, exc)
            return None
