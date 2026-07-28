"""Tests for audio extraction helpers."""

import shutil
import wave
from pathlib import Path

import pytest

from suburn.audio import extract_audio
from suburn.utils import run_command


def _generate_silent_video(path: Path, duration: int = 1) -> None:
    """Create a short silent MP4 video for testing."""
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s=320x240:d={duration}",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(path),
        ]
    )


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_extract_audio_creates_valid_wav(tmp_path: Path) -> None:
    """Extracting audio should produce a readable 16kHz mono WAV file."""
    video_path = tmp_path / "silent.mp4"
    output_wav = tmp_path / "output.wav"

    _generate_silent_video(video_path)
    result = extract_audio(video_path, output_wav)

    assert result == output_wav
    assert result.exists()
    assert result.stat().st_size > 44  # larger than a minimal WAV header

    with wave.open(str(result), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getsampwidth() == 2
        assert wav.getnframes() > 0
