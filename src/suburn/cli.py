"""Command-line interface for suburn."""

from pathlib import Path
from typing import Annotated

import typer

from suburn import __version__
from suburn.config import (
    DEFAULT_BOX_COLOR,
    DEFAULT_FONT_COLOR,
    DEFAULT_FONT_SIZE,
    DEFAULT_POSITION,
    DEFAULT_PREVIEW_DURATION,
    DEFAULT_THREADS,
)
from suburn.models import (
    UnknownModelError,
    download_model,
    ensure_model,
    get_default_model,
    list_models,
    resolve_model,
)
from suburn.transcribe import transcribe_video
from suburn.utils import log_error, log_info, log_success
from suburn.video import burn_pipeline, convert_to_mp4, generate_preview

app = typer.Typer(
    name="suburn",
    help="Transcribe videos with whisperfile and burn subtitles with ffmpeg.",
    no_args_is_help=True,
)

models_app = typer.Typer(help="Manage whisperfile models.")
app.add_typer(models_app, name="models")


def _resolve_output(input_path: Path, suffix: str) -> Path:
    """Build a default output path from an input path and suffix."""
    return input_path.parent / f"{input_path.stem}{suffix}"


@app.command()
def transcribe(
    video: Annotated[Path, typer.Argument(help="Input video file.", exists=True, readable=True)],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output SRT file (default: <video>.srt).",
        ),
    ] = None,
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="Whisperfile model alias to use.",
        ),
    ] = get_default_model(),
    threads: Annotated[
        int,
        typer.Option(
            "--threads",
            "-t",
            help="Number of threads for whisperfile.",
        ),
    ] = DEFAULT_THREADS,
    gpu: Annotated[
        str | None,
        typer.Option(
            "--gpu",
            help="Enable GPU acceleration (nvidia, metal, amd).",
        ),
    ] = None,
) -> None:
    """Transcribe a video and save subtitles as SRT."""
    try:
        output_srt = output or _resolve_output(video, ".srt")
        srt_path = transcribe_video(
            video,
            model,
            output_srt=output_srt,
            language="en",
            threads=threads,
            gpu=gpu,
        )
        log_success(f"Subtitles saved to '{srt_path}'")
    except (RuntimeError, UnknownModelError) as exc:
        log_error(str(exc))
        raise typer.Exit(code=1) from exc


@app.command()
def burn(
    video: Annotated[Path, typer.Argument(help="Input video file.", exists=True, readable=True)],
    srt: Annotated[
        Path | None,
        typer.Option(
            "--srt",
            "-s",
            help="Optional SRT file. If omitted, transcription is run automatically.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output video file (default: <video>-sub.mp4).",
        ),
    ] = None,
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="Whisperfile model alias (used when --srt is not provided).",
        ),
    ] = get_default_model(),
    threads: Annotated[int, typer.Option("--threads", "-t", help="Number of threads.")] = DEFAULT_THREADS,
    gpu: Annotated[
        str | None,
        typer.Option("--gpu", help="Enable GPU acceleration (nvidia, metal, amd)."),
    ] = None,
    font_size: Annotated[
        int,
        typer.Option("--font-size", help="Subtitle font size."),
    ] = DEFAULT_FONT_SIZE,
    font_color: Annotated[
        str,
        typer.Option("--font-color", help="Subtitle font color."),
    ] = DEFAULT_FONT_COLOR,
    box_color: Annotated[
        str,
        typer.Option("--box-color", help="Subtitle background box color."),
    ] = DEFAULT_BOX_COLOR,
    position: Annotated[
        str,
        typer.Option("--position", help="Subtitle vertical position (bottom or top)."),
    ] = DEFAULT_POSITION,
) -> None:
    """Burn subtitles into a video, generating them automatically if needed."""
    try:
        output_video = output or _resolve_output(video, "-sub.mp4")
        generated_srt = srt is None

        if generated_srt:
            srt = _resolve_output(video, ".srt")
            transcribe_video(
                video,
                model,
                output_srt=srt,
                language="en",
                threads=threads,
                gpu=gpu,
            )
            log_info(f"Generated subtitles: {srt}")

        burn_pipeline(
            video,
            output_video,
            srt,
            font_size=font_size,
            font_color=font_color,
            box_color=box_color,
            position=position,
        )
        log_success(f"Subtitled video saved to '{output_video}'")
    except (RuntimeError, UnknownModelError, ValueError) as exc:
        log_error(str(exc))
        raise typer.Exit(code=1) from exc


