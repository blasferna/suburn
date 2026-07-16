"""Tests for model alias resolution and URL generation."""

import pytest

from suburn.models import UnknownModelError, model_url, resolve_model


def test_resolve_alias():
    assert resolve_model("tiny.en") == "whisper-tiny.en.llamafile"
    assert resolve_model("small") == "whisper-small.llamafile"
    assert resolve_model("large-v3") == "whisper-large-v3.llamafile"


def test_resolve_filename():
    assert resolve_model("whisper-small.en.llamafile") == "whisper-small.en.llamafile"


def test_resolve_unknown():
    with pytest.raises(UnknownModelError):
        resolve_model("not-a-model")


def test_model_url():
    url = model_url("whisper-tiny.en.llamafile")
    assert "Mozilla/whisperfile/resolve/main/whisper-tiny.en.llamafile" in url
    assert "download=true" in url
