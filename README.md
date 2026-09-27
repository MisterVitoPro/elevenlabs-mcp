# ElevenLabs MCP Server

![Version](https://img.shields.io/badge/dynamic/toml?url=https://raw.githubusercontent.com/MisterVitoPro/elevenlabs-mcp/main/pyproject.toml&query=$.project.version&label=version&color=blue)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/MisterVitoPro/elevenlabs-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/MisterVitoPro/elevenlabs-mcp)
[![Tests](https://github.com/MisterVitoPro/elevenlabs-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/MisterVitoPro/elevenlabs-mcp/actions/workflows/tests.yml)
[![CodeQL](https://github.com/MisterVitoPro/elevenlabs-mcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/MisterVitoPro/elevenlabs-mcp/actions/workflows/codeql.yml)

An [MCP](https://modelcontextprotocol.io/) server that provides AI assistants with access to [ElevenLabs](https://elevenlabs.io/) audio capabilities -- text-to-speech, voice conversion, sound effects, transcription, and more.

## Features

- **Text-to-Speech** -- Convert text to natural-sounding speech with 30+ voices
- **Sound Effects** -- Generate sound effects from text descriptions
- **Music Generation** -- Compose full music tracks from a text prompt
- **Speech-to-Speech** -- Convert speech audio to a different voice
- **Multi-Speaker Dialogue** -- Generate dialogue with multiple voices from a script
- **Audio Isolation** -- Remove background noise from audio files
- **Speech-to-Text** -- Transcribe audio files using Scribe v2
- **Voice & Model Discovery** -- Browse available voices and models
- **Usage Tracking** -- Monitor API character usage and quotas

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- [ElevenLabs API key](https://elevenlabs.io/app/settings/api-keys)

## Installation

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management. Install it first if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then clone and sync the project:

```bash
git clone https://github.com/MisterVitoPro/elevenlabs-mcp.git
cd elevenlabs-mcp
uv sync
```

## Configuration

Set your ElevenLabs API key:

```bash
export ELEVENLABS_API_KEY=sk_your-key-here
```

> **Use the secret key, not the key ID.** The [API keys dashboard](https://elevenlabs.io/app/settings/api-keys)
> lists keys by ID. The secret key starts with `sk_` and is shown only once, when the
> key is created or rotated. Passing the ID fails every request with
> `API key ID used as API key`.

Optionally set a custom output directory (defaults to `~/elevenlabs-output/`):

```bash
export ELEVENLABS_OUTPUT_DIR=/path/to/output
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ELEVENLABS_API_KEY` | *required* | Secret API key, starting with `sk_` |
| `ELEVENLABS_API_KEY_ID` | unset | ID of the key above, for your own reference. Never used to authenticate; echoed by `get_usage` as `api_key_id` |
| `ELEVENLABS_OUTPUT_DIR` | `~/elevenlabs-output` | Where generated audio is written. Tools refuse to write outside it |
| `ELEVENLABS_INPUT_DIR` | `~/elevenlabs-input` | Where tools read source audio from. Tools refuse to read outside it |
| `ELEVENLABS_TIMEOUT` | `120` | HTTP timeout in seconds |
| `MAX_TTS_CHARS` | `5000` | Client-side cap on `text_to_speech` input length |
| `ELEVENLABS_MODEL_ALLOWLIST` | unset | Comma-separated model IDs; requests for anything else are rejected |

Since the dashboard identifies keys by ID rather than name, recording
`ELEVENLABS_API_KEY_ID` alongside the key makes it easy to tell later which key a
given config is using. See `.env.example`.

## MCP Integration

### Claude Code

Add to your MCP settings (`~/.claude/settings.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "elevenlabs": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/elevenlabs-mcp", "python", "-m", "elevenlabs_mcp.server"],
      "env": {
        "ELEVENLABS_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "elevenlabs": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/elevenlabs-mcp", "python", "-m", "elevenlabs_mcp.server"],
      "env": {
        "ELEVENLABS_API_KEY": "your-key-here"
      }
    }
  }
}
```

## Tools

### Audio Generation

#### `text_to_speech`

Convert text to speech audio.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | *required* | Text to convert |
| `voice` | string | `"George"` | Voice name or ID |
| `model` | string | `"eleven_multilingual_v2"` | Model ID (`eleven_v3` for expressiveness, `eleven_flash_v2_5` for low latency) |
| `output_format` | string | `"mp3_44100_128"` | Audio format |
| `output_path` | string | auto-generated | File path to save audio |

#### `sound_effect`

Generate a sound effect from a text description.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | *required* | Description of the desired sound |
| `duration` | float | auto | Duration in seconds (0.5--30) |
| `output_path` | string | auto-generated | File path to save audio |

#### `compose_music`

Generate a music track from a text description.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | *required* | Description of the music (genre, mood, instrumentation) |
| `length_seconds` | float | auto | Track length in seconds (3--600) |
| `model` | string | `"music_v2_5"` | Music model ID |
| `output_format` | string | `"mp3_44100_128"` | Audio format |
| `force_instrumental` | bool | `false` | Guarantee the track has no vocals |
| `output_path` | string | auto-generated | File path to save audio |

#### `speech_to_speech`

Convert speech in an audio file to a different voice.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_path` | string | *required* | Path to input audio file |
| `voice` | string | `"George"` | Target voice name or ID |
| `model` | string | `"eleven_multilingual_sts_v2"` | Model ID (use `eleven_english_sts_v2` for English-only) |
| `output_path` | string | auto-generated | File path to save audio |

#### `text_to_dialogue`

Generate multi-speaker dialogue audio from a script.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dialogue` | list[dict] | *required* | List of `{"voice": "...", "text": "..."}` turns |
| `output_path` | string | auto-generated | File path to save audio |

### Audio Processing

#### `audio_isolation`

Remove background noise from an audio file, isolating the voice.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_path` | string | *required* | Path to input audio file |
| `output_path` | string | auto-generated | File path to save audio |

#### `speech_to_text`

Transcribe an audio file to text using Scribe v2.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_path` | string | *required* | Path to input audio file |

Returns the transcription text directly.

### Discovery & Usage

#### `list_voices`

List all available ElevenLabs voices. Returns JSON with voice ID, name, category, description, and labels.

#### `get_voice`

Get details for a specific voice. Returns JSON with full voice details including settings and preview URL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voice` | string | *required* | Voice name or ID |

#### `list_models`

List all available ElevenLabs models. Returns JSON with model ID, name, description, and capabilities.

#### `get_usage`

Get current API usage and quota information. Returns JSON with tier, character count, limit, remaining, and reset time.

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

### Project Structure

```
elevenlabs-mcp/
  src/elevenlabs_mcp/
    __init__.py
    server.py        # MCP server with all tools
  tests/
    test_server.py   # Unit tests
  pyproject.toml
```

## License

[MIT](LICENSE)
