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


# P1-003: generate_filename sanitization — replaces old test_generate_filename_tts/sfx
# Old assertions like endswith("_Rachel.mp3") conflict with sanitization/kind fixes.

def test_generate_filename_sanitizes_slash_in_label():
    # P1-003: voice name containing "/" must not produce path traversal in filename
    from elevenlabs_mcp.server import generate_filename
    name = generate_filename("My/Voice", "tts")
    assert "/" not in name


def test_generate_filename_sanitizes_dotdot_traversal():
    # P1-003: "../../etc/passwd" as voice name must not produce traversal sequences
    from elevenlabs_mcp.server import generate_filename
    name = generate_filename("../../etc/passwd", "tts")
    assert ".." not in name
    assert "/" not in name
    assert "\\" not in name


def test_generate_filename_truncates_long_label():
    # P1-003: labels longer than 64 chars must be truncated
    from elevenlabs_mcp.server import generate_filename
    long_label = "A" * 200
    name = generate_filename(long_label, "tts")
    label_with_ext = name.split("_")[-1]
    label_part = label_with_ext.rsplit(".", 1)[0]
    assert len(label_part) <= 64


def test_generate_filename_includes_kind_in_name():
    # P1-003/P1-004: kind ("tts", "sfx") must appear in filename
    from elevenlabs_mcp.server import generate_filename
    assert "tts" in generate_filename("Rachel", "tts")
    assert "sfx" in generate_filename("sfx", "sfx")


# P1-004: format-based file extension

def test_generate_filename_pcm_format_uses_pcm_extension():
    # P1-004: pcm output format must produce .pcm extension, not hardcoded .mp3
    from elevenlabs_mcp.server import generate_filename
    assert generate_filename("Rachel", "tts", "pcm_44100").endswith(".pcm")


def test_generate_filename_ulaw_format_uses_ulaw_extension():
    # P1-004: ulaw output format must produce .ulaw extension
    from elevenlabs_mcp.server import generate_filename
    assert generate_filename("Rachel", "tts", "ulaw_8000").endswith(".ulaw")


def test_generate_filename_mp3_format_uses_mp3_extension():
    # P1-004: mp3 output format must produce .mp3 extension
    from elevenlabs_mcp.server import generate_filename
    assert generate_filename("Rachel", "tts", "mp3_44100_128").endswith(".mp3")


def test_generate_filename_unknown_format_falls_back_to_mp3():
    # P1-004: unrecognised format falls back to .mp3
    from elevenlabs_mcp.server import generate_filename
    assert generate_filename("Rachel", "tts", "flac_44100").endswith(".mp3")


def test_ext_from_format_known_formats():
    # P1-004: internal helper _ext_from_format covers all documented formats
    from elevenlabs_mcp.server import _ext_from_format
    assert _ext_from_format("mp3_44100_128") == "mp3"
    assert _ext_from_format("pcm_44100") == "pcm"
    assert _ext_from_format("ulaw_8000") == "ulaw"
    assert _ext_from_format("opus_48000_32") == "opus"
    assert _ext_from_format("aac_44100_128") == "aac"
    assert _ext_from_format("flac_44100") == "mp3"


# P1-001: path traversal via output_path — replaces old test_resolve_output_path_custom

def test_resolve_output_path_rejects_traversal_outside_output_dir():
    # P1-001: absolute path outside configured output dir must raise ValueError
    import pytest
    import tempfile
    from elevenlabs_mcp.server import resolve_output_path

    with tempfile.TemporaryDirectory() as output_dir:
        with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": output_dir}):
            with pytest.raises(ValueError, match="must be inside the configured output directory"):
                resolve_output_path("/etc/passwd", "voice", "tts")


def test_resolve_output_path_accepts_path_inside_output_dir():
    # P1-001: path inside the configured output dir must be accepted
    import tempfile
    from elevenlabs_mcp.server import resolve_output_path

    with tempfile.TemporaryDirectory() as output_dir:
        target = os.path.join(output_dir, "my_output.mp3")
        with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": output_dir}):
            result = resolve_output_path(target, "voice", "tts")
        assert result == Path(target).resolve()


def test_resolve_output_path_custom_inside_output_dir():
    # P1-001: replacement for old test_resolve_output_path_custom (/tmp/custom.mp3)
    # After the fix, a custom path must live inside the configured output dir.
    import tempfile
    from elevenlabs_mcp.server import resolve_output_path

    with tempfile.TemporaryDirectory() as output_dir:
        custom_path = os.path.join(output_dir, "custom.mp3")
        with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": output_dir}):
            result = resolve_output_path(custom_path, "Rachel", "tts")
        assert result == Path(custom_path).resolve()


