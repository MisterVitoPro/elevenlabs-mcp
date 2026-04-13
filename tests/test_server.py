import json
import os
import tempfile
from unittest.mock import MagicMock, patch
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


def test_validate_audio_path_valid_file():
    from elevenlabs_mcp.server import validate_audio_path
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake audio")
        f.flush()
        result = validate_audio_path(f.name)
        assert result == Path(f.name)
    os.unlink(f.name)


def test_validate_audio_path_missing_file():
    import pytest
    from elevenlabs_mcp.server import validate_audio_path
    with pytest.raises(ValueError, match="Audio file not found"):
        validate_audio_path("/nonexistent/audio.mp3")


def test_list_voices():
    from elevenlabs_mcp.server import list_voices

    mock_client = MagicMock()
    mock_voice = MagicMock()
    mock_voice.voice_id = "abc123"
    mock_voice.name = "George"
    mock_voice.category = "premade"
    mock_voice.description = "A deep voice"
    mock_voice.labels = {"accent": "british"}
    mock_client.voices.get_all.return_value = MagicMock(voices=[mock_voice])

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = list_voices()

    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["voice_id"] == "abc123"
    assert data[0]["name"] == "George"
    assert data[0]["category"] == "premade"
    assert data[0]["description"] == "A deep voice"
    assert data[0]["labels"] == {"accent": "british"}


def test_get_voice():
    from elevenlabs_mcp.server import get_voice

    mock_client = MagicMock()
    mock_voice_list = MagicMock()
    mock_voice_entry = MagicMock()
    mock_voice_entry.voice_id = "abc123"
    mock_voice_entry.name = "George"
    mock_voice_list.voices = [mock_voice_entry]
    mock_client.voices.get_all.return_value = mock_voice_list

    mock_voice_detail = MagicMock()
    mock_voice_detail.voice_id = "abc123"
    mock_voice_detail.name = "George"
    mock_voice_detail.category = "premade"
    mock_voice_detail.description = "A deep voice"
    mock_voice_detail.labels = {"accent": "british"}
    mock_voice_detail.settings = None
    mock_voice_detail.preview_url = "https://example.com/preview.mp3"
    mock_client.voices.get.return_value = mock_voice_detail

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = get_voice(voice="George")

    data = json.loads(result)
    assert data["voice_id"] == "abc123"
    assert data["name"] == "George"
    assert data["preview_url"] == "https://example.com/preview.mp3"
