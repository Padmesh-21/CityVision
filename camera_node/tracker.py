"""Minimal frame-to-frame object tracking.

A vehicle sitting in view gets detected on every sampled frame. Without
tracking we'd re-run OCR on it every single frame. CentroidTracker
assigns a stable track_id to each detection by nearest-centroid matching
against recent tracks, so the pipeline can run OCR a bounded number of
times per track (keeping the best reading) instead of once per frame.

This is a tracking concern, distinct from deduplication.py, which
decides whether an *already OCR'd* plate should be re-sent to the server.
"""

import time
from dataclasses import dataclass, field

from detector import BoundingBox


@dataclass
class Track:
    track_id: int
    centroid: tuple[int, int]
    last_seen: float = field(default_factory=time.time)
    ocr_attempts: int = 0
    best_plate: str = ""
    best_confidence: float = 0.0
    best_is_valid_format: bool = False


class CentroidTracker:
    def __init__(self, max_distance: float = 80, max_age: float = 2.0, max_ocr_attempts: int = 3):
        self._tracks: dict[int, Track] = {}
        self._next_id = 1
        self._max_distance = max_distance
        self._max_age = max_age
        # A vehicle sits in view for several sampled frames, and OCR
        # quality varies frame to frame (motion blur, glare, angle) --
        # taking the single first attempt means one bad frame permanently
        # ruins the reading. Trying a few frames and keeping the best one
        # meaningfully improves accuracy at zero extra dependency/model
        # cost.
        self._max_ocr_attempts = max_ocr_attempts

    def update(self, boxes: list[BoundingBox]) -> list[tuple[int, BoundingBox]]:
        now = time.time()
        self._expire(now)

        assigned = []
        for box in boxes:
            centroid = (box.x + box.width // 2, box.y + box.height // 2)
            track_id = self._match(centroid)
            if track_id is None:
                track_id = self._next_id
                self._next_id += 1
                self._tracks[track_id] = Track(track_id, centroid)
            else:
                self._tracks[track_id].centroid = centroid
                self._tracks[track_id].last_seen = now
            assigned.append((track_id, box))
        return assigned

    def needs_ocr(self, track_id: int) -> bool:
        track = self._tracks.get(track_id)
        return track is not None and track.ocr_attempts < self._max_ocr_attempts

    def record_ocr_attempt(
        self, track_id: int, plate_number: str, confidence: float, is_valid_format: bool
    ) -> tuple[bool, str, float]:
        """Records one OCR attempt for this track, keeping whichever
        reading is best so far -- a format-valid reading always beats an
        invalid one (regardless of confidence), since matching the known
        Indian plate layout is a stronger signal than OCR's own confidence
        score; ties broken by confidence.

        Returns (is_final_attempt, best_plate_so_far, best_confidence_so_far).
        """
        track = self._tracks.get(track_id)
        if track is None:
            return True, plate_number, confidence

        track.ocr_attempts += 1
        is_better = (is_valid_format, confidence) > (track.best_is_valid_format, track.best_confidence)
        if is_better:
            track.best_plate = plate_number
            track.best_confidence = confidence
            track.best_is_valid_format = is_valid_format

        is_final = track.ocr_attempts >= self._max_ocr_attempts
        return is_final, track.best_plate, track.best_confidence

    def _match(self, centroid: tuple[int, int]) -> int | None:
        best_id, best_dist = None, self._max_distance
        for track_id, track in self._tracks.items():
            dist = ((track.centroid[0] - centroid[0]) ** 2 + (track.centroid[1] - centroid[1]) ** 2) ** 0.5
            if dist < best_dist:
                best_id, best_dist = track_id, dist
        return best_id

    def _expire(self, now: float) -> None:
        expired = [tid for tid, track in self._tracks.items() if now - track.last_seen > self._max_age]
        for track_id in expired:
            del self._tracks[track_id]
