# ElevenLabs MCP Server -- Expand Tools

**Date:** 2026-04-12
**Status:** Proposed

## Summary

Add 8 new MCP tools to the ElevenLabs MCP server, bringing the total from 2 to 10. The goal is a full-featured wrapper exposing the most useful ElevenLabs API capabilities as MCP tools.

## Existing Tools

1. **`text_to_speech`** -- Convert text to speech audio with voice/model selection.
2. **`sound_effect`** -- Generate a sound effect from a text description.

## New Tools

### Group 1: Voice Management

#### `list_voices`
- **Purpose:** Return all available voices so users can discover voice names/IDs before calling text_to_speech.
- **Parameters:** None.
- **Returns:** JSON list of voices, each with: `voice_id`, `name`, `category`, `description`, `labels`.
- **SDK method:** `client.voices.get_all()`

#### `get_voice`
- **Purpose:** Get full details for a specific voice.
- **Parameters:**
  - `voice` (str, required) -- Voice name or ID. Uses existing `resolve_voice_id` helper.
- **Returns:** JSON object with voice details: `voice_id`, `name`, `category`, `description`, `labels`, `settings`, `preview_url`.
- **SDK method:** `client.voices.get(voice_id)`

### Group 2: Audio Generation

#### `speech_to_speech`
- **Purpose:** Convert an audio file's speech into a different voice.
- **Parameters:**
  - `audio_path` (str, required) -- Path to input audio file.
  - `voice` (str, default "George") -- Target voice name or ID.
  - `model` (str, default "eleven_english_sts_v2") -- Model ID.
  - `output_path` (str | None, default None) -- Optional output file path.
- **Returns:** Path to the saved output audio file.
- **SDK method:** `client.speech_to_speech.convert(voice_id, audio=file, model_id=model)`

#### `text_to_dialogue`
- **Purpose:** Generate multi-speaker dialogue from a script.
- **Parameters:**
  - `dialogue` (list[dict], required) -- List of turns, each with `voice` (str) and `text` (str).
  - `output_path` (str | None, default None) -- Optional output file path.
- **Returns:** Path to the saved output audio file.
- **SDK method:** `client.text_to_dialogue.convert(inputs=[DialogueInput(text=..., voice_id=...)])`
- **Note:** Each dialogue turn's voice name is resolved to an ID via `resolve_voice_id`.

#### `audio_isolation`
- **Purpose:** Remove background noise from an audio file, isolating the voice.
- **Parameters:**
  - `audio_path` (str, required) -- Path to input audio file.
  - `output_path` (str | None, default None) -- Optional output file path.
- **Returns:** Path to the saved output audio file.
- **SDK method:** `client.audio_isolation.convert(audio=file)`

### Group 3: Transcription

#### `speech_to_text`
- **Purpose:** Transcribe an audio file to text.
- **Parameters:**
  - `audio_path` (str, required) -- Path to input audio file.
- **Returns:** Transcript text string.
- **SDK method:** `client.speech_to_text.convert(audio=file)`

### Group 4: Account & Models

#### `list_models`
- **Purpose:** Return available ElevenLabs models so users know valid model IDs.
- **Parameters:** None.
- **Returns:** JSON list of models, each with: `model_id`, `name`, `description`, `can_do_text_to_speech`, `can_do_voice_conversion`.
- **SDK method:** `client.models.list()`

#### `get_usage`
- **Purpose:** Return current API usage and quota info.
- **Parameters:** None.
- **Returns:** JSON object with usage details: `character_count`, `character_limit`, `next_reset_unix`.
- **SDK method:** `client.user.get()` then extract subscription usage fields.

## Design Decisions

### Audio file inputs
Tools that accept audio files take a local file path string. No URL support -- keeps it simple. Can be added later.

### Voice resolution
All tools that accept a `voice` parameter reuse the existing `resolve_voice_id` helper, which accepts either a voice name or ID.

### Output file handling
All audio-producing tools reuse the existing `resolve_output_path` and `save_audio` helpers. Output files default to `ELEVENLABS_OUTPUT_DIR` with timestamped filenames.

### Return values
- Audio-producing tools return the output file path as a string.
- Query tools (list_voices, get_voice, list_models, get_usage) return structured data as JSON strings.
- speech_to_text returns the transcript as a plain string.

### What's excluded (and why)
- **Dubbing** -- Multi-step async workflow (create, poll, download). Doesn't map to a single tool call cleanly.
- **Music generation** -- Complex parameters, long generation times, better suited for a dedicated workflow.
- **Conversational AI** -- Stateful agent management, not a good fit for stateless tool calls.
- **Studio/Podcasts** -- Project-based workflows with multiple steps.
- **History** -- Low value as an MCP tool; users can check the ElevenLabs dashboard.
- **Pronunciation dictionaries** -- Niche, can be added later if needed.

## File Structure

All new tools go in `src/elevenlabs_mcp/server.py` alongside the existing tools. The file is small enough that splitting isn't warranted yet.

## Error Handling

All tools follow the existing pattern: let SDK exceptions propagate naturally. The `get_client()` helper already validates the API key. The `resolve_voice_id` helper already provides a clear error with available voices when a voice isn't found.

For file-input tools, validate that the file exists before calling the SDK, raising a `ValueError` with a clear message if not.
