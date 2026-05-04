"""Ingest the Kitzur Shulchan Aruch source into one Markdown file per seif.

For each row of `sorce_files/kitzur_shulchan_aruch.txt`:
    {siman_field}|{seif_letter}|{text}

write `data/seifim/{siman_idx:03d}__{seif_idx:03d}.md` containing:
    # סימן {siman_letter} - {chapter_title}
    ## סעיף {seif_letter}

    {text}

Indices are gematria values of the Hebrew letters; chapter title has its
"ובו X סעיפים" suffix and trailing colon stripped. Idempotent: wipes
data/seifim/ at the start of each run.
"""
from __future__ import annotations
import re
import shutil
import sys
from pathlib import Path

from kitzur_core.config import SOURCE_FILE, SEIFIM_DIR

HEBREW_TO_INT = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80, "צ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
    "ך": 20, "ם": 40, "ן": 50, "ף": 80, "ץ": 90,
}

_STRIP_MARKS_RE = re.compile(r"[\"'׳״\s]")
_SIMAN_RE = re.compile(r"^סימן\s+(\S+?)(?:\s+-\s+(.+))?$")
_OBO_RE = re.compile(r"\s*ובו\s+\S+\s*סעיפים\s*$")


def gematria(s: str) -> int:
    cleaned = _STRIP_MARKS_RE.sub("", s)
    return sum(HEBREW_TO_INT.get(c, 0) for c in cleaned)


def parse_siman_field(field: str) -> tuple[str, str, int]:
    cleaned = field.strip().rstrip(":")
    m = _SIMAN_RE.match(cleaned)
    if not m:
        raise ValueError(f"unparseable siman field: {field!r}")
    siman_letter = m.group(1)
    chapter = (m.group(2) or "").strip()
    chapter = _OBO_RE.sub("", chapter).strip().rstrip(":")
    return siman_letter, chapter, gematria(siman_letter)


def main() -> int:
    if not SOURCE_FILE.exists():
        print(f"Source not found: {SOURCE_FILE}", file=sys.stderr)
        return 1

    if SEIFIM_DIR.exists():
        shutil.rmtree(SEIFIM_DIR)
    SEIFIM_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped: list[tuple[int, str]] = []

    with SOURCE_FILE.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\r\n")
            if not line:
                continue
            if lineno == 1 and line.startswith("siman|"):
                continue
            parts = line.split("|", 2)
            if len(parts) != 3:
                skipped.append((lineno, "wrong column count"))
                continue
            siman_field, seif_letter, text = parts
            try:
                siman_letter, chapter_title, siman_idx = parse_siman_field(siman_field)
            except ValueError as e:
                skipped.append((lineno, str(e)))
                continue
            seif_idx = gematria(seif_letter)
            if siman_idx == 0 or seif_idx == 0:
                skipped.append((lineno, f"zero index siman={siman_letter!r} seif={seif_letter!r}"))
                continue

            heading = f"# סימן {siman_letter}"
            if chapter_title:
                heading += f" - {chapter_title}"
            body = f"{heading}\n## סעיף {seif_letter}\n\n{text}\n"

            filename = f"{siman_idx:03d}__{seif_idx:03d}.md"
            (SEIFIM_DIR / filename).write_text(body, encoding="utf-8")
            written += 1

    print(f"Wrote {written} seif files to {SEIFIM_DIR}")
    if skipped:
        print(f"Skipped {len(skipped)} lines:", file=sys.stderr)
        for lineno, reason in skipped[:10]:
            print(f"  line {lineno}: {reason}", file=sys.stderr)
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more", file=sys.stderr)
    return 0 if written > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