@app.command()
def convert(
    video: Annotated[Path, typer.Argument(help="Input video file.", exists=True, readable=True)],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output MP4 file (default: <video>.mp4)."),
    ] = None,
) -> None:
    """Convert a video to MP4."""
    try:
        output_video = output or _resolve_output(video, ".mp4")
        convert_to_mp4(video, output_video)
        log_success(f"Converted video saved to '{output_video}'")
    except RuntimeError as exc:
        log_error(str(exc))
        raise typer.Exit(code=1) from exc


@app.command()
def preview(
    video: Annotated[Path, typer.Argument(help="Input video file.", exists=True, readable=True)],
    srt: Annotated[
        Path | None,
        typer.Option("--srt", "-s", help="Optional SRT file."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output preview file (default: <video>-test.mp4)."),
    ] = None,
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Whisperfile model alias."),
    ] = get_default_model(),
    duration: Annotated[
        int,
        typer.Option("--duration", "-d", help="Preview duration in seconds."),
    ] = DEFAULT_PREVIEW_DURATION,
    threads: Annotated[int, typer.Option("--threads", "-t", help="Number of threads.")] = DEFAULT_THREADS,
    gpu: Annotated[
        str | None,
        typer.Option("--gpu", help="Enable GPU acceleration (nvidia, metal, amd)."),
    ] = None,
    font_size: Annotated[int, typer.Option("--font-size", help="Subtitle font size.")] = DEFAULT_FONT_SIZE,
    font_color: Annotated[
        str,
        typer.Option("--font-color", help="Subtitle font color."),
    ] = DEFAULT_FONT_COLOR,
    box_color: Annotated[
        str,
        typer.Option("--box-color", help="Subtitle background box color."),
    ] = DEFAULT_BOX_COLOR,
    position: Annotated[
        str,
        typer.Option("--position", help="Subtitle vertical position."),
    ] = DEFAULT_POSITION,
) -> None:
    """Generate a short preview with burned subtitles."""
    try:
        output_video = output or _resolve_output(video, "-test.mp4")
        generated_srt = srt is None

        if generated_srt:
            srt = _resolve_output(video, ".srt")
            transcribe_video(
                video,
                model,
                output_srt=srt,
                language="en",
                threads=threads,
                gpu=gpu,
            )
            log_info(f"Generated subtitles: {srt}")

        generate_preview(
            video,
            output_video,
            srt,
            duration,
            font_size=font_size,
            font_color=font_color,
            box_color=box_color,
            position=position,
        )
        log_success(f"Preview saved to '{output_video}'")
    except (RuntimeError, UnknownModelError, ValueError) as exc:
        log_error(str(exc))
        raise typer.Exit(code=1) from exc


@models_app.command("list")
def models_list() -> None:
    """List supported models and their local download status."""
    models = list_models()
    log_info("Supported models (* = downloaded):")
    for alias in sorted(models):
        status = "*" if models[alias] else " "
        print(f"  [{status}] {alias:<12} -> {resolve_model(alias)}")


@models_app.command("download")
def models_download(
    alias: Annotated[str, typer.Argument(help="Model alias to download.")],
) -> None:
    """Download a whisperfile model."""
    try:
        path = download_model(alias)
        log_success(f"Model ready at {path}")
    except UnknownModelError as exc:
        log_error(str(exc))
        raise typer.Exit(code=1) from exc


@models_app.command("default")
def models_default(
    alias: Annotated[str | None, typer.Argument(help="Model alias to set as default.")] = None,
) -> None:
    """Show or set the default model alias."""
    if alias is None:
        log_info(f"Default model: {get_default_model()}")
        return

    try:
        resolve_model(alias)
    except UnknownModelError as exc:
        log_error(str(exc))
        raise typer.Exit(code=1) from exc

    # Persist default to a small config file in the model directory.
    from suburn.config import get_model_dir

    config_path = get_model_dir() / ".default"
    config_path.write_text(alias, encoding="utf-8")
    log_success(f"Default model set to '{alias}'")


@app.callback(invoke_without_command=True)
def main(version: Annotated[bool, typer.Option("--version", "-v")] = False) -> None:
    """Suburn CLI entry point."""
    if version:
        print(f"suburn {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
