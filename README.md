# ElevenLabs MCP Server

MCP server for ElevenLabs text-to-speech and sound effect generation.

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
cd elevenlabs-mcp
uv sync
```

## Configuration

Set your ElevenLabs API key as an environment variable:

```bash
export ELEVENLABS_API_KEY=your-key-here
```

Optionally set a custom output directory (defaults to `~/elevenlabs-output/`):

```bash
export ELEVENLABS_OUTPUT_DIR=/path/to/output
```

## Claude Code Integration

Add to your MCP settings:

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

### text_to_speech

Convert text to speech audio.

- `text` (required): Text to convert
- `voice`: Voice ID or name (default: "Rachel")
- `model`: Model ID (default: "eleven_multilingual_v2")
- `output_format`: Audio format (default: "mp3_44100_128")
- `output_path`: Custom save location

### sound_effect

Generate a sound effect from a text prompt.

- `prompt` (required): Description of the desired sound
- `duration`: Duration in seconds (0.5-30)
- `output_path`: Custom save location
