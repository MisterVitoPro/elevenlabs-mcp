# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-14

### Added

- `compose_music` tool -- generate a music track from a text prompt, with optional length, instrumental-only mode, and output format
- Optional `ELEVENLABS_API_KEY_ID` environment variable to record which API key a config uses. Informational only, never used to authenticate; `get_usage` echoes it as `api_key_id`
- Document every environment variable in the README, including a warning that the API key must be the `sk_` secret and not the key ID shown in the dashboard

### Changed

- Upgrade `elevenlabs` SDK from 2.42.0 to 2.68.0, which adds the `music_v2` and `music_v2_5` model IDs
- `speech_to_speech` now defaults to `eleven_multilingual_sts_v2` instead of `eleven_english_sts_v2`, matching the current ElevenLabs recommendation. Pass `model="eleven_english_sts_v2"` to keep the previous behavior.
- Document `eleven_v3` and `eleven_flash_v2_5` as `text_to_speech` model options. The default stays `eleven_multilingual_v2`.

## [1.1.1] - 2026-04-15

### Fixed

- Add `if __name__ == "__main__": main()` guard to `server.py` so the server starts correctly when invoked via `python -m elevenlabs_mcp.server`
- Update MCP config examples in README to use `python -m` invocation, avoiding Windows file-lock errors on the `elevenlabs-mcp.exe` entry point script

## [1.1.0] - 2026-04-15

### Security

- Contain `resolve_output_path` and `validate_audio_path` within `ELEVENLABS_OUTPUT_DIR` / `ELEVENLABS_INPUT_DIR` (defaults `~/elevenlabs-output`, `~/elevenlabs-input`)
- Sanitize voice names in `generate_filename` so they cannot introduce path separators or traversal sequences
- Add an HTTP timeout via `ELEVENLABS_TIMEOUT` (default 120s)
- Pin dependency upper bounds (`elevenlabs <3.0.0`, `fastmcp <4.0.0`)
- Mask the API key in `get_client` error paths

### Fixed

- `generate_filename` derives its extension from `output_format` and adds microseconds plus a uuid suffix to prevent same-second collisions
- `text_to_dialogue` validates the shape of each turn and fetches the voice list once instead of once per turn
- `resolve_voice_id` raises on ambiguous name matches instead of silently taking the first
- `get_usage` guards a `None` subscription and `None` character fields
- `save_audio` writes atomically via a `.tmp` file and `Path.replace`

### Added

- `MAX_TTS_CHARS` cap on `text_to_speech` (default 5000), enforced client-side
- `model` and optional `output_path` parameters on `speech_to_text`
- Module-level client singleton and a 5-minute voice catalog cache
- Optional `ELEVENLABS_MODEL_ALLOWLIST` for client-side model validation
- Fail-fast startup validation of `ELEVENLABS_API_KEY`

## [1.0.0] - 2026-04-12

### Added

- `text_to_speech` tool -- convert text to speech with configurable voice, model, and output format
- `sound_effect` tool -- generate sound effects from text descriptions
- `list_voices` tool -- list all available ElevenLabs voices
- `get_voice` tool -- get details for a specific voice
- `speech_to_speech` tool -- convert speech audio to a different voice
- `text_to_dialogue` tool -- generate multi-speaker dialogue from a script
- `audio_isolation` tool -- remove background noise from audio files
- `speech_to_text` tool -- transcribe audio files using Scribe v2
- `list_models` tool -- list available models and capabilities
- `get_usage` tool -- check API character usage and quotas
- Voice name resolution -- use voice names instead of IDs across all tools
- Configurable output directory via `ELEVENLABS_OUTPUT_DIR` environment variable

[1.2.0]: https://github.com/MisterVitoPro/elevenlabs-mcp/releases/tag/v1.2.0
[1.1.1]: https://github.com/MisterVitoPro/elevenlabs-mcp/releases/tag/v1.1.1
[1.1.0]: https://github.com/MisterVitoPro/elevenlabs-mcp/releases/tag/v1.1.0
[1.0.0]: https://github.com/MisterVitoPro/elevenlabs-mcp/releases/tag/v1.0.0
