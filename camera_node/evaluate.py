"""OCR accuracy evaluation harness.

Computes character accuracy, exact-plate accuracy, precision, recall,
mean confidence and character-confusion counts for the OCR stage, on a
labeled set of plate crop images.

Do NOT trust any accuracy number from this script until it has been run
against real captured plate images -- see the "Measuring real accuracy"
section of camera_node/README.md. If `test_data/plates/` is empty or
missing, this generates a small SYNTHETIC dataset instead (clearly
labeled as such in the output) purely so the harness itself can be
exercised; synthetic results say nothing about real-world accuracy on
actual Indian plates.

Usage:
    python evaluate.py                        # auto: real data if present, else synthetic
    python evaluate.py --data-dir path/to/plates
    python evaluate.py --ocr mock             # use MockOCRModel instead of EasyOCR

Expected data format: one image per file, named "<GROUND_TRUTH_PLATE>...jpg"
e.g. TN09AB1234.jpg, TN09AB1234_angle2.jpg, KA05MH4321_blur.jpg
"""

import argparse
import difflib
import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from ocr import EasyOCRModel, MockOCRModel, OCRModel
from plate_format import correct_plate
from preprocessing import preprocess_plate

logger = logging.getLogger("evaluate")

DEFAULT_DATA_DIR = Path(__file__).parent / "test_data" / "plates"

# Used only to generate the synthetic fallback dataset -- arbitrary
# well-formed plates, not real vehicle records.
_SYNTHETIC_PLATES = ["TN09AB1234", "KA05MH4321", "MH12CD7890", "DL03EF5678", "AP07GH9012"]

# Marker file dropped alongside a generated synthetic dataset. Its
# presence -- not merely "the directory has files in it" -- is what
# `main()` checks before deciding whether to print the "SYNTHETIC, not
# real-world" warning: a directory that already contains synthetic
# images from a previous run must still be reported as synthetic.
_SYNTHETIC_MARKER = ".synthetic"


@dataclass
class SampleResult:
    filename: str
    ground_truth: str
    predicted_raw: str
    predicted_corrected: str
    confidence: float
    exact_match: bool
    char_accuracy: float
    precision: float
    recall: float
    confusions: list[tuple[str, str]] = field(default_factory=list)


