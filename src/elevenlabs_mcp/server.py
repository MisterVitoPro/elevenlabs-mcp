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


def save_audio(audio_chunks, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)


from elevenlabs.client import ElevenLabs


def get_client() -> ElevenLabs:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is required")
    return ElevenLabs(api_key=api_key)


@mcp.tool
def text_to_speech(
    text: str,
    voice: str = "Rachel",
    model: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
    output_path: str | None = None,
) -> str:
    """Convert text to speech audio using ElevenLabs.

    Args:
        text: The text to convert to speech.
        voice: Voice ID or name. Defaults to "Rachel".
        model: Model ID. Defaults to "eleven_multilingual_v2".
        output_format: Audio format. Defaults to "mp3_44100_128".
        output_path: Optional file path to save audio. Defaults to auto-generated path.
    """
    client = get_client()
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice,
        model_id=model,
        output_format=output_format,
    )
    path = resolve_output_path(output_path, voice, "tts")
    save_audio(audio, path)
    return str(path.resolve())


def main():
    mcp.run()
