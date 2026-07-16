"""SRT parsing utilities."""

import re
from dataclasses import dataclass
from pathlib import Path

TIME_RE = re.compile(
    r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)"
)


@dataclass(frozen=True)
class SubtitleEntry:
    """A single parsed subtitle entry."""

    start: float
    end: float
    text: str


def parse_srt(srt_path: Path) -> list[SubtitleEntry]:
    """Parse an SRT file into a list of subtitle entries."""
    content = srt_path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\s*\n", content.strip())
    entries: list[SubtitleEntry] = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        time_line = lines[1]
        # Preserve explicit line breaks already present in the SRT file.
        text = "\n".join(lines[2:]).strip()
        if not text:
            continue

        match = TIME_RE.match(time_line)
        if not match:
            continue

        start = _to_seconds(*match.groups()[0:4])
        end = _to_seconds(*match.groups()[4:8])
        entries.append(SubtitleEntry(start=start, end=end, text=text))

    return entries


def _to_seconds(hours: str, minutes: str, seconds: str, millis: str) -> float:
    """Convert SRT time components to seconds."""
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0
