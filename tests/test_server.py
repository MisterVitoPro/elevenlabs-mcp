import os
import tempfile
from unittest.mock import patch
from pathlib import Path


def test_get_output_dir_uses_env_var():
    with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": "/tmp/test-output"}):
        from elevenlabs_mcp.server import get_output_dir
        assert get_output_dir() == Path("/tmp/test-output")


def test_get_output_dir_defaults_to_home():
    env = os.environ.copy()
    env.pop("ELEVENLABS_OUTPUT_DIR", None)
    with patch.dict(os.environ, env, clear=True):
        from elevenlabs_mcp.server import get_output_dir
        result = get_output_dir()
        assert result == Path.home() / "elevenlabs-output"


def test_generate_filename_tts():
    from elevenlabs_mcp.server import generate_filename
    name = generate_filename("Rachel", "tts")
    assert name.endswith("_Rachel.mp3")
    assert len(name) > len("_Rachel.mp3")


def test_generate_filename_sfx():
    from elevenlabs_mcp.server import generate_filename
    name = generate_filename("sfx", "sfx")
    assert name.endswith("_sfx.mp3")


def test_resolve_output_path_custom():
    from elevenlabs_mcp.server import resolve_output_path
    result = resolve_output_path("/tmp/custom.mp3", "Rachel", "tts")
    assert result == Path("/tmp/custom.mp3")


def test_resolve_output_path_default():
    from elevenlabs_mcp.server import resolve_output_path
    with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": tempfile.mkdtemp()}):
        result = resolve_output_path(None, "Rachel", "tts")
        assert str(result).endswith("_Rachel.mp3")


def test_save_audio_creates_directory_and_file():
    from elevenlabs_mcp.server import save_audio
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "test.mp3"
        audio_chunks = [b"fake", b"audio", b"data"]
        save_audio(audio_chunks, output_path)
        assert output_path.exists()
        assert output_path.read_bytes() == b"fakeaudiodata"
