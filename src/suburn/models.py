"""Model download and resolution for whisperfile."""

import os
import stat
import urllib.request
from pathlib import Path

from suburn.config import (
    DEFAULT_MODEL_ALIAS,
    MODEL_ALIASES,
    WHISPERFILE_BASE_URL,
    get_model_dir,
)
from suburn.utils import download_progress, log_info, log_success, log_warn


class UnknownModelError(ValueError):
    """Raised when a requested model alias or filename is not supported."""


def resolve_model(name_or_alias: str) -> str:
    """Resolve a model alias or filename to a supported whisperfile name."""
    name = name_or_alias.strip()
    if name in MODEL_ALIASES:
        return MODEL_ALIASES[name]
    if name in MODEL_ALIASES.values():
        return name
    raise UnknownModelError(
        f"Unknown model '{name}'. Supported aliases: {', '.join(sorted(MODEL_ALIASES))}"
    )


def list_models() -> dict[str, Path | None]:
    """Return a mapping of model aliases to their local paths (or None)."""
    model_dir = get_model_dir()
    local_files = {p.name: p for p in model_dir.glob("*.llamafile") if p.is_file()}
    return {alias: local_files.get(filename) for alias, filename in MODEL_ALIASES.items()}


def model_url(filename: str) -> str:
    """Build the HuggingFace download URL for a whisperfile model."""
    return WHISPERFILE_BASE_URL.format(model=filename)


def model_path(filename: str) -> Path:
    """Return the local path where a model would be stored."""
    return get_model_dir() / filename


def ensure_model(name_or_alias: str) -> Path:
    """Ensure a model exists locally, downloading it if necessary."""
    filename = resolve_model(name_or_alias)
    path = model_path(filename)

    if path.exists():
        if not os.access(path, os.X_OK):
            log_warn(f"Model exists but is not executable: {path}")
            _make_executable(path)
        return path

    return download_model(filename)


def download_model(name_or_alias: str) -> Path:
    """Download a whisperfile model from HuggingFace."""
    filename = resolve_model(name_or_alias)
    path = model_path(filename)
    url = model_url(filename)

    path.parent.mkdir(parents=True, exist_ok=True)
    log_info(f"Downloading model '{filename}' from HuggingFace...")

    with download_progress() as progress:
        task = progress.add_task(filename, total=None)

        def reporthook(block_num: int, block_size: int, total_size: int) -> None:
            downloaded = block_num * block_size
            if total_size > 0:
                progress.update(task, total=total_size, completed=downloaded)

        urllib.request.urlretrieve(url, path, reporthook=reporthook)

    _make_executable(path)
    log_success(f"Model saved to {path}")
    return path


def _make_executable(path: Path) -> None:
    """Add execute permission to a whisperfile binary."""
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def get_default_model() -> str:
    """Return the configured default model alias.

    The user can override the built-in default by writing an alias to
    ``<model_dir>/.default`` via ``suburn models default <alias>``.
    """
    override = get_model_dir() / ".default"
    if override.exists():
        alias = override.read_text(encoding="utf-8").strip()
        if alias in MODEL_ALIASES:
            return alias
    return DEFAULT_MODEL_ALIAS
