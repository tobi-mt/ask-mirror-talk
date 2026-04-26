from app.core.openai_compat import create_chat_completion


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


def test_legacy_chat_completion_keeps_legacy_sampling_params():
    client = _Client()

    create_chat_completion(
        client,
        model="gpt-4o",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=123,
        temperature=0.7,
        presence_penalty=0.4,
        frequency_penalty=0.3,
    )

    payload = client.chat.completions.payload
    assert payload["max_tokens"] == 123
    assert "max_completion_tokens" not in payload
    assert payload["temperature"] == 0.7
    assert payload["presence_penalty"] == 0.4
    assert payload["frequency_penalty"] == 0.3
