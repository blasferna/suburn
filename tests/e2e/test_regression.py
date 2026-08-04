"""Regression tests for known audio extraction issues."""

import shutil
from pathlib import Path

import pytest

from suburn.transcribe import transcribe_video
from suburn.utils import run_command

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _generate_black_video_with_audio(
    audio_path: Path, output_video: Path, duration: int = 10
) -> None:
    """Generate a video with a black screen and the provided audio track."""
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s=640x480:d={duration}",
            "-i",
            audio_path,
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            output_video,
        ]
    )


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_transcribe_regression_audio_with_black_video(tmp_path: Path) -> None:
    """A real audio track muxed with a synthetic black video must be transcribable.

    This uses a short audio fixture extracted from the MKV that triggered the
    WAV decoder regression, paired with a generated black video so no video
    content from the original file is exposed in the repository.
    """
    audio_fixture = FIXTURES / "regression_audio.mp3"
    if not audio_fixture.exists():
        pytest.skip("regression audio fixture not found")

    video_path = tmp_path / "regression_video.mp4"
    _generate_black_video_with_audio(audio_fixture, video_path, duration=10)

    output_srt = tmp_path / "output.srt"
    result = transcribe_video(
        video_path,
        "tiny.en",
        output_srt=output_srt,
        threads=4,
    )

    assert result == output_srt
    assert result.exists()
    assert result.stat().st_size > 0
    content = result.read_text(encoding="utf-8")
    assert "-->" in content
