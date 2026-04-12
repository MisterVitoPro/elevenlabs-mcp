import os
from datetime import datetime
from pathlib import Path


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
