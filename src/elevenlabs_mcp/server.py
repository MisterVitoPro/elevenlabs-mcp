import httpx
import json
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP
from elevenlabs.client import ElevenLabs
from elevenlabs import DialogueInput

mcp = FastMCP("ElevenLabs")

_client: "tuple[tuple, ElevenLabs] | None" = None

_voices_cache: "dict[int, tuple[float, object]]" = {}
_VOICES_TTL = 300.0


def get_output_dir() -> Path:
    return Path(os.environ.get("ELEVENLABS_OUTPUT_DIR", str(Path.home() / "elevenlabs-output")))


def get_input_dir() -> Path:
    return Path(os.environ.get("ELEVENLABS_INPUT_DIR", str(Path.home() / "elevenlabs-input")))


def _ext_from_format(output_format: str) -> str:
    prefix = output_format.split("_")[0].lower()
    known = {"mp3", "pcm", "ulaw", "opus", "aac"}
    return prefix if prefix in known else "mp3"


def generate_filename(label: str, kind: str, output_format: str = "mp3_44100_128") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_label = re.sub(r"[^\w\-]", "_", label)[:64]
    ext = _ext_from_format(output_format)
    suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}_{kind}_{safe_label}_{suffix}.{ext}"


def resolve_output_path(
    output_path: str | None,
    label: str,
    kind: str,
    output_format: str = "mp3_44100_128",
) -> Path:
    if output_path is not None and output_path.strip() == "":
        raise ValueError("output_path must not be empty.")
    output_dir = get_output_dir().resolve()
    if output_path:
        resolved = Path(output_path).resolve()
        try:
            resolved.relative_to(output_dir)
        except ValueError:
            raise ValueError(
                f"output_path '{output_path}' must be inside the configured output "
                f"directory '{output_dir}'."
            )
        return resolved
    return output_dir / generate_filename(label, kind, output_format)


def validate_audio_path(audio_path: str) -> Path:
    input_dir = get_input_dir().resolve()
    path = Path(audio_path).resolve()
    try:
        path.relative_to(input_dir)
    except ValueError:
        raise ValueError(
            f"Audio path '{audio_path}' must be inside the configured input "
            f"directory '{input_dir}'."
        )
    if not path.is_file():
        raise ValueError(f"Audio file not found: {audio_path}")
    return path


def _validate_model(model: str) -> None:
    allowlist = os.environ.get("ELEVENLABS_MODEL_ALLOWLIST")
    if allowlist is None:
        return
    allowed = {m.strip() for m in allowlist.split(",") if m.strip()}
    if model not in allowed:
        raise ValueError(
            f"model '{model}' is not in the configured allowlist. Allowed: {sorted(allowed)}"
        )


