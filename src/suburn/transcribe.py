"""Transcription with whisperfile."""

import os
import shutil
import tempfile
from pathlib import Path

from suburn.audio import extract_audio
from suburn.config import DEFAULT_THREADS
from suburn.models import ensure_model
from suburn.utils import log_info, run_command


def transcribe_audio(
    audio_path: Path,
    model_path: Path,
    output_prefix: Path,
    *,
    language: str = "en",
    threads: int = DEFAULT_THREADS,
    gpu: str | None = None,
) -> Path:
    """Run whisperfile on an audio file and return the generated SRT path."""
    log_info("Transcribing audio with whisperfile...")

    # whisperfile models are APE (Actually Portable Executable) binaries.
    # Running them through the system shell interpreter is the most portable
    # way to execute them on Linux when the kernel's binfmt_misc APE handler
    # is not registered.
    cmd: list[str | Path] = [
        "sh",
        model_path,
        "-f",
        audio_path,
        "-osrt",
        "-of",
        output_prefix,
        "-l",
        language,
        "-t",
        str(threads),
    ]
    if gpu:
        cmd.extend(["--gpu", gpu])

    # whisperfile prints progress to stderr; stream it so the user sees it.
    run_command(cmd, capture_output=False)

    srt_path = Path(f"{output_prefix}.srt")
    if not srt_path.exists():
        raise RuntimeError(f"whisperfile did not produce expected SRT file: {srt_path}")
    return srt_path


def transcribe_video(
    video_path: Path,
    model_alias: str,
    *,
    output_srt: Path | None = None,
    language: str = "en",
    threads: int = DEFAULT_THREADS,
    gpu: str | None = None,
) -> Path:
    """Transcribe a video file and return the path to the generated SRT."""
    model_path = ensure_model(model_alias)

    fd, audio_wav = tempfile.mkstemp(suffix=".wav", prefix="suburn_audio_")
    os.close(fd)
    audio_wav_path = Path(audio_wav)

    fd, srt_prefix = tempfile.mkstemp(prefix="suburn_subs_")
    os.close(fd)
    srt_prefix_path = Path(srt_prefix)
    generated_srt = Path(f"{srt_prefix_path}.srt")

    try:
        extract_audio(video_path, audio_wav_path)
        transcribe_audio(
            audio_wav_path,
            model_path,
            srt_prefix_path,
            language=language,
            threads=threads,
            gpu=gpu,
        )

        if output_srt is not None:
            output_srt.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(generated_srt), str(output_srt))
            return output_srt
        return generated_srt
    finally:
        audio_wav_path.unlink(missing_ok=True)
        # Clean up any whisperfile sidecar files (txt, vtt, etc.) it may have created.
        for ext in (".txt", ".vtt", ".lrc", ".csv", ".json", ".wts"):
            Path(f"{srt_prefix_path}{ext}").unlink(missing_ok=True)
        # Only delete the generated SRT if the caller asked us to move it elsewhere.
        if output_srt is not None:
            generated_srt.unlink(missing_ok=True)
