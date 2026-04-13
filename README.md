# ElevenLabs MCP Server

An [MCP](https://modelcontextprotocol.io/) server that provides AI assistants with access to [ElevenLabs](https://elevenlabs.io/) audio capabilities -- text-to-speech, voice conversion, sound effects, transcription, and more.

## Features

- **Text-to-Speech** -- Convert text to natural-sounding speech with 30+ voices
- **Sound Effects** -- Generate sound effects from text descriptions
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

```bash
git clone https://github.com/MisterVitoPro/elevenlabs-mcp.git
cd elevenlabs-mcp
uv sync
```

## Configuration

Set your ElevenLabs API key:

```bash
export ELEVENLABS_API_KEY=your-key-here
```

Optionally set a custom output directory (defaults to `~/elevenlabs-output/`):

```bash
export ELEVENLABS_OUTPUT_DIR=/path/to/output
```

## MCP Integration

### Claude Code

Add to your MCP settings (`~/.claude/settings.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "elevenlabs": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/elevenlabs-mcp", "elevenlabs-mcp"],
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
      "args": ["run", "--directory", "/path/to/elevenlabs-mcp", "elevenlabs-mcp"],
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
| `model` | string | `"eleven_multilingual_v2"` | Model ID |
| `output_format` | string | `"mp3_44100_128"` | Audio format |
| `output_path` | string | auto-generated | File path to save audio |

#### `sound_effect`

Generate a sound effect from a text description.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | *required* | Description of the desired sound |
| `duration` | float | auto | Duration in seconds (0.5--30) |
| `output_path` | string | auto-generated | File path to save audio |

#### `speech_to_speech`

Convert speech in an audio file to a different voice.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_path` | string | *required* | Path to input audio file |
| `voice` | string | `"George"` | Target voice name or ID |
| `model` | string | `"eleven_english_sts_v2"` | Model ID |
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
