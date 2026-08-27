"""Camera node entry point.

Webcam -> Frame Sampling -> Vehicle Detection -> Plate Detection ->
Plate Crop -> Preprocessing -> OCR -> Deduplication -> POST detection
event to Django.

Run with: python main.py   (after configuring .env, see .env.example)
"""

import logging
import sys
from datetime import datetime, timezone

from api_client import DetectionAPIClient
from camera import WebcamSource
from config import CameraConfig
from deduplication import PlateDeduplicator
from detector import YoloVehicleDetector
from ocr import EasyOCRModel
from plate_detector import LocalPlateDetector
from plate_format import correct_plate
from preprocessing import preprocess_plate
from tracker import CentroidTracker

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s"
)


def run() -> None:
    cfg = CameraConfig
    # Logger name includes the camera identity so output from several
    # nodes running in parallel (Step 3) stays distinguishable, whether
    # interleaved in one console or collected into one log file.
    logger = logging.getLogger(f"camera_node.{cfg.CAMERA_ID}")

    webcam = WebcamSource(cfg.CAMERA_INDEX, cfg.FRAME_SAMPLE_INTERVAL_SECONDS)
    vehicle_detector = YoloVehicleDetector(
        model_path=cfg.VEHICLE_MODEL_PATH, confidence_threshold=cfg.VEHICLE_CONFIDENCE_THRESHOLD
    )
    plate_detector = LocalPlateDetector()
    ocr_model = EasyOCRModel()
    tracker = CentroidTracker(max_age=cfg.TRACK_MAX_AGE_SECONDS)
    dedup = PlateDeduplicator(window_seconds=cfg.DEDUP_WINDOW_SECONDS)
    api_client = DetectionAPIClient(cfg.SERVER_URL, cfg.CAMERA_ID, cfg.API_KEY)

    logger.info("Starting camera node %s (server=%s)", cfg.CAMERA_ID, cfg.SERVER_URL)
    webcam.open()

    try:
        for frame in webcam.frames():
            vehicle_boxes = vehicle_detector.detect(frame)
            tracked = tracker.update(vehicle_boxes)

            for track_id, vehicle_box in tracked:
                if not tracker.needs_ocr(track_id):
                    continue

                plate_box = plate_detector.detect(frame, vehicle_box)
                if plate_box is None:
                    continue

                plate_crop = frame[
                    plate_box.y : plate_box.y + plate_box.height,
                    plate_box.x : plate_box.x + plate_box.width,
                ]
                if plate_crop.size == 0:
                    continue

                preprocessed = preprocess_plate(plate_crop)
                raw_plate_number, confidence = ocr_model.read_plate(preprocessed)
                plate_number = correct_plate(raw_plate_number)
                tracker.mark_ocr_done(track_id)

                if not plate_number:
                    continue

                logger.info(
                    "Track %s -> plate=%s (raw=%s) confidence=%.2f",
                    track_id,
                    plate_number,
                    raw_plate_number,
                    confidence,
                )

                if not dedup.should_send(plate_number):
                    logger.debug("Suppressing duplicate detection for %s", plate_number)
                    continue

                timestamp = datetime.now(timezone.utc).isoformat()
                result = api_client.send_detection(
                    plate_number=plate_number,
                    ocr_confidence=confidence,
                    timestamp=timestamp,
                    latitude=cfg.LATITUDE,
                    longitude=cfg.LONGITUDE,
                    direction=cfg.DIRECTION,
                    plate_image=plate_crop if cfg.SEND_PLATE_IMAGE else None,
                )
                if result and result.get("success"):
                    alert_tag = " -- ALERT GENERATED" if result.get("alert_generated") else ""
                    logger.info(
                        "Sent detection id=%s vehicle_id=%s%s",
                        result["detection_id"],
                        result["vehicle_id"],
                        alert_tag,
                    )
    except KeyboardInterrupt:
        logger.info("Shutting down camera node (Ctrl+C)")
    finally:
        webcam.close()


if __name__ == "__main__":
    sys.exit(run())