def generate_synthetic_dataset(out_dir: Path, count_per_plate: int = 3) -> None:
    """Renders known plate strings with mild rotation/blur/noise so this
    harness has something to run against before real Indian plate photos
    are collected. This is a synthetic sanity check, not a real-world
    accuracy measurement."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)

    for plate in _SYNTHETIC_PLATES:
        for i in range(count_per_plate):
            img = np.full((120, 400, 3), 235, dtype=np.uint8)
            cv2.putText(
                img, plate, (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (20, 20, 20), 4, cv2.LINE_AA
            )

            angle = rng.uniform(-8, 8)
            center = (img.shape[1] // 2, img.shape[0] // 2)
            rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(
                img, rot_matrix, (img.shape[1], img.shape[0]), borderValue=(235, 235, 235)
            )

            if rng.random() < 0.5:
                ksize = int(rng.choice([3, 5]))
                img = cv2.GaussianBlur(img, (ksize, ksize), 0)

            noise = rng.normal(0, 8, img.shape)
            img = np.clip(img.astype(np.int16) + noise.astype(np.int16), 0, 255).astype(np.uint8)

            cv2.imwrite(str(out_dir / f"{plate}_{i}.jpg"), img)

    (out_dir / _SYNTHETIC_MARKER).touch()
    logger.info(
        "Generated %d SYNTHETIC test images in %s", len(_SYNTHETIC_PLATES) * count_per_plate, out_dir
    )


def _compare(ground_truth: str, predicted: str) -> tuple[float, float, float, list[tuple[str, str]]]:
    """Character-level accuracy/precision/recall via sequence alignment,
    plus the specific (ground_truth_char, predicted_char) substitutions
    -- aggregating these across a dataset reveals systematic OCR
    confusions (e.g. O<->0) even when overall accuracy looks fine."""
    matcher = difflib.SequenceMatcher(None, ground_truth, predicted)
    matched = sum(block.size for block in matcher.get_matching_blocks())

    confusions = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            confusions.extend(zip(ground_truth[i1:i2], predicted[j1:j2]))

    char_accuracy = matched / max(len(ground_truth), 1)
    precision = matched / max(len(predicted), 1)
    recall = matched / max(len(ground_truth), 1)
    return char_accuracy, precision, recall, confusions


_IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")


def evaluate(data_dir: Path, ocr_model: OCRModel) -> list[SampleResult]:
    results = []
    image_paths = sorted(
        path for pattern in _IMAGE_EXTENSIONS for path in data_dir.glob(pattern)
    )

    for path in image_paths:
        ground_truth = path.stem.split("_")[0].upper()
        image = cv2.imread(str(path))
        if image is None:
            logger.warning("Could not read %s, skipping", path)
            continue

        preprocessed = preprocess_plate(image)
        raw_text, confidence = ocr_model.read_plate(preprocessed)
        corrected_text = correct_plate(raw_text)

        char_accuracy, precision, recall, confusions = _compare(ground_truth, corrected_text)
        results.append(
            SampleResult(
                filename=path.name,
                ground_truth=ground_truth,
                predicted_raw=raw_text,
                predicted_corrected=corrected_text,
                confidence=confidence,
                exact_match=corrected_text == ground_truth,
                char_accuracy=char_accuracy,
                precision=precision,
                recall=recall,
                confusions=confusions,
            )
        )
    return results


def summarize(results: list[SampleResult]) -> dict:
    if not results:
        return {"sample_count": 0}

    confusion_counter: Counter = Counter()
    for result in results:
        confusion_counter.update(result.confusions)

    return {
        "sample_count": len(results),
        "exact_plate_accuracy": sum(r.exact_match for r in results) / len(results),
        "mean_character_accuracy": sum(r.char_accuracy for r in results) / len(results),
        "mean_precision": sum(r.precision for r in results) / len(results),
        "mean_recall": sum(r.recall for r in results) / len(results),
        "mean_confidence": sum(r.confidence for r in results) / len(results),
        "top_confusions": [f"{gt}->{pred}: {count}" for (gt, pred), count in confusion_counter.most_common(10)],
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--ocr", choices=["easyocr", "mock"], default="easyocr")
    parser.add_argument("--report", type=Path, default=Path("evaluation_report.json"))
    args = parser.parse_args()

    needs_generation = not args.data_dir.exists() or not any(args.data_dir.iterdir())
    if needs_generation:
        generate_synthetic_dataset(args.data_dir)

    # Checked via the marker file dropped by generate_synthetic_dataset,
    # not "did we just generate it" -- so a *previously* generated
    # synthetic dataset is still correctly flagged on later runs instead
    # of silently being reported as real.
    is_synthetic = (args.data_dir / _SYNTHETIC_MARKER).exists()
    if is_synthetic:
        logger.warning(
            "%s contains a SYNTHETIC dataset (see .synthetic marker). The numbers "
            "below do NOT represent real-world accuracy on actual Indian license "
            "plates. Replace it with real photos (filename = ground-truth plate, "
            "e.g. TN09AB1234.jpg) and delete the .synthetic marker before trusting "
            "any accuracy figure.",
            args.data_dir,
        )

    ocr_model: OCRModel = MockOCRModel() if args.ocr == "mock" else EasyOCRModel()

    results = evaluate(args.data_dir, ocr_model)
    summary = summarize(results)
    summary["dataset_is_synthetic"] = is_synthetic

    print(json.dumps(summary, indent=2))
    args.report.write_text(json.dumps(summary, indent=2))
    logger.info("Full report written to %s", args.report)


if __name__ == "__main__":
    main()
