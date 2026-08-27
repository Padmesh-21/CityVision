# Camera Node

An edge ANPR pipeline that runs on a laptop, using its webcam as a
simulated CCTV camera:

```
Webcam -> Frame Sampling -> Vehicle Detection -> Plate Detection
   -> Plate Crop -> Preprocessing -> OCR -> Deduplication
   -> POST /api/detections/ on the Django backend
```

## Files

| File | Responsibility |
|---|---|
| `config.py` | Loads all settings from `.env` -- server URL, camera identity/location, thresholds |
| `camera.py` | Opens the webcam via OpenCV, yields frames sampled at a fixed interval |
| `detector.py` | `VehicleDetector` interface + `YoloVehicleDetector` (pretrained YOLOv8) |
| `plate_detector.py` | `PlateDetector` interface + `YoloPlateDetector` (YOLOv8 fine-tuned for plates) |
| `preprocessing.py` | OpenCV preprocessing: resize, grayscale, CLAHE contrast |
| `ocr.py` | `OCRModel` interface + `EasyOCRModel` (pretrained) |
| `plate_format.py` | Indian plate format validation + OCR-confusion correction (e.g. `O`<->`0`) using the known `SSDDLLNNNN` layout |
| `tracker.py` | Frame-to-frame centroid tracking, so OCR runs once per vehicle track, not once per frame |
| `deduplication.py` | Suppresses re-sending the same plate within a configurable time window |
| `api_client.py` | POSTs detection events to Django, authenticated with the camera's API key |
| `main.py` | Wires all of the above into the capture loop |
| `evaluate.py` | OCR accuracy evaluation harness (character accuracy, exact-match, precision/recall, confusions) |
| `debug_view.py` | Live OpenCV window showing every detection stage (see "Debugging" below) |

## Models (Step 4)

| Stage | Model | Pretrained or trained? |
|---|---|---|
| Vehicle detection | YOLOv8n (COCO), filtered to car/motorcycle/bus/truck | Pretrained, used as-is -- "is this a vehicle" transfers directly from COCO, no fine-tuning needed |
| Plate localization | YOLOv8n fine-tuned specifically on license plate images (`YoloPlateDetector`) | Pretrained by a third party specifically for this task (COCO has no "license plate" class at all, so the vehicle model's own weights can't do this) |
| OCR | EasyOCR (pretrained English scene-text recognizer) | Pretrained, **not** fine-tuned for license plates |

**Getting the plate-detection model:** unlike `yolov8n.pt` (a stock
ultralytics weight that auto-downloads by name), this is a third-party
fine-tuned checkpoint and has to be fetched once per machine:

```powershell
curl.exe -L -o models/license_plate_yolov8n.pt https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt
```

(Verified: single class `license_plate`, correctly detects a real plate
at 0.88 confidence, tight/accurate box -- see "Verified" below. 42k+
downloads on Hugging Face as of writing.)

**Known limitation, stated plainly:** EasyOCR is a general scene-text
engine. It was not trained on Indian plates specifically, which have two
failure modes it doesn't know about: two-line motorcycle plates, and
non-standard/stylized fonts that are common in practice despite the
official HSRP standard. `plate_format.py` corrects common single-character
OCR confusions using the known plate layout, which helps regardless of
engine, but it can't fix a fundamentally misread plate. It also trims
stray leading characters when OCR reads more than the expected 10 --
real Indian plates commonly have an "IND" hologram/state emblem to the
left of the plate number, which EasyOCR sometimes merges into the same
text run as one detected region; since the plate number is always the
trailing part of that run, trimming to the last 10 characters recovers
it without guessing at a segmentation.

**Preprocessing, tested not assumed:** `preprocessing.py` used to also
hard-threshold the crop to pure black/white and deskew it, on the
assumption that a "clean" binary image helps OCR. Tested against a real
plate photo with known ground truth, comparing exact variants through
the real EasyOCR model, that assumption was backwards for this engine --
binarization made readings worse, sometimes catastrophically (a
perfectly legible crop reading as a single stray character). EasyOCR's
model was trained on natural scene text and does its own internal
preprocessing; a resized, contrast-enhanced (CLAHE) *grayscale* image
outperformed a hand-thresholded binary mask in every configuration
tried. See "Verified" below for the numbers.

**The plan, not just an assumption:** don't trust an accuracy number for
this pipeline that wasn't measured on real photos. Run `evaluate.py`
(below) against real Indian plate images once you have some; fine-tune
EasyOCR's recognition model (or swap in a different `OCRModel`) only if
that measurement shows it's needed. This project doesn't yet have real
Indian plate photos to test against -- see "Measuring real accuracy."

