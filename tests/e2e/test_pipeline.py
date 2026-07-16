"""End-to-end tests for the suburn pipeline."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from suburn.cli import app
from suburn.transcribe import transcribe_video
from suburn.video import burn_pipeline, generate_preview

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

runner = CliRunner()


def test_transcribe_video(sample_video_path: Path, tmp_path: Path) -> None:
    """Generate an SRT from a real video using the tiny model."""
    output_srt = tmp_path / "output.srt"
    result = transcribe_video(
        sample_video_path,
        "tiny.en",
        output_srt=output_srt,
        threads=4,
    )

    assert result.exists()
    assert result.stat().st_size > 0
    content = result.read_text(encoding="utf-8")
    assert "-->" in content


def test_burn_subtitles(sample_video_path: Path, tmp_path: Path) -> None:
    """Burn generated subtitles into a new MP4."""
    srt_path = tmp_path / "subs.srt"
    transcribe_video(sample_video_path, "tiny.en", output_srt=srt_path, threads=4)

    output_video = tmp_path / "output-sub.mp4"
    burn_pipeline(sample_video_path, output_video, srt_path)

    assert output_video.exists()
    assert output_video.stat().st_size > 0


def test_generate_preview(sample_video_path: Path, tmp_path: Path) -> None:
    """Generate a short preview with burned subtitles."""
    srt_path = tmp_path / "subs.srt"
    transcribe_video(sample_video_path, "tiny.en", output_srt=srt_path, threads=4)

    preview_video = tmp_path / "preview-test.mp4"
    generate_preview(sample_video_path, preview_video, srt_path, duration=5)

    assert preview_video.exists()
    assert preview_video.stat().st_size > 0


def test_cli_burn_command(sample_video_path: Path, tmp_path: Path) -> None:
    """Run the full ``suburn burn`` CLI command end-to-end."""
    output_video = tmp_path / "cli-sub.mp4"
    result = runner.invoke(
        app,
        [
            "burn",
            str(sample_video_path),
            "--model",
            "tiny.en",
            "--output",
            str(output_video),
            "--threads",
            "4",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_video.exists()
    assert output_video.stat().st_size > 0