def test_resolve_output_path_default():
    from elevenlabs_mcp.server import resolve_output_path
    with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": tempfile.mkdtemp()}):
        result = resolve_output_path(None, "Rachel", "tts")
        assert str(result).endswith(".mp3")


# P2-007: empty string output_path

def test_resolve_output_path_rejects_empty_string():
    # P2-007: empty string output_path must raise ValueError
    import pytest
    import tempfile
    from elevenlabs_mcp.server import resolve_output_path
    with tempfile.TemporaryDirectory() as output_dir:
        with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": output_dir}):
            with pytest.raises(ValueError, match="must not be empty"):
                resolve_output_path("", "voice", "tts")


# P1-002: file exfiltration via validate_audio_path

def test_validate_audio_path_rejects_file_outside_input_dir():
    # P1-002: audio file outside configured input dir must raise ValueError
    import pytest
    import tempfile
    from elevenlabs_mcp.server import validate_audio_path

    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as outside_file:
            outside_file.write(b"audio data")
            outside_path = outside_file.name
        try:
            with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": input_dir}):
                with pytest.raises(ValueError, match="must be inside the configured input directory"):
                    validate_audio_path(outside_path)
        finally:
            os.unlink(outside_path)


def test_validate_audio_path_accepts_file_inside_input_dir():
    # P1-002: audio file inside configured input dir must be accepted
    import tempfile
    from elevenlabs_mcp.server import validate_audio_path

    with tempfile.TemporaryDirectory() as input_dir:
        input_file = os.path.join(input_dir, "test.mp3")
        Path(input_file).write_bytes(b"audio data")
        with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": input_dir}):
            result = validate_audio_path(input_file)
        assert result == Path(input_file).resolve()


def test_validate_audio_path_missing_file_inside_input_dir():
    # P1-002: missing file inside input dir must still raise "Audio file not found"
    import pytest
    import tempfile
    from elevenlabs_mcp.server import validate_audio_path

    with tempfile.TemporaryDirectory() as input_dir:
        missing_path = os.path.join(input_dir, "nonexistent.mp3")
        with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": input_dir}):
            with pytest.raises(ValueError, match="Audio file not found"):
                validate_audio_path(missing_path)


def test_validate_audio_path_valid_file():
    from elevenlabs_mcp.server import validate_audio_path
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_file = os.path.join(tmpdir, "test.mp3")
        with open(audio_file, "wb") as f:
            f.write(b"fake audio")
        with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": tmpdir}):
            result = validate_audio_path(audio_file)
            assert result == Path(audio_file).resolve()


def test_validate_audio_path_missing_file():
    import pytest
    from elevenlabs_mcp.server import validate_audio_path
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = os.path.join(tmpdir, "nonexistent.mp3")
        with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": tmpdir}):
            with pytest.raises(ValueError, match="Audio file not found"):
                validate_audio_path(missing_path)


def test_save_audio_creates_directory_and_file():
    from elevenlabs_mcp.server import save_audio
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "test.mp3"
        audio_chunks = [b"fake", b"audio", b"data"]
        save_audio(audio_chunks, output_path)
        assert output_path.exists()
        assert output_path.read_bytes() == b"fakeaudiodata"


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

    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            input_path = os.path.join(input_dir, "input.mp3")
            with open(input_path, "wb") as f:
                f.write(b"fake input audio")
            output_file = os.path.join(output_dir, "output.mp3")
            with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": input_dir, "ELEVENLABS_OUTPUT_DIR": output_dir}):
                with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
                    result = speech_to_speech(
                        audio_path=input_path,
                        voice="George",
                        output_path=output_file,
                    )
            assert result == str(Path(output_file).resolve())
            assert Path(output_file).read_bytes() == b"convertedaudio"
            mock_client.speech_to_speech.convert.assert_called_once()


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
        with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": tmpdir}):
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


# P1-005: text_to_dialogue malformed input validation (gap fills)

def test_text_to_dialogue_rejects_empty_list():
    # P1-005: empty dialogue list must raise ValueError mentioning "non-empty"
    import pytest
    from elevenlabs_mcp.server import text_to_dialogue
    with pytest.raises(ValueError, match="non-empty"):
        text_to_dialogue(dialogue=[])


