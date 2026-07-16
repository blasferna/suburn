"""Shared utilities for logging and subprocess execution."""

import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()


def log_info(message: str) -> None:
    console.print(f"[blue]INFO[/blue] {message}")


def log_warn(message: str) -> None:
    console.print(f"[yellow]WARN[/yellow] {message}")


def log_error(message: str) -> None:
    console.print(f"[red]ERROR[/red] {message}")


def log_success(message: str) -> None:
    console.print(f"[green]OK[/green] {message}")


def require_command(name: str) -> str:
    """Ensure an external command is available and return its path."""
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"'{name}' is not installed or not in PATH")
    return path


def run_command(
    cmd: Iterable[str | Path],
    *,
    check: bool = True,
    capture_output: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run an external command with consistent error handling."""
    str_cmd = [str(arg) for arg in cmd]
    try:
        return subprocess.run(
            str_cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        stdout = exc.stdout.strip() if exc.stdout else ""
        detail = stderr or stdout or "no output captured"
        raise RuntimeError(f"Command failed: {' '.join(str_cmd)}\n{detail}") from exc


def download_progress() -> Progress:
    """Return a Rich progress bar suitable for file downloads."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        DownloadColumn(binary_units=True),
        "•",
            TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
    )