def save_audio(audio_chunks, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with open(tmp_path, "wb") as f:
            for chunk in audio_chunks:
                f.write(chunk)
        tmp_path.replace(output_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def get_client() -> ElevenLabs:
    global _client
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is required")
    timeout_seconds = float(os.environ.get("ELEVENLABS_TIMEOUT", "120"))
    # Include id(ElevenLabs) so cache invalidates when the class is patched in tests.
    cache_key = (api_key, timeout_seconds, id(ElevenLabs))
    if _client is not None and _client[0] == cache_key:
        return _client[1]
    try:
        instance = ElevenLabs(api_key=api_key, timeout=httpx.Timeout(timeout_seconds))
    except Exception:
        raise ValueError("Failed to initialize ElevenLabs client: invalid or missing API key") from None
    _client = (cache_key, instance)
    return instance


def resolve_voice_id(client: ElevenLabs, voice: str) -> str:
    """Resolve a voice name to its ID. If the value already looks like an ID, return it as-is."""
    now = time.monotonic()
    entry = _voices_cache.get(id(client))
    if entry is None or now - entry[0] > _VOICES_TTL:
        response = client.voices.get_all()
        _voices_cache[id(client)] = (now, response)
    else:
        response = entry[1]

    exact_id_match = None
    name_matches = []
    for v in response.voices:
        if v.voice_id == voice:
            exact_id_match = v.voice_id
            break
        if v.name:
            name_lower = v.name.lower()
            voice_lower = voice.lower()
            if name_lower == voice_lower or name_lower.split(" - ")[0] == voice_lower:
                name_matches.append(v)

    if exact_id_match is not None:
        return exact_id_match
    if len(name_matches) == 1:
        return name_matches[0].voice_id
    if len(name_matches) > 1:
        candidates = ", ".join(f"{v.name} ({v.voice_id})" for v in name_matches)
        raise ValueError(
            f"Voice '{voice}' is ambiguous. Matching voices: {candidates}"
        )
    available = [f"{v.name} ({v.voice_id})" for v in response.voices if v.name]
    raise ValueError(f"Voice '{voice}' not found. Available voices: {', '.join(available)}")


@mcp.tool
def text_to_speech(
    text: str,
    voice: str = "George",
    model: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
    output_path: str | None = None,
) -> str:
    """Convert text to speech audio using ElevenLabs.

    Args:
        text: The text to convert to speech.
        voice: Voice ID or name. Defaults to "George".
        model: Model ID. Defaults to "eleven_multilingual_v2".
        output_format: Audio format. Defaults to "mp3_44100_128".
        output_path: Optional file path to save audio. Defaults to auto-generated path.
    """
    _validate_model(model)
    max_chars = int(os.environ.get("MAX_TTS_CHARS", "5000"))
    if len(text) > max_chars:
        raise ValueError(
            f"text length {len(text)} exceeds maximum allowed {max_chars} characters."
        )
    client = get_client()
    voice_id = resolve_voice_id(client, voice)
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model,
        output_format=output_format,
    )
    path = resolve_output_path(output_path, voice, "tts", output_format)
    save_audio(audio, path)
    return str(path.resolve())


@mcp.tool
def sound_effect(
    prompt: str,
    duration: float | None = None,
    output_path: str | None = None,
) -> str:
    """Generate a sound effect from a text description using ElevenLabs.

    Args:
        prompt: Text description of the desired sound effect.
        duration: Optional duration in seconds (0.5-30). Auto-determined if omitted.
        output_path: Optional file path to save audio. Defaults to auto-generated path.
    """
    client = get_client()
    kwargs = {"text": prompt}
    if duration is not None:
        kwargs["duration_seconds"] = duration
    audio = client.text_to_sound_effects.convert(**kwargs)
    path = resolve_output_path(output_path, "sfx", "sfx")
    save_audio(audio, path)
    return str(path.resolve())


@mcp.tool
def list_voices() -> str:
    """List all available ElevenLabs voices.

    Returns a JSON array of voices with their ID, name, category, description, and labels.
    """
    client = get_client()
    response = client.voices.get_all()
    voices = [
        {
            "voice_id": v.voice_id,
            "name": v.name,
            "category": v.category,
            "description": v.description,
            "labels": v.labels,
        }
        for v in response.voices
    ]
    return json.dumps(voices, indent=2)


@mcp.tool
def get_voice(voice: str) -> str:
    """Get details for a specific ElevenLabs voice.

    Args:
        voice: Voice name or ID.

    Returns JSON with voice details including settings and preview URL.
    """
    client = get_client()
    voice_id = resolve_voice_id(client, voice)
    v = client.voices.get(voice_id)
    data = {
        "voice_id": v.voice_id,
        "name": v.name,
        "category": v.category,
        "description": v.description,
        "labels": v.labels,
        "settings": v.settings,
        "preview_url": v.preview_url,
    }
    return json.dumps(data, indent=2, default=str)


@mcp.tool
def speech_to_speech(
    audio_path: str,
    voice: str = "George",
    model: str = "eleven_english_sts_v2",
    output_path: str | None = None,
) -> str:
    """Convert speech in an audio file to a different voice.

    Args:
        audio_path: Path to the input audio file.
        voice: Target voice name or ID. Defaults to "George".
        model: Model ID. Defaults to "eleven_english_sts_v2".
        output_path: Optional file path to save audio. Defaults to auto-generated path.
    """
    _validate_model(model)
    input_path = validate_audio_path(audio_path)
    client = get_client()
    voice_id = resolve_voice_id(client, voice)
    path = resolve_output_path(output_path, voice, "sts")
    with open(input_path, "rb") as f:
        audio = client.speech_to_speech.convert(
            voice_id=voice_id,
            audio=f,
            model_id=model,
        )
        try:
            save_audio(audio, path)
        finally:
            close = getattr(audio, "close", None)
            if callable(close):
                close()
    return str(path.resolve())


@mcp.tool
def text_to_dialogue(
    dialogue: list[dict],
    output_path: str | None = None,
) -> str:
    """Generate multi-speaker dialogue audio from a script.

    Args:
        dialogue: List of dialogue turns. Each turn is a dict with "voice" (name or ID) and "text".
        output_path: Optional file path to save audio. Defaults to auto-generated path.
    """
    if not dialogue or not isinstance(dialogue, list):
        raise ValueError("dialogue must be a non-empty list of turn dicts.")
    for i, turn in enumerate(dialogue):
        if not isinstance(turn, dict):
            raise ValueError(f"dialogue[{i}] must be a dict, got {type(turn).__name__}.")
        missing = [k for k in ("voice", "text") if k not in turn]
        if missing:
            raise ValueError(f"dialogue[{i}] is missing required key(s): {', '.join(missing)}.")

    client = get_client()
    response = client.voices.get_all()
    voice_map: dict[str, str] = {}
    for v in response.voices:
        if v.voice_id:
            voice_map[v.voice_id] = v.voice_id
        if v.name:
            voice_map[v.name.lower()] = v.voice_id
            base = v.name.lower().split(" - ")[0]
            voice_map[base] = v.voice_id
    available_desc = [f"{v.name} ({v.voice_id})" for v in response.voices if v.name]

    def _resolve(voice: str) -> str:
        if voice in voice_map:
            return voice_map[voice]
        key = voice.lower()
        if key in voice_map:
            return voice_map[key]
        raise ValueError(
            f"Voice '{voice}' not found. Available voices: {', '.join(available_desc)}"
        )

    inputs = []
    for turn in dialogue:
        voice_id = _resolve(turn["voice"])
        inputs.append(DialogueInput(text=turn["text"], voice_id=voice_id))
    audio = client.text_to_dialogue.convert(inputs=inputs)
    path = resolve_output_path(output_path, "dialogue", "dialogue")
    save_audio(audio, path)
    return str(path.resolve())


@mcp.tool
def audio_isolation(
    audio_path: str,
    output_path: str | None = None,
) -> str:
    """Remove background noise from an audio file, isolating the voice.

    Args:
        audio_path: Path to the input audio file.
        output_path: Optional file path to save audio. Defaults to auto-generated path.
    """
    input_path = validate_audio_path(audio_path)
    client = get_client()
    path = resolve_output_path(output_path, "isolated", "isolation")
    with open(input_path, "rb") as f:
        audio = client.audio_isolation.convert(audio=f)
        try:
            save_audio(audio, path)
        finally:
            close = getattr(audio, "close", None)
            if callable(close):
                close()
    return str(path.resolve())


@mcp.tool
def speech_to_text(audio_path: str, model: str = "scribe_v2", output_path: str | None = None) -> str:
    """Transcribe an audio file to text.

    Args:
        audio_path: Path to the input audio file.
        model: Transcription model ID. Defaults to "scribe_v2".
        output_path: Optional file path to save the transcript. Defaults to returning text.
    """
    _validate_model(model)
    input_path = validate_audio_path(audio_path)
    client = get_client()
    with open(input_path, "rb") as f:
        response = client.speech_to_text.convert(
            file=f,
            model_id=model,
        )
    if output_path is not None:
        if output_path.strip() == "":
            raise ValueError("output_path must not be empty.")
        output_dir = get_output_dir().resolve()
        resolved = Path(output_path).resolve()
        try:
            resolved.relative_to(output_dir)
        except ValueError:
            raise ValueError(
                f"output_path '{output_path}' must be inside the configured output "
                f"directory '{output_dir}'."
            )
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(response.text, encoding="utf-8")
        return str(resolved)
    return response.text


@mcp.tool
def list_models() -> str:
    """List all available ElevenLabs models.

    Returns a JSON array of models with their ID, name, description, and capabilities.
    """
    client = get_client()
    models = client.models.list()
    data = [
        {
            "model_id": m.model_id,
            "name": m.name,
            "description": m.description,
            "can_do_text_to_speech": m.can_do_text_to_speech,
            "can_do_voice_conversion": m.can_do_voice_conversion,
        }
        for m in models
    ]
    return json.dumps(data, indent=2)


@mcp.tool
def get_usage() -> str:
    """Get current ElevenLabs API usage and quota information.

    Returns JSON with character usage, limits, and reset time.
    """
    client = get_client()
    user = client.user.get()
    sub = user.subscription
    if sub is None:
        return json.dumps({"error": "No subscription information available."}, indent=2)
    count = sub.character_count
    limit = sub.character_limit
    remaining = (limit - count) if (limit is not None and count is not None) else None
    data = {
        "tier": sub.tier,
        "character_count": count,
        "character_limit": limit,
        "characters_remaining": remaining,
        "next_reset_unix": sub.next_character_count_reset_unix,
    }
    return json.dumps(data, indent=2)


def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY environment variable is required. "
            "Set it before starting the server."
        )
    mcp.run()
