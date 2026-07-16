"""Video conversion and subtitle burning."""

import os
import subprocess
import tempfile
from pathlib import Path

from suburn.config import DEFAULT_BOX_COLOR, DEFAULT_FONT_COLOR, DEFAULT_FONT_SIZE, DEFAULT_POSITION
from suburn.subtitles import parse_srt
from suburn.utils import log_info, log_warn, require_command, run_command


def convert_to_mp4(input_path: Path, output_path: Path) -> None:
    """Convert a video to MP4, trying copy first and falling back to AAC audio."""
    ffmpeg = require_command("ffmpeg")
    log_info(f"Converting '{input_path.name}' to MP4...")

    try:
        run_command([ffmpeg, "-y", "-i", input_path, "-c", "copy", output_path])
        return
    except RuntimeError:
        log_warn("Direct copy failed, re-encoding audio to AAC...")

    run_command(
        [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            output_path,
        ]
    )


def _get_video_dimensions(input_path: Path) -> tuple[int, int]:
    """Return the width and height of the first video stream using ffprobe."""
    ffprobe = require_command("ffprobe")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            str(input_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    width, height = result.stdout.strip().split("x")
    return int(width), int(height)


def _ass_color(color: str) -> str:
    """Convert a color name or hex string to ASS BGR format.

    ASS color format is &HAABBGGRR. Accepted inputs:
    - Common color names (white, yellow, red, green, blue, cyan, magenta, black,
      grey/gray)
    - #RRGGBB hex strings
    - Already formatted &HAABBGGRR strings
    """
    if color.startswith("&H"):
        return color

    if color.startswith("#"):
        rgb = color.lstrip("#")
        if len(rgb) == 6:
            r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
            return f"&H00{b}{g}{r}"

    names = {
        "white": "&H00FFFFFF",
        "yellow": "&H0000FFFF",
        "red": "&H000000FF",
        "green": "&H0000FF00",
        "blue": "&H00FF0000",
        "cyan": "&H00FFFF00",
        "magenta": "&H00FF00FF",
        "black": "&H00000000",
        "grey": "&H00808080",
        "gray": "&H00808080",
    }
    if color.lower() in names:
        return names[color.lower()]

    # Fall back to white if the color is not understood.
    return "&H00FFFFFF"


def _ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format (H:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def _generate_ass_file(
    srt_path: Path,
    ass_path: Path,
    width: int,
    height: int,
    *,
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: str = DEFAULT_FONT_COLOR,
    box_color: str = DEFAULT_BOX_COLOR,
    position: str = DEFAULT_POSITION,
) -> None:
    """Convert an SRT file to an ASS file with a Netflix-style grey box."""
    primary = _ass_color(font_color)
    outline = _ass_color(box_color)
    alignment = 2 if position == "bottom" else 8
    margin_v = 60

    style = (
        f"Style: Default,DejaVu Sans,{font_size},{primary},&H00000000,"
        f"{outline},&H00000000,0,0,0,0,100,100,0,0,3,4,0,"
        f"{alignment},10,10,{margin_v},1"
    )

    events: list[str] = []
    for entry in parse_srt(srt_path):
        start = _ass_time(entry.start)
        end = _ass_time(entry.end)
        text = entry.text.replace("\n", "\\N")
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    ass_content = (
        "[Script Info]\n"
        "Title: suburn\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding\n"
        f"{style}\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        + "\n".join(events)
    )
    ass_path.write_text(ass_content, encoding="utf-8")


def _quote_filter_value(value: str) -> str:
    """Quote a value for safe use in an ffmpeg filter string.

    Single quotes are used as delimiters; internal single quotes are escaped
    with a backslash.
    """
    if "'" in value:
        value = value.replace("'", "\\'")
    return f"'{value}'"


def _build_ass_filter(ass_path: Path) -> str:
    """Build an ffmpeg -vf ass filter string."""
    quoted_path = _quote_filter_value(str(ass_path))
    return f"ass={quoted_path}"


def burn_subtitles(
    input_path: Path,
    output_path: Path,
    srt_path: Path,
    *,
    duration: float | None = None,
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: str = DEFAULT_FONT_COLOR,
    box_color: str = DEFAULT_BOX_COLOR,
    position: str = DEFAULT_POSITION,
) -> None:
    """Burn subtitles into a video using ffmpeg's ass filter with a generated ASS file."""
    ffmpeg = require_command("ffmpeg")
    log_info("Burning subtitles into video...")

    width, height = _get_video_dimensions(input_path)
    fd, tmp_ass = tempfile.mkstemp(suffix=".ass", prefix="suburn_ass_")
    os.close(fd)
    ass_path = Path(tmp_ass)

    try:
        _generate_ass_file(
            srt_path,
            ass_path,
            width,
            height,
            font_size=font_size,
            font_color=font_color,
            box_color=box_color,
            position=position,
        )
        filter_str = _build_ass_filter(ass_path)
        cmd: list[str | Path] = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vf",
            filter_str,
            "-c:a",
            "copy",
        ]
        if duration is not None:
            cmd.extend(["-t", str(duration)])
        cmd.append(output_path)
        run_command(cmd)
    finally:
        ass_path.unlink(missing_ok=True)


def prepare_video_for_burning(input_path: Path) -> tuple[Path, Path | None]:
    """Return a path suitable for ffmpeg burning and a temporary file to clean up.

    If the input is already MP4, return it directly. Otherwise convert to a temp MP4.
    """
    if input_path.suffix.lower() == ".mp4":
        return input_path, None

    fd, tmp_path = tempfile.mkstemp(suffix=".mp4", prefix="suburn_convert_")
    os.close(fd)
    tmp_output = Path(tmp_path)
    convert_to_mp4(input_path, tmp_output)
    return tmp_output, tmp_output


def burn_pipeline(
    input_path: Path,
    output_path: Path,
    srt_path: Path,
    *,
    duration: float | None = None,
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: str = DEFAULT_FONT_COLOR,
    box_color: str = DEFAULT_BOX_COLOR,
    position: str = DEFAULT_POSITION,
) -> None:
    """Convert if needed, then burn subtitles into a video."""
    entries = parse_srt(srt_path)
    if not entries:
        raise ValueError(f"No valid subtitle entries found in {srt_path}")

    prepared_video, tmp_video = prepare_video_for_burning(input_path)
    try:
        burn_subtitles(
            prepared_video,
            output_path,
            srt_path,
            duration=duration,
            font_size=font_size,
            font_color=font_color,
            box_color=box_color,
            position=position,
        )
    finally:
        if tmp_video is not None:
            tmp_video.unlink(missing_ok=True)


def generate_preview(
    input_path: Path,
    output_path: Path,
    srt_path: Path,
    duration: int,
    *,
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: str = DEFAULT_FONT_COLOR,
    box_color: str = DEFAULT_BOX_COLOR,
    position: str = DEFAULT_POSITION,
) -> None:
    """Generate a short preview with burned subtitles."""
    burn_pipeline(
        input_path,
        output_path,
        srt_path,
        duration=duration,
        font_size=font_size,
        font_color=font_color,
        box_color=box_color,
        position=position,
    )
