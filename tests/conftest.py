"""Shared pytest fixtures for suburn tests."""

import os
import urllib.request
from pathlib import Path

import pytest

from suburn.models import ensure_model
from suburn.utils import run_command

# Use a test-specific model directory so E2E tests don't pollute user data.
TEST_CACHE = Path(__file__).parent / ".cache"
MODEL_DIR = TEST_CACHE / "models"
AUDIO_DIR = TEST_CACHE / "audio"
VIDEO_DIR = TEST_CACHE / "video"

os.environ.setdefault("SUBURN_MODEL_DIR", str(MODEL_DIR))

SAMPLE_AUDIO_URL = (
    "https://huggingface.co/Mozilla/whisperfile/resolve/main/raven_poe_64kb.mp3"
)
TEST_MODEL_ALIAS = "tiny.en"


def _download_file(url: str, destination: Path) -> None:
    """Download a file if it does not already exist."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    urllib.request.urlretrieve(url, destination)


@pytest.fixture(scope="session")
def tiny_model_path() -> Path:
    """Ensure the tiny.en whisperfile model is available for tests."""
    return ensure_model(TEST_MODEL_ALIAS)


@pytest.fixture(scope="session")
def sample_audio_path() -> Path:
    """Download a short speech sample for testing."""
    path = AUDIO_DIR / "raven_poe_64kb.mp3"
    _download_file(SAMPLE_AUDIO_URL, path)
    return path


@pytest.fixture(scope="session")
def sample_video_path(sample_audio_path: Path) -> Path:
    """Generate a short MP4 video from the sample audio."""
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    video_path = VIDEO_DIR / "sample.mp4"

    if video_path.exists():
        return video_path

    # Create a 10-second 640x480 video with the sample audio.
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=640x480:d=10",
            "-i",
            sample_audio_path,
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            video_path,
        ]
    )
    return video_path
