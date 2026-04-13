# Expand ElevenLabs MCP Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 8 new MCP tools (list_voices, get_voice, speech_to_speech, text_to_dialogue, audio_isolation, speech_to_text, list_models, get_usage) to the ElevenLabs MCP server.

**Architecture:** All tools are added to `src/elevenlabs_mcp/server.py`, reusing existing helpers (`get_client`, `resolve_voice_id`, `resolve_output_path`, `save_audio`). A new `validate_audio_path` helper handles file existence checks for audio-input tools. Query tools return JSON strings; audio-producing tools return file paths.

**Tech Stack:** Python 3.10+, FastMCP, ElevenLabs SDK (`elevenlabs` package), pytest

---

### Task 1: Add `validate_audio_path` helper

**Files:**
- Modify: `src/elevenlabs_mcp/server.py:26` (insert before `save_audio`)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_validate_audio_path_valid_file tests/test_server.py::test_validate_audio_path_missing_file -v`
Expected: FAIL with `ImportError` or `cannot import name 'validate_audio_path'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after the `resolve_output_path` function (before `save_audio`):

```python
def validate_audio_path(audio_path: str) -> Path:
    path = Path(audio_path)
    if not path.is_file():
        raise ValueError(f"Audio file not found: {audio_path}")
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_validate_audio_path_valid_file tests/test_server.py::test_validate_audio_path_missing_file -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add validate_audio_path helper"
```

---

### Task 2: Add `list_voices` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `sound_effect` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
import json
from unittest.mock import MagicMock


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_list_voices -v`
Expected: FAIL with `ImportError` or `cannot import name 'list_voices'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after the `sound_effect` tool. Also add `import json` at the top of the file:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_list_voices -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add list_voices tool"
```

---

### Task 3: Add `get_voice` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `list_voices` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_get_voice -v`
Expected: FAIL with `ImportError` or `cannot import name 'get_voice'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after `list_voices`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_get_voice -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add get_voice tool"
```

---

### Task 4: Add `speech_to_speech` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `get_voice` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_speech_to_speech -v`
Expected: FAIL with `ImportError` or `cannot import name 'speech_to_speech'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after `get_voice`:

```python
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
    with open(input_path, "rb") as f:
        audio = client.speech_to_speech.convert(
            voice_id=voice_id,
            audio=f,
            model_id=model,
        )
    path = resolve_output_path(output_path, voice, "sts")
    save_audio(audio, path)
    return str(path.resolve())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_speech_to_speech -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add speech_to_speech tool"
```

---

### Task 5: Add `text_to_dialogue` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `speech_to_speech` tool, add `DialogueInput` import)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_text_to_dialogue -v`
Expected: FAIL with `ImportError` or `cannot import name 'text_to_dialogue'`

- [ ] **Step 3: Write the implementation**

Add `from elevenlabs import DialogueInput` near the top of `src/elevenlabs_mcp/server.py` (after the `from elevenlabs.client import ElevenLabs` line).

Then add the tool after `speech_to_speech`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_text_to_dialogue -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add text_to_dialogue tool"
```

---

### Task 6: Add `audio_isolation` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `text_to_dialogue` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_audio_isolation -v`
Expected: FAIL with `ImportError` or `cannot import name 'audio_isolation'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after `text_to_dialogue`:

```python
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
    with open(input_path, "rb") as f:
        audio = client.audio_isolation.convert(audio=f)
    path = resolve_output_path(output_path, "isolated", "isolation")
    save_audio(audio, path)
    return str(path.resolve())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_audio_isolation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add audio_isolation tool"
```

---

### Task 7: Add `speech_to_text` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `audio_isolation` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_speech_to_text -v`
Expected: FAIL with `ImportError` or `cannot import name 'speech_to_text'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after `audio_isolation`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_speech_to_text -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add speech_to_text tool"
```

---

### Task 8: Add `list_models` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `speech_to_text` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_list_models -v`
Expected: FAIL with `ImportError` or `cannot import name 'list_models'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after `speech_to_text`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_list_models -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add list_models tool"
```

---

### Task 9: Add `get_usage` tool

**Files:**
- Modify: `src/elevenlabs_mcp/server.py` (add after `list_models` tool)
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_get_usage -v`
Expected: FAIL with `ImportError` or `cannot import name 'get_usage'`

- [ ] **Step 3: Write the implementation**

Add to `src/elevenlabs_mcp/server.py` after `list_models`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/test_server.py::test_get_usage -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add src/elevenlabs_mcp/server.py tests/test_server.py && git commit -m "feat: add get_usage tool"
```

---

### Task 10: Run full test suite and final commit

**Files:**
- All previously modified files

- [ ] **Step 1: Run the full test suite**

Run: `cd D:/mcp/elevenlabs-mcp && uv run pytest tests/ -v`
Expected: All tests PASS (both existing and new)

- [ ] **Step 2: Verify all 10 tools are registered**

Run: `cd D:/mcp/elevenlabs-mcp && uv run python -c "from elevenlabs_mcp.server import mcp; print([t.name for t in mcp._tool_manager._tools.values()])"`

Expected output should include all 10 tools: `text_to_speech`, `sound_effect`, `list_voices`, `get_voice`, `speech_to_speech`, `text_to_dialogue`, `audio_isolation`, `speech_to_text`, `list_models`, `get_usage`

- [ ] **Step 3: Fix any issues found in steps 1-2**

If any tests fail or tools are missing, fix the issues before proceeding.

- [ ] **Step 4: Update pyproject.toml description**

In `pyproject.toml`, update the description to reflect the expanded functionality:

```toml
description = "MCP server for ElevenLabs text-to-speech, voice conversion, transcription, and audio tools"
```

- [ ] **Step 5: Commit**

```bash
cd D:/mcp/elevenlabs-mcp && git add pyproject.toml && git commit -m "chore: update project description for expanded tool set"
```
