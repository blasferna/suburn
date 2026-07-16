"""Audio extraction helpers."""

import tempfile
from pathlib import Path

from suburn.utils import log_info, require_command, run_command


def extract_audio(video_path: Path, output_wav: Path | None = None) -> Path:
    """Extract audio from a video file into a 16kHz mono WAV for whisperfile.

    If no output path is provided, a temporary file is created.
    """
    ffmpeg = require_command("ffmpeg")

    if output_wav is None:
        suffix = f"_{video_path.stem}.wav"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="suburn_audio_")
        output_wav = Path(tmp_path)
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
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            output_wav,
        ]
    )
    return output_wav