`preprocessing.py` and `plate_format.py` are real, not placeholders --
pure OpenCV/regex logic that benefits any OCR engine behind the
interface, so they're implemented for keeps rather than as stand-ins.

## Measuring real accuracy

```powershell
python evaluate.py
```

If `test_data/plates/` doesn't exist or is empty, this **generates a
synthetic dataset** (rendered text, mild rotation/blur/noise) so the
harness itself can be exercised -- and says so loudly in its output
(`dataset_is_synthetic: true`). Synthetic results say nothing about
real-world accuracy; they only prove the measurement code works.

To measure *real* accuracy: drop real plate photos into
`test_data/plates/`, named `<GROUND_TRUTH_PLATE>...jpg` (e.g.
`TN09AB1234.jpg`, `TN09AB1234_angle2.jpg`), delete the `.synthetic`
marker file in that folder, and rerun. The report
(`evaluation_report.json`) includes character accuracy, exact-plate
accuracy, precision, recall, mean confidence, and the most common
character confusions -- the last one tells you exactly which OCR mistake
to fix first (e.g. if `O->0` dominates, that's likely already handled by
`plate_format.py`; a less obvious one might point at a font issue).

## Setup

```powershell
cd D:\Programs\Projects\Hackathon\anpr-platform\camera_node
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`easyocr` unconditionally depends on `opencv-python-headless`, which
gets installed alongside the `opencv-python` this project actually needs
and silently breaks any GUI window (`cv2.imshow`, used by
`debug_view.py`) with `The function is not implemented. Rebuild the
library with Windows, GTK+ 2.x or Cocoa support`. Fix it once per venv,
right after the install above:

```powershell
pip uninstall -y opencv-python-headless
pip install --force-reinstall --no-deps opencv-python==4.10.0.84
```

(`main.py` and `evaluate.py` never call `cv2.imshow`, so they work either
way -- this only bites you if you run `debug_view.py`.)

Also download the plate-detection model (see "Models" below for
details/verification -- `yolov8n.pt`, the vehicle model, auto-downloads
on first run, but this one doesn't):

```powershell
curl.exe -L -o models/license_plate_yolov8n.pt https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt
```

Edit `.env`:
- `SERVER_URL` -- where the Django backend from Step 1 is running.
- `CAMERA_ID` / `API_KEY` -- must match a `Camera` already created via
  `POST /api/cameras/` (the API key is only ever shown once, at
  creation -- use `POST /api/cameras/<id>/regenerate_api_key/` as ADMIN if
  you lost it).
- `LATITUDE` / `LONGITUDE` / `DIRECTION` -- should match that same Camera
  record.

## Running

Make sure the Django backend from Step 1 is running first (`python
manage.py runserver 0.0.0.0:8000` from `backend/`), then:

```powershell
python main.py
```

As of Step 4, `main.py` uses the real `YoloVehicleDetector` by default,
which -- unlike Step 2/3's motion detector -- only fires on an actual
car/motorcycle/bus/truck. Pointing the webcam at an empty room now
correctly produces **no** detections. To see a live detection, show the
webcam an actual vehicle (or a printed/on-screen photo of one with a
legible plate). You'll see log lines like:

```
[...] INFO camera_node.CAM001: Track 1 -> plate=TN09AB1234 (raw=TNO9ABI234) confidence=0.83
[...] INFO camera_node.CAM001: Sent detection id=2 vehicle_id=2
```

(`raw=` shows what EasyOCR actually read before `plate_format.py`'s
format-aware correction cleaned it up.)

If the plate happens to be on your `Blacklist` (see the Step 1 API),
you'll instead see `-- ALERT GENERATED`.

Stop with `Ctrl+C`.

## Debugging: "is it even detecting the plate?"

`main.py` is deliberately silent when nothing happens: it only runs
plate detection *inside* a box YOLO already classified as a vehicle
(car/motorcycle/bus/truck). If you point the webcam at, say, a phone
held up showing a plate photo, YOLO won't classify a hand holding a
phone as a vehicle, so `vehicle_boxes` stays empty and plate
detection/OCR never runs -- with no log line telling you why.

Run `python debug_view.py` instead to see every stage live in a window:

- **yellow box** -- anything YOLO recognizes at all, any COCO class
  (so you can tell "YOLO sees nothing" apart from "YOLO sees something,
  just not a vehicle")
- **green box** -- specifically a vehicle class
- **blue box** -- a plate found by `YoloPlateDetector`, run directly on
  the *full frame* (not gated behind a vehicle box), so you can test
  plate localization and OCR in isolation from vehicle detection
- a second window shows the preprocessed plate crop and prints the raw
  vs. format-corrected OCR text to the console

Press `q` in the video window to quit. If you're testing with a plate
photo on your phone, hold it close enough and steady enough that the
plate fills a reasonable fraction of the frame and stays in focus.

## Verified

**Step 2/3:** real webcam capture via OpenCV
(`cv2.VideoCapture(0, cv2.CAP_DSHOW)`), against a live local Django
server, with detections landing correctly in MySQL (including the
uploaded plate-crop image); four concurrent camera identities with
correct per-camera attribution.

**Step 4 (real models):**
- `YoloVehicleDetector` on a real photo (bus, 0.87 confidence, correct
  COCO class filtering) and on the live webcam feed (correctly detects
  **zero** vehicles in an empty room -- no false positives).
- `EasyOCRModel`: real pretrained detection + recognition models
  downloaded and loaded; scored 100% exact-match on `evaluate.py`'s
  synthetic dataset (expected -- clean rendered text is easy; this is
  **not** a real-world accuracy claim, see "Measuring real accuracy").
- Full chain (YOLO vehicle -> YOLO plate -> preprocessing -> EasyOCR ->
  `plate_format.correct_plate`) run on a real photo without errors, and
  the empty-OCR-result case (no legible plate in frame) handled cleanly
  rather than crashing or hallucinating text.
- `evaluate.py` itself: caught and fixed a real bug where a dataset
  generated as synthetic would be mis-reported as non-synthetic on a
  later run -- now tracked via an explicit `.synthetic` marker file
  rather than "is the directory non-empty."

**Plate detector swap + preprocessing rework** (measured on the one real
Indian plate photo in `test_data/plates/`, ground truth `MH20DV2366`):

| Change | Character accuracy | Notes |
|---|---|---|
| Original (`LocalPlateDetector` + hard-threshold preprocessing) | 60% | `evaluate.py`'s original recorded number |
| New (`YoloPlateDetector` + CLAHE-only preprocessing + IND-badge trim) | 90% | Only remaining error: `M` misread as `H`/`N`, likely residual "IND" badge pixels bleeding into the first character |
| Same change, measured via `evaluate.py`'s harness (runs on the raw uncropped photo, not a tight crop -- a harder test) | 80% | Confirms the preprocessing change helps even without the plate-detector crop |

Also confirmed: `YoloPlateDetector` on this photo returns a tight,
visually correct box (0.88 confidence) around just the plate -- a human
eye can read the crop cleanly. `LocalPlateDetector`'s classical CV
approach found a looser, less precise box on the same photo.

## Running multiple nodes (Step 3)

**On real separate laptops** (the production simulation): copy this whole
`camera_node/` folder to each laptop, create one `Camera` per laptop via
`POST /api/cameras/` (e.g. `CAM002`), and give each laptop's `.env` that
camera's `CAMERA_ID`/`API_KEY`, pointed at the same `SERVER_URL` (your
host machine's LAN IP, e.g. `http://192.168.1.100:8000`). The code is
identical on every laptop -- only `.env` differs.

