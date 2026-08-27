"""Suppresses re-sending the same plate number to the server too often.

Distinct from tracker.py's job: the tracker avoids re-running OCR on a
vehicle that's still sitting in the frame; this avoids spamming the
Django API if OCR briefly loses and re-acquires the same plate (e.g. a
new track_id gets assigned after a short occlusion), or if the same
vehicle idles in view across many tracker expirations.
"""

import time


class PlateDeduplicator:
    def __init__(self, window_seconds: int = 10):
        self._window_seconds = window_seconds
        self._last_sent: dict[str, float] = {}

    def should_send(self, plate_number: str) -> bool:
        now = time.time()
        last_sent = self._last_sent.get(plate_number)
        if last_sent is not None and (now - last_sent) < self._window_seconds:
            return False
        self._last_sent[plate_number] = now
        return True
