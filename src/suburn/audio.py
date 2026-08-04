"""Audio extraction helpers."""

import tempfile
from pathlib import Path

from suburn.utils import log_info, require_command, run_command


def extract_audio(video_path: Path, output_audio: Path | None = None) -> Path:
    """Extract audio from a video file into a 16kHz mono MP3 for whisperfile.

    Whisperfile's WAV decoder is fragile with certain inputs (e.g. MKV files
    with negative start times or non-monotonic timestamps), so we feed it an
    MP3 instead. MP3 is reliably decoded by whisperfile and avoids the
    ``failed to read pcm frames`` error.

    If no output path is provided, a temporary file is created.
    """
    ffmpeg = require_command("ffmpeg")

    if output_audio is None:
        suffix = f"_{video_path.stem}.mp3"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="suburn_audio_")
        output_audio = Path(tmp_path)
        # Close the file descriptor; ffmpeg will write to the path.
        import os

        os.close(fd)

    log_info(f"Extracting audio from '{video_path.name}'...")
    run_command(
        [
            ffmpeg,
            "-y",
            "-i",
            video_path,
            "-vn",
            "-map",
            "0:a:0",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-b:a",
            "128k",
            output_audio,
        ]
    )
    return output_audio
