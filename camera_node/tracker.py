"""Minimal frame-to-frame object tracking.

A vehicle sitting in view gets detected on every sampled frame. Without
tracking we'd re-run OCR on it every single frame. CentroidTracker
assigns a stable track_id to each detection by nearest-centroid matching
against recent tracks, so the pipeline can run OCR once per track instead
of once per frame.

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
    ocr_done: bool = False


class CentroidTracker:
    def __init__(self, max_distance: float = 80, max_age: float = 2.0):
        self._tracks: dict[int, Track] = {}
        self._next_id = 1
        self._max_distance = max_distance
        self._max_age = max_age

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
        return track is not None and not track.ocr_done

    def mark_ocr_done(self, track_id: int) -> None:
        if track_id in self._tracks:
            self._tracks[track_id].ocr_done = True

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
