"""Tests for SRT parsing."""

from suburn.subtitles import SubtitleEntry, parse_srt


SAMPLE_SRT = """1
00:00:01,600 --> 00:00:04,820
Hello world

2
00:00:05,000 --> 00:00:07,500
It's a test

3
00:00:08,000 --> 00:00:09,000


4
00:00:10,000 --> 00:00:12,000
Final line
"""


def test_parse_srt(tmp_path):
    srt_path = tmp_path / "sample.srt"
    srt_path.write_text(SAMPLE_SRT, encoding="utf-8")

    entries = parse_srt(srt_path)
    assert len(entries) == 3

    assert entries[0] == SubtitleEntry(start=1.6, end=4.82, text="Hello world")
    assert entries[1] == SubtitleEntry(start=5.0, end=7.5, text="It's a test")
    assert entries[2] == SubtitleEntry(start=10.0, end=12.0, text="Final line")


def test_parse_srt_preserves_line_breaks(tmp_path):
    srt_path = tmp_path / "sample.srt"
    srt_path.write_text(
        "1\n00:00:01,000 --> 00:00:02,000\nFirst line\nSecond line\n",
        encoding="utf-8",
    )

    entries = parse_srt(srt_path)
    assert entries[0].text == "First line\nSecond line"


def test_empty_srt(tmp_path):
    srt_path = tmp_path / "empty.srt"
    srt_path.write_text("", encoding="utf-8")
    entries = parse_srt(srt_path)
    assert entries == []


def test_apostrophe_preserved(tmp_path):
    srt_path = tmp_path / "sample.srt"
    srt_path.write_text(
        "1\n00:00:01,000 --> 00:00:02,000\nIt's working\n",
        encoding="utf-8",
    )

    entries = parse_srt(srt_path)
    assert entries[0].text == "It's working"
