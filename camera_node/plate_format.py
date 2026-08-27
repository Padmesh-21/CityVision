"""Indian license plate format validation and OCR-confusion correction.

Standard format: SS DD L{1,3} NNNN
  SS   - 2-letter state code (e.g. TN, KA, MH)
  DD   - 1-2 digit RTO district code
  L    - 1-3 letter series
  NNNN - 4-digit number

Knowing this structure lets us correct common OCR character confusions
by position without retraining the OCR model -- e.g. an 'O' read in a
digit slot is almost certainly a '0'. This is cheap and has no external
dependency, so it's applied regardless of which OCR engine is behind
ocr.OCRModel.
"""

import re

_FULL_FORMAT_RE = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$")

# The exact layout used everywhere in this project's own examples and by
# far the most common on the road: 2 letters, 2 digits, 2 letters, 4
# digits (e.g. TN09AB1234). Correction is only attempted at this fixed
# length -- guessing a segmentation for the 1- or 3-character RTO/series
# variants would risk introducing errors rather than fixing them.
_CORRECTABLE_LAYOUT = "LLDDLLDDDD"

_DIGIT_LOOKS_LIKE_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z", "6": "G"}
_LETTER_LOOKS_LIKE_DIGIT = {"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6", "Q": "0"}


def is_valid_format(plate_number: str) -> bool:
    return bool(_FULL_FORMAT_RE.match(plate_number))


def correct_plate(raw: str) -> str:
    """Best-effort correction of common OCR character confusions using
    the known Indian plate layout. Returns the input unchanged (aside
    from uppercasing/stripping non-alphanumerics) if it isn't the
    correctable length."""
    candidate = re.sub(r"[^A-Z0-9]", "", raw.upper())
    layout_len = len(_CORRECTABLE_LAYOUT)

    if len(candidate) > layout_len:
        # Real Indian plates commonly have an "IND" hologram/state emblem
        # to the left of the plate number itself. OCR sometimes merges
        # that into the same text run (one detected region, not two), so
        # a too-long reading usually means stray characters *before* the
        # actual plate number, not after it -- the plate number is the
        # trailing run. Trimming to the last `layout_len` characters
        # recovers it without guessing at a segmentation.
        candidate = candidate[-layout_len:]

    if len(candidate) != layout_len:
        return candidate

    corrected_chars = []
    for char, expected in zip(candidate, _CORRECTABLE_LAYOUT):
        if expected == "L" and char.isdigit():
            corrected_chars.append(_DIGIT_LOOKS_LIKE_LETTER.get(char, char))
        elif expected == "D" and char.isalpha():
            corrected_chars.append(_LETTER_LOOKS_LIKE_DIGIT.get(char, char))
        else:
            corrected_chars.append(char)
    return "".join(corrected_chars)
