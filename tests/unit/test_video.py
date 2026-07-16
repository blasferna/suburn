"""Tests for video burning helpers."""

from pathlib import Path

from suburn.video import _ass_color, _ass_time, _build_ass_filter, _quote_filter_value


def test_ass_color_white():
    assert _ass_color("white") == "&H00FFFFFF"


def test_ass_color_grey():
    assert _ass_color("grey") == "&H00808080"
    assert _ass_color("gray") == "&H00808080"


def test_ass_color_hex():
    assert _ass_color("#FF0000") == "&H000000FF"
    assert _ass_color("#00FF00") == "&H0000FF00"
    assert _ass_color("#0000FF") == "&H00FF0000"


def test_ass_color_passthrough():
    assert _ass_color("&HFF123456") == "&HFF123456"


def test_ass_color_unknown_defaults_white():
    assert _ass_color("notacolor") == "&H00FFFFFF"


def test_ass_time():
    assert _ass_time(0) == "0:00:00.00"
    assert _ass_time(3661.53) == "1:01:01.53"
    assert _ass_time(5.5) == "0:00:05.50"


def test_quote_filter_value_simple():
    assert _quote_filter_value("foo") == "'foo'"


def test_quote_filter_value_with_apostrophe():
    assert _quote_filter_value("it's") == "'it\\'s'"


def test_build_ass_filter():
    ass = Path("/tmp/subtitles.ass")
    filter_str = _build_ass_filter(ass)
    assert filter_str == "ass='/tmp/subtitles.ass'"


def test_build_ass_filter_escapes_path():
    ass = Path("/tmp/my subtitles.ass")
    filter_str = _build_ass_filter(ass)
    assert filter_str == "ass='/tmp/my subtitles.ass'"
