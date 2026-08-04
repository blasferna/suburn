"""Tests for audio extraction helpers."""

import json
import shutil
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


def _generate_video_with_negative_start_time(path: Path, duration: int = 2) -> None:
    """Create an MKV where the audio stream starts at a negative timestamp.

    This emulates the kind of container produced by some ffmpeg versions that
    triggered the original ``-ss 0`` regression.
    """
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
            "-output_ts_offset",
            "-0.021",
            str(path),
        ]
    )


def _probe_mp3(path: Path) -> dict:
    """Return ffprobe JSON output for an audio file."""
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
    )
    return json.loads(result.stdout)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_extract_audio_creates_valid_mp3(tmp_path: Path) -> None:
    """Extracting audio should produce a readable 16kHz mono MP3 file."""
    video_path = tmp_path / "silent.mp4"
    output_mp3 = tmp_path / "output.mp3"

    _generate_silent_video(video_path)
    result = extract_audio(video_path, output_mp3)

    assert result == output_mp3
    assert result.exists()
    assert result.stat().st_size > 0

    probe = _probe_mp3(result)
    stream = probe["streams"][0]
    assert stream["codec_name"] == "mp3"
    assert stream["sample_rate"] == "16000"
    assert stream["channels"] == 1


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_extract_audio_preserves_full_duration_with_negative_start_time(
    tmp_path: Path,
) -> None:
    """Audio from containers with negative start times must not be truncated.

    Using ``-ss 0`` before the input trims the first audio samples. With WAV
    that produced a file whisperfile could not decode; with MP3 it still loses
    the negative-offset portion and shortens the result. The extracted audio
    must cover the full nominal duration.
    """
    video_path = tmp_path / "negative_start.mkv"
    output_mp3 = tmp_path / "output.mp3"
    duration = 2

    _generate_video_with_negative_start_time(video_path, duration=duration)
    result = extract_audio(video_path, output_mp3)

    probe = _probe_mp3(result)
    stream = probe["streams"][0]
    assert stream["codec_name"] == "mp3"
    extracted_seconds = float(stream["duration"])
    # The audio should cover the full nominal duration; an ``-ss 0``
    # regression would drop the ~21 ms of negative-offset audio.
    assert extracted_seconds >= duration
