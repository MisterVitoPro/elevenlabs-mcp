# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/MisterVitoPro/elevenlabs-mcp/releases/tag/v1.0.0