def test_text_to_dialogue_rejects_none():
    # P1-005: None dialogue must raise ValueError
    import pytest
    from elevenlabs_mcp.server import text_to_dialogue
    with pytest.raises(ValueError):
        text_to_dialogue(dialogue=None)


def test_text_to_dialogue_rejects_turn_missing_text_key():
    # P1-005: dialogue turn missing "text" key must raise ValueError referencing index
    import pytest
    from elevenlabs_mcp.server import text_to_dialogue
    with pytest.raises(ValueError, match=r"dialogue\[0\]"):
        text_to_dialogue(dialogue=[{"voice": "Alice"}])


def test_text_to_dialogue_rejects_turn_missing_voice_key():
    # P1-005: dialogue turn missing "voice" key must raise ValueError referencing index
    import pytest
    from elevenlabs_mcp.server import text_to_dialogue
    with pytest.raises(ValueError, match=r"dialogue\[0\]"):
        text_to_dialogue(dialogue=[{"text": "hello"}])


def test_text_to_dialogue_rejects_non_dict_turn():
    # P1-005: non-dict item in dialogue list must raise ValueError referencing index
    import pytest
    from elevenlabs_mcp.server import text_to_dialogue
    with pytest.raises(ValueError, match=r"dialogue\[0\]"):
        text_to_dialogue(dialogue=["not a dict"])


# P1-007: N+1 voice resolution

def test_text_to_dialogue_fetches_voice_list_once():
    # P1-007: voices.get_all must be called exactly once even with repeated voice names
    import tempfile
    from elevenlabs_mcp.server import text_to_dialogue

    mock_client = MagicMock()
    mock_voice_alice = MagicMock()
    mock_voice_alice.voice_id = "alice_id"
    mock_voice_alice.name = "Alice"
    mock_voice_bob = MagicMock()
    mock_voice_bob.voice_id = "bob_id"
    mock_voice_bob.name = "Bob"
    mock_client.voices.get_all.return_value = MagicMock(voices=[mock_voice_alice, mock_voice_bob])
    mock_client.text_to_dialogue.convert.return_value = iter([b"audio"])

    dialogue = [
        {"voice": "Alice", "text": "Line one."},
        {"voice": "Bob", "text": "Line two."},
        {"voice": "Alice", "text": "Line three."},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "out.mp3")
        with patch.dict(os.environ, {"ELEVENLABS_OUTPUT_DIR": tmpdir}):
            with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
                text_to_dialogue(dialogue=dialogue, output_path=output_file)

    assert mock_client.voices.get_all.call_count == 1


# P1-008: HTTP timeout

def test_get_client_passes_timeout_to_elevenlabs():
    # P1-008: get_client must pass an httpx.Timeout to ElevenLabs constructor
    import httpx
    with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key"}):
        with patch("elevenlabs_mcp.server.ElevenLabs") as mock_cls:
            from elevenlabs_mcp.server import get_client
            get_client()
        kwargs = mock_cls.call_args.kwargs
        assert "timeout" in kwargs
        assert isinstance(kwargs["timeout"], httpx.Timeout)


def test_get_client_uses_env_var_timeout():
    # P1-008: ELEVENLABS_TIMEOUT env var must be used as the timeout value
    import httpx
    with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key", "ELEVENLABS_TIMEOUT": "30"}):
        with patch("elevenlabs_mcp.server.ElevenLabs") as mock_cls:
            from elevenlabs_mcp.server import get_client
            get_client()
        assert mock_cls.call_args.kwargs["timeout"] == httpx.Timeout(30.0)


def test_get_client_uses_default_timeout_120():
    # P1-008: default timeout must be 120 seconds when env var is absent
    import httpx
    env = {k: v for k, v in os.environ.items() if k != "ELEVENLABS_TIMEOUT"}
    env["ELEVENLABS_API_KEY"] = "test-key"
    with patch.dict(os.environ, env, clear=True):
        with patch("elevenlabs_mcp.server.ElevenLabs") as mock_cls:
            from elevenlabs_mcp.server import get_client
            get_client()
        assert mock_cls.call_args.kwargs["timeout"] == httpx.Timeout(120.0)


# P1-006: get_usage None-field handling (gap fills)

def test_get_usage_none_subscription_returns_error_json():
    # P1-006: None subscription must return JSON with an "error" key instead of crashing
    from elevenlabs_mcp.server import get_usage

    mock_client = MagicMock()
    mock_user = MagicMock()
    mock_user.subscription = None
    mock_client.user.get.return_value = mock_user

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = get_usage()

    assert "error" in json.loads(result)