**On one development machine** (no extra laptops handy yet): `config.py`
reads its env file from the `CAMERA_ENV_FILE` environment variable
(default `.env`), so you can run several node identities from this same
directory, all sharing this machine's one webcam:

```powershell
# terminal 1
python main.py                                  # uses .env -> CAM001

# terminal 2
$env:CAMERA_ENV_FILE=".env.cam002"; python main.py

# terminal 3
$env:CAMERA_ENV_FILE=".env.cam003"; python main.py

# terminal 4
$env:CAMERA_ENV_FILE=".env.cam004"; python main.py
```

`.env.cam002` / `.env.cam003` / `.env.cam004` already point at CAM002
(Guindy), CAM003 (T Nagar) and CAM004 (Adyar) -- created on the backend
alongside CAM001 (Anna Nagar). This is a hardware stand-in only: on this
one machine, several processes share the one physical webcam
concurrently (each opens its own `cv2.VideoCapture` handle), which is
why frame rates dip a bit with more nodes running. On real separate
laptops each node gets its own dedicated webcam and this isn't a
concern.

### Verified (Step 3)

Ran all four nodes concurrently against a live local Django server for
25 seconds each. Confirmed in MySQL afterward:
- Every detection was attributed to the correct `camera_id` -- no
  cross-camera mixups despite four processes hitting the same endpoint
  at once.
- Each `Camera.last_seen` updated independently.
- One mock plate (`TN07EF4321`) happened to come up on CAM002, CAM003
  and CAM004, producing a real cross-camera trajectory in chronological
  order (Guindy -> T Nagar -> Adyar) -- exactly the query Step 5's
  trajectory endpoint will run.
- A blacklisted plate detected on CAM001 correctly produced
  `alert_generated: true`.
