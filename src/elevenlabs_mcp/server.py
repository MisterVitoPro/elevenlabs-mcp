import json
import os
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("ElevenLabs")


def get_output_dir() -> Path:
    return Path(os.environ.get("ELEVENLABS_OUTPUT_DIR", Path.home() / "elevenlabs-output"))


def generate_filename(label: str, kind: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{label}.mp3"


def resolve_output_path(output_path: str | None, label: str, kind: str) -> Path:
    if output_path:
        return Path(output_path)
    output_dir = get_output_dir()
    return output_dir / generate_filename(label, kind)


def validate_audio_path(audio_path: str) -> Path:
    path = Path(audio_path)
    if not path.is_file():
        raise ValueError(f"Audio file not found: {audio_path}")
    return path


def save_audio(audio_chunks, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)


from elevenlabs.client import ElevenLabs
from elevenlabs import DialogueInput


def get_client() -> ElevenLabs:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is required")
    return ElevenLabs(api_key=api_key)


def resolve_voice_id(client: ElevenLabs, voice: str) -> str:
    """Resolve a voice name to its ID. If the value already looks like an ID, return it as-is."""
    response = client.voices.get_all()
    for v in response.voices:
        if v.voice_id == voice:
            return voice
        if v.name:
            name_lower = v.name.lower()
            voice_lower = voice.lower()
            if name_lower == voice_lower or name_lower.split(" - ")[0] == voice_lower:
                return v.voice_id
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
    client = get_client()
    voice_id = resolve_voice_id(client, voice)
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model,
        output_format=output_format,
    )
    path = resolve_output_path(output_path, voice, "tts")
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
        save_audio(audio, path)
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
    client = get_client()
    inputs = []
    for turn in dialogue:
        voice_id = resolve_voice_id(client, turn["voice"])
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
        save_audio(audio, path)
    return str(path.resolve())


@mcp.tool
def speech_to_text(audio_path: str) -> str:
    """Transcribe an audio file to text.

    Args:
        audio_path: Path to the input audio file.
    """
    input_path = validate_audio_path(audio_path)
    client = get_client()
    with open(input_path, "rb") as f:
        response = client.speech_to_text.convert(
            file=f,
            model_id="scribe_v2",
        )
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
    data = {
        "tier": sub.tier,
        "character_count": sub.character_count,
        "character_limit": sub.character_limit,
        "characters_remaining": sub.character_limit - sub.character_count,
        "next_reset_unix": sub.next_character_count_reset_unix,
    }
    return json.dumps(data, indent=2)


def main():
    mcp.run()
