# suburn

A CLI for transcribing videos and burning subtitles into MP4 with ffmpeg.

## Requirements

- Python >= 3.11
- [ffmpeg](https://ffmpeg.org/) built with `--enable-libass`
- [uv](https://docs.astral.sh/uv/) (recommended)

## Installation

Install directly from the repository with `uv`:

```bash
uv tool install git+https://github.com/blasferna/suburn.git
```

This installs the `suburn` command globally.

## Usage

### Transcribe a video

```bash
suburn transcribe video.mkv
```

Generates `video.srt` using the default `small.en` whisperfile model.

### Burn subtitles into a video

```bash
suburn burn video.mkv
```

Creates `video-sub.mp4` with auto-generated subtitles.

Use your own SRT file:

```bash
suburn burn video.mkv -s subtitles.srt
```

### Generate a short preview

```bash
suburn preview video.mkv -s subtitles.srt --duration 10
```

Creates a 10-second preview with burned subtitles.

### Manage whisperfile models

```bash
suburn models list
suburn models download tiny.en
suburn models default tiny.en
```

## Styling

Default subtitle style is Netflix-like: white text on a semi-transparent dark grey box at the bottom.

You can customize it:

```bash
suburn burn video.mkv \
  --font-size 24 \
  --font-color white \
  --box-color "#333333" \
  --position bottom
```

For a fully opaque background, use an ASS alpha value of `00`:

```bash
suburn burn video.mkv --box-color "&H00333333"
```

## Notes

- When you provide an SRT with `-s`, it is never modified or deleted.
- Auto-generated SRT files are kept next to the input video by default.

## Development

Clone the repository and run the tests:

```bash
uv run pytest
```

Run slow end-to-end tests with:

```bash
uv run pytest -m slow
```

## License

MIT
