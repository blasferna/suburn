"""Configuration and constants for suburn."""

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "suburn"
APP_AUTHOR = "suburn"

WHISPERFILE_BASE_URL = (
    "https://huggingface.co/Mozilla/whisperfile/resolve/main/{model}?download=true"
)

MODEL_ALIASES = {
    "tiny.en": "whisper-tiny.en.llamafile",
    "tiny": "whisper-tiny.llamafile",
    "small.en": "whisper-small.en.llamafile",
    "small": "whisper-small.llamafile",
    "medium.en": "whisper-medium.en.llamafile",
    "medium": "whisper-medium.llamafile",
    "large-v2": "whisper-large-v2.llamafile",
    "large-v3": "whisper-large-v3.llamafile",
}

DEFAULT_MODEL_ALIAS = "small.en"
TEST_MODEL_ALIAS = "tiny.en"

DEFAULT_THREADS = 4
DEFAULT_FONT_SIZE = 22
DEFAULT_FONT_COLOR = "white"
DEFAULT_BOX_COLOR = "&H10333333"  # dark grey, ~94% opaque
DEFAULT_POSITION = "bottom"
DEFAULT_PREVIEW_DURATION = 10
DEFAULT_MAX_LINE_LENGTH = 35


def get_model_dir() -> Path:
    """Return the directory where whisperfile models are stored."""
    if env_dir := os.environ.get("SUBURN_MODEL_DIR"):
        return Path(env_dir).expanduser().resolve()
    return Path(user_data_dir(APP_NAME, APP_AUTHOR)) / "models"


def get_cache_dir() -> Path:
    """Return the general application cache directory."""
    if env_dir := os.environ.get("SUBURN_CACHE_DIR"):
        return Path(env_dir).expanduser().resolve()
    return Path(user_data_dir(APP_NAME, APP_AUTHOR)) / "cache"