def test_get_usage_none_character_count_returns_none_remaining():
    # P1-006: None character_count must produce characters_remaining=None rather than crashing
    from elevenlabs_mcp.server import get_usage

    mock_client = MagicMock()
    mock_sub = MagicMock()
    mock_sub.tier = "starter"
    mock_sub.character_count = None
    mock_sub.character_limit = 30000
    mock_sub.next_character_count_reset_unix = 1700000000
    mock_user = MagicMock()
    mock_user.subscription = mock_sub
    mock_client.user.get.return_value = mock_user

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = get_usage()

    assert json.loads(result)["characters_remaining"] is None


def test_get_usage_none_character_limit_returns_none_remaining():
    # P1-006: None character_limit must produce characters_remaining=None rather than crashing
    from elevenlabs_mcp.server import get_usage

    mock_client = MagicMock()
    mock_sub = MagicMock()
    mock_sub.tier = "starter"
    mock_sub.character_count = 5000
    mock_sub.character_limit = None
    mock_sub.next_character_count_reset_unix = 1700000000
    mock_user = MagicMock()
    mock_user.subscription = mock_sub
    mock_client.user.get.return_value = mock_user

    with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
        result = get_usage()

    assert json.loads(result)["characters_remaining"] is None


def test_audio_isolation():
    from elevenlabs_mcp.server import audio_isolation

    mock_client = MagicMock()
    mock_client.audio_isolation.convert.return_value = iter([b"clean", b"audio"])

    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            input_path = os.path.join(input_dir, "noisy.mp3")
            with open(input_path, "wb") as f:
                f.write(b"noisy audio data")
            output_file = os.path.join(output_dir, "isolated.mp3")
            with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": input_dir, "ELEVENLABS_OUTPUT_DIR": output_dir}):
                with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
                    result = audio_isolation(
                        audio_path=input_path,
                        output_path=output_file,
                    )

            assert result == str(Path(output_file).resolve())
            assert Path(output_file).read_bytes() == b"cleanaudio"
            mock_client.audio_isolation.convert.assert_called_once()


def test_speech_to_text():
    from elevenlabs_mcp.server import speech_to_text

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello, this is a transcription test."
    mock_client.speech_to_text.convert.return_value = mock_response

    with tempfile.TemporaryDirectory() as input_dir:
        input_path = os.path.join(input_dir, "audio.mp3")
        with open(input_path, "wb") as f:
            f.write(b"fake audio data")
        with patch.dict(os.environ, {"ELEVENLABS_INPUT_DIR": input_dir}):
            with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
                result = speech_to_text(audio_path=input_path)

    assert result == "Hello, this is a transcription test."
    mock_client.speech_to_text.convert.assert_called_once()
    call_kwargs = mock_client.speech_to_text.convert.call_args.kwargs
    assert call_kwargs["model_id"] == "scribe_v2"


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


# P2-009: text_to_speech length cap

def test_text_to_speech_rejects_text_exceeding_max_chars():
    # P2-009: text longer than MAX_TTS_CHARS must raise ValueError before calling the API
    import pytest
    from elevenlabs_mcp.server import text_to_speech

    long_text = "x" * 5001
    with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key", "MAX_TTS_CHARS": "5000"}):
        with patch("elevenlabs_mcp.server.get_client") as mock_get_client:
            with pytest.raises(ValueError, match="5000"):
                text_to_speech(text=long_text)
            mock_get_client.assert_not_called()


def test_text_to_speech_accepts_text_at_max_chars():
    # P2-009: text exactly at MAX_TTS_CHARS must be accepted and processed normally
    import tempfile
    from elevenlabs_mcp.server import text_to_speech

    exact_text = "x" * 5000
    mock_client = MagicMock()
    mock_voice = MagicMock()
    mock_voice.voice_id = "abc123"
    mock_voice.name = "George"
    mock_client.voices.get_all.return_value = MagicMock(voices=[mock_voice])
    mock_client.text_to_speech.convert.return_value = iter([b"audio"])

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "out.mp3")
        with patch.dict(os.environ, {
            "ELEVENLABS_API_KEY": "test-key",
            "MAX_TTS_CHARS": "5000",
            "ELEVENLABS_OUTPUT_DIR": tmpdir,
        }):
            with patch("elevenlabs_mcp.server.get_client", return_value=mock_client):
                result = text_to_speech(text=exact_text, output_path=output_file)
        assert result is not None
