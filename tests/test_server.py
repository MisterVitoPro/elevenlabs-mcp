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


def test_speech_to_speech():
    from elevenlabs_mcp.server import speech_to_speech

    mock_client = MagicMock()
    mock_voice_entry = MagicMock()
    mock_voice_entry.voice_id = "abc123"
    mock_voice_entry.name = "George"
    mock_client.voices.get_all.return_value = MagicMock(voices=[mock_voice_entry])
    mock_client.speech_to_speech.convert.return_value = iter([b"converted", b"audio"])

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as input_f:
        input_f.write(b"fake input audio")
        input_f.flush()
        input_path = input_f.name

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "output.mp3")
        with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
            result = speech_to_speech(
                audio_path=input_path,
                voice="George",
                output_path=output_file,
            )
        assert result == str(Path(output_file).resolve())
        assert Path(output_file).read_bytes() == b"convertedaudio"
        mock_client.speech_to_speech.convert.assert_called_once()
    os.unlink(input_path)


def test_text_to_dialogue():
    from elevenlabs_mcp.server import text_to_dialogue

    mock_client = MagicMock()
    mock_voice_alice = MagicMock()
    mock_voice_alice.voice_id = "alice_id"
    mock_voice_alice.name = "Alice"
    mock_voice_bob = MagicMock()
    mock_voice_bob.voice_id = "bob_id"
    mock_voice_bob.name = "Bob"
    mock_client.voices.get_all.return_value = MagicMock(
        voices=[mock_voice_alice, mock_voice_bob]
    )
    mock_client.text_to_dialogue.convert.return_value = iter([b"dialogue", b"audio"])

    dialogue = [
        {"voice": "Alice", "text": "Hello there!"},
        {"voice": "Bob", "text": "Hi Alice!"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "dialogue.mp3")
        with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
            result = text_to_dialogue(dialogue=dialogue, output_path=output_file)

        assert result == str(Path(output_file).resolve())
        assert Path(output_file).read_bytes() == b"dialogueaudio"
        call_kwargs = mock_client.text_to_dialogue.convert.call_args
        inputs = call_kwargs.kwargs["inputs"]
        assert len(inputs) == 2
        assert inputs[0].text == "Hello there!"
        assert inputs[0].voice_id == "alice_id"
        assert inputs[1].text == "Hi Alice!"
        assert inputs[1].voice_id == "bob_id"


def test_audio_isolation():
    from elevenlabs_mcp.server import audio_isolation

    mock_client = MagicMock()
    mock_client.audio_isolation.convert.return_value = iter([b"clean", b"audio"])

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as input_f:
        input_f.write(b"noisy audio data")
        input_f.flush()
        input_path = input_f.name

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "isolated.mp3")
        with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
            result = audio_isolation(
                audio_path=input_path,
                output_path=output_file,
            )

        assert result == str(Path(output_file).resolve())
        assert Path(output_file).read_bytes() == b"cleanaudio"
        mock_client.audio_isolation.convert.assert_called_once()

    os.unlink(input_path)


def test_speech_to_text():
    from elevenlabs_mcp.server import speech_to_text

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello, this is a transcription test."
    mock_client.speech_to_text.convert.return_value = mock_response

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as input_f:
        input_f.write(b"fake audio data")
        input_f.flush()
        input_path = input_f.name

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = speech_to_text(audio_path=input_path)

    assert result == "Hello, this is a transcription test."
    mock_client.speech_to_text.convert.assert_called_once()
    call_kwargs = mock_client.speech_to_text.convert.call_args.kwargs
    assert call_kwargs["model_id"] == "scribe_v2"
    os.unlink(input_path)


def test_list_models():
    from elevenlabs_mcp.server import list_models

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.model_id = "eleven_multilingual_v2"
    mock_model.name = "Multilingual v2"
    mock_model.description = "Multi-language model"
    mock_model.can_do_text_to_speech = True
    mock_model.can_do_voice_conversion = True
    mock_client.models.list.return_value = [mock_model]

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = list_models()

    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["model_id"] == "eleven_multilingual_v2"
    assert data[0]["name"] == "Multilingual v2"
    assert data[0]["description"] == "Multi-language model"
    assert data[0]["can_do_text_to_speech"] is True
    assert data[0]["can_do_voice_conversion"] is True


def test_get_usage():
    from elevenlabs_mcp.server import get_usage

    mock_client = MagicMock()
    mock_subscription = MagicMock()
    mock_subscription.tier = "starter"
    mock_subscription.character_count = 5000
    mock_subscription.character_limit = 30000
    mock_subscription.next_character_count_reset_unix = 1700000000
    mock_user = MagicMock()
    mock_user.subscription = mock_subscription
    mock_client.user.get.return_value = mock_user

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = get_usage()

    data = json.loads(result)
    assert data["tier"] == "starter"
    assert data["character_count"] == 5000
    assert data["character_limit"] == 30000
    assert data["characters_remaining"] == 25000
    assert data["next_reset_unix"] == 1700000000
