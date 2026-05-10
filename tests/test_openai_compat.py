from app.core.openai_compat import create_chat_completion
from app.qa.answer import _answer_model_candidates


class _Completions:
    def __init__(self):
        self.payload = None

    def create(self, **kwargs):
        self.payload = kwargs
        return kwargs


class _Chat:
    def __init__(self):
        self.completions = _Completions()


class _Client:
    def __init__(self):
        self.chat = _Chat()


class _LegacyCompletions:
    def __init__(self):
        self.payloads = []

    def create(self, **kwargs):
        self.payloads.append(kwargs)
        if "max_completion_tokens" in kwargs:
            raise TypeError("Completions.create() got an unexpected keyword argument 'max_completion_tokens'")
        return kwargs


class _LegacyClient:
    def __init__(self):
        self.chat = _Chat()
        self.chat.completions = _LegacyCompletions()


def test_gpt5_chat_completion_uses_new_token_param_and_omits_legacy_sampling():
    client = _Client()

    create_chat_completion(
        client,
        model="gpt-5.2",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=123,
        temperature=0.7,
        presence_penalty=0.4,
        frequency_penalty=0.3,
    )

    payload = client.chat.completions.payload
    assert payload["max_completion_tokens"] == 123
    assert "max_tokens" not in payload
    assert "temperature" not in payload
    assert "presence_penalty" not in payload
    assert "frequency_penalty" not in payload


def test_gpt5_chat_completion_raises_for_old_sdk_without_max_completion_tokens():
    """GPT-5 models require max_completion_tokens. Old SDK versions should fail fast."""
    client = _LegacyClient()

    try:
        create_chat_completion(
            client,
            model="gpt-5-mini",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=123,
        )
        assert False, "Expected TypeError to be raised for GPT-5 with old SDK"
    except TypeError as exc:
        assert "max_completion_tokens" in str(exc)
        # Verify it tried once with max_completion_tokens before failing
        assert len(client.chat.completions.payloads) == 1
        assert client.chat.completions.payloads[0]["max_completion_tokens"] == 123


def test_legacy_chat_completion_keeps_legacy_sampling_params():
    client = _Client()

    create_chat_completion(
        client,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=100,
        temperature=0.7,
        presence_penalty=0.4,
        frequency_penalty=0.3,
    )

    payload = client.chat.completions.payload
    assert payload["max_tokens"] == 100
    assert payload["temperature"] == 0.7
    assert payload["presence_penalty"] == 0.4
    assert payload["frequency_penalty"] == 0.3
    assert "max_completion_tokens" not in payload


def test_legacy_models_use_max_tokens_directly():
    """Non-reasoning models use max_tokens directly and do not try max_completion_tokens."""
    client = _LegacyClient()

    payload = create_chat_completion(
        client,
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=123,
    )

    # It should only try once with max_tokens
    assert len(client.chat.completions.payloads) == 1
    assert client.chat.completions.payloads[0]["max_tokens"] == 123
    assert payload["max_tokens"] == 123
    assert "max_completion_tokens" not in payload

    create_chat_completion(
        client,
        model="gpt-4o",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=123,
        temperature=0.7,
        presence_penalty=0.4,
        frequency_penalty=0.3,
    )

    # Use payloads list since _LegacyClient is being used
    last_payload = client.chat.completions.payloads[-1]
    assert last_payload["max_tokens"] == 123
    assert "max_completion_tokens" not in last_payload
    assert last_payload["temperature"] == 0.7
    assert last_payload["presence_penalty"] == 0.4
    assert last_payload["frequency_penalty"] == 0.3


def test_answer_model_candidates_alias_invalid_recommendations_and_keep_stable_fallbacks():
    assert _answer_model_candidates("gpt-5.5") == ["gpt-5.2", "gpt-4.1", "gpt-4.1-mini"]
    assert _answer_model_candidates("gpt-5.4-mini") == ["gpt-5-mini", "gpt-4.1", "gpt-4.1-mini"]
