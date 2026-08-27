"""Webcam capture with frame sampling.

We deliberately do not process every frame at full FPS -- a vehicle
passage takes at least a second or two, so sampling every
`sample_interval_seconds` is enough to catch it while keeping CPU usage
low on a laptop.
"""

import logging
import time

import cv2

logger = logging.getLogger(__name__)


class WebcamSource:
    def __init__(self, camera_index: int = 0, sample_interval_seconds: float = 0.5):
        self._camera_index = camera_index
        self._sample_interval = sample_interval_seconds
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        # CAP_DSHOW avoids the multi-second startup delay MSMF sometimes
        # has on Windows.
        self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open webcam at index {self._camera_index}")
        logger.info("Webcam %s opened", self._camera_index)

    def frames(self):
        """Yields sampled BGR frames until the caller stops iterating."""
        last_yield = 0.0
        while True:
            ok, frame = self._cap.read()
            if not ok:
                logger.warning("Failed to read frame from webcam; retrying")
                time.sleep(0.5)
                continue

            now = time.time()
            if now - last_yield < self._sample_interval:
                continue
            last_yield = now
            yield frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            logger.info("Webcam released")
