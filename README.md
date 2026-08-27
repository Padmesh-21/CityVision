# ANPR & City Traffic Intelligence Platform

A distributed multi-camera Automatic Number Plate Recognition (ANPR)
platform. Laptop webcams currently simulate city-wide camera nodes; the
architecture is designed so they can be swapped for real RTSP/IP CCTV
cameras later without touching the database schema, trajectory engine,
analytics engine, alert engine, or the React dashboard -- only the
ingestion layer (`camera_node/`) changes.

## Status

Being built incrementally. See the step-by-step plan below.

- [x] **Step 1 -- Backend foundation**: Django + DRF + MySQL, core models
      (User, Camera, Vehicle, Detection, Blacklist, Alert), JWT auth,
      camera API-key auth, admin panel.
- [x] **Step 2 -- Camera node**: OpenCV webcam capture, frame sampling,
      modular `VehicleDetector`/`PlateDetector`/`OCRModel` interfaces
      (mock implementations for now), real preprocessing, tracking,
      deduplication, and a working API client -- verified end-to-end
      against the Step 1 backend.
- [x] **Step 3 -- Multi-camera communication**: 4 camera identities
      (CAM001 Anna Nagar, CAM002 Guindy, CAM003 T Nagar, CAM004 Adyar)
      running concurrently against the same Django server, verified with
      correct per-camera attribution and a real cross-camera trajectory.
- [x] **Step 4 -- AI/OCR integration**: pretrained YOLOv8 vehicle
      detector (real, no training needed), classical CV plate
      localization (no trained model), pretrained EasyOCR + Indian
      plate format-correction, and an accuracy evaluation harness
      (`evaluate.py`) -- explicitly flags synthetic vs. real results so
      no accuracy number is trusted without real Indian plate photos.
- [x] **Step 5 -- Trajectory reconstruction + analytics**: `GET
      /api/vehicles/<plate>/trajectory/`, plus `/api/analytics/`
      summary, route-density, average-speed and heatmap endpoints --
      all derived live from `Detection` rows, no new tables. Verified
      against real multi-camera test data; caught and fixed a MySQL
      timezone-table gap that was silently zeroing out hourly stats.
- [x] **Step 6 -- React GIS dashboard**: Vite + React, JWT auth with
      silent token refresh, Leaflet map (camera markers, trajectory
      polylines, alert markers, heatmap layer), Recharts analytics,
      Dashboard/Vehicle Search/Analytics/Alerts/Cameras pages. Verified
      live in a real (headless) browser against the real backend --
      every page, zero console errors, real cross-camera trajectory
      rendered on the map.
- [ ] Step 7 -- Real-time alerts (Django Channels)
- [ ] Step 8 -- Optimization & scalability (Celery, Redis, RTSP)

## Architecture

```text
Laptop Webcam (edge node)
   -> local vehicle/plate detection + OCR + dedup
   -> POST /api/detections/  (X-API-Key auth)
        -> Django REST API
             -> normalize plate, find/create Vehicle, create Detection
             -> check Blacklist -> create Alert if matched
        -> MySQL (Users, Cameras, Vehicles, Detections, Blacklist, Alerts)
   -> React dashboard (JWT auth) reads via GET endpoints
```

Trajectories are *derived*, not stored: a vehicle's path across the city is
just its `Detection` rows ordered by `timestamp`.

## Repository layout

```text
anpr-platform/
├── backend/        Django project (see backend/ for setup instructions)
├── camera_node/    Edge camera application (Step 2+)
├── frontend/       React dashboard (Step 6+)
├── models/         AI model weights (Step 4+)
├── docs/           Architecture/database/API/deployment docs
└── README.md
```

## Backend setup

See the setup, testing and API instructions provided alongside Step 1 in
the project chat (they will be copied into `docs/` as the platform grows).
