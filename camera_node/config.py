"""Environment-based configuration for one camera node instance.

Nothing here is hardcoded: which physical camera to open, where the
Django server lives, and this node's identity/location all come from an
env file (see `.env.example`). Running a second node on another laptop
is just a different `.env` -- the code is identical.

On a single development machine (Step 3 testing before real laptops are
available), multiple node identities can also be run from this same
directory by pointing each process at a different env file:

    CAMERA_ENV_FILE=.env.cam002 python main.py

This has no effect on a real multi-laptop deployment, where each laptop
simply has its own plain `.env`.
"""

import os

from decouple import Config, RepositoryEnv

_env_file = os.environ.get("CAMERA_ENV_FILE", ".env")
config = Config(RepositoryEnv(_env_file))


class CameraConfig:
    # -- Identity / server --
    SERVER_URL: str = config("SERVER_URL", default="http://127.0.0.1:8000")
    CAMERA_ID: str = config("CAMERA_ID")
    API_KEY: str = config("API_KEY")

    # -- Location metadata attached to every detection this node sends.
    # Should match the Camera record created via POST /api/cameras/ on
    # the backend. --
    LATITUDE: float = config("LATITUDE", cast=float)
    LONGITUDE: float = config("LONGITUDE", cast=float)
    DIRECTION: str = config("DIRECTION", default="")

    # -- Webcam capture --
    CAMERA_INDEX: int = config("CAMERA_INDEX", default=0, cast=int)
    FRAME_SAMPLE_INTERVAL_SECONDS: float = config(
        "FRAME_SAMPLE_INTERVAL_SECONDS", default=0.5, cast=float
    )

    # -- Detection / tracking --
    # Used by detector.YoloVehicleDetector, the default since Step 4.
    VEHICLE_MODEL_PATH: str = config("VEHICLE_MODEL_PATH", default="models/yolov8n.pt")
    VEHICLE_CONFIDENCE_THRESHOLD: float = config(
        "VEHICLE_CONFIDENCE_THRESHOLD", default=0.4, cast=float
    )
    # Only used if detector.MotionVehicleDetector (the Step 2 zero-dependency
    # fallback) is swapped in instead.
    MIN_VEHICLE_AREA: int = config("MIN_VEHICLE_AREA", default=6000, cast=int)
    TRACK_MAX_AGE_SECONDS: float = config("TRACK_MAX_AGE_SECONDS", default=2.0, cast=float)

    # -- Deduplication --
    DEDUP_WINDOW_SECONDS: int = config("DEDUP_WINDOW_SECONDS", default=10, cast=int)

    # -- Outbound payload --
    SEND_PLATE_IMAGE: bool = config("SEND_PLATE_IMAGE", default=True, cast=bool)
