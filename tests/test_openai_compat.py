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


def test_gpt5_chat_completion_does_not_downgrade_to_max_tokens_for_old_sdk():
    """GPT-5 models should not be downgraded to max_tokens on old SDKs.

    The API rejects max_tokens for GPT-5/o-series, so we surface the SDK mismatch
    and let callers use model fallback chains.
    """
    client = _LegacyClient()

    try:
        create_chat_completion(
            client,
            model="gpt-5-mini",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=123,
        )
        assert False, "Expected TypeError for unsupported max_completion_tokens in old SDK"
    except TypeError as exc:
        assert "max_completion_tokens" in str(exc)

    # Should only try once (max_completion_tokens) and fail fast.
    assert len(client.chat.completions.payloads) == 1
    assert client.chat.completions.payloads[0]["max_completion_tokens"] == 123


def test_legacy_chat_completion_keeps_legacy_sampling_params():
    client = _Client()

    create_chat_completion(
        client,
        model="gpt-4-turbo",  # Use gpt-4-turbo instead of gpt-4o-mini
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
    # These models don't have aliases, so they're returned as-is with fallbacks
    assert _answer_model_candidates("gpt-5.5") == ["gpt-5.5", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
    assert _answer_model_candidates("gpt-5.4-mini") == ["gpt-5.4-mini", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
    # Test aliasing works for known models
    assert _answer_model_candidates("gpt-4.1") == ["gpt-4-turbo", "gpt-4o-mini", "gpt-4o", "gpt-4"]
    assert _answer_model_candidates("gpt-4.1-mini") == ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]


class _BadRequestError(Exception):
    """Mock BadRequestError from OpenAI API."""


class _APIErrorCompletions:
    """Mock completions that simulates OpenAI API parameter errors."""
    def __init__(self, reject_max_tokens=True):
        self.reject_max_tokens = reject_max_tokens
        self.attempts = []

    def create(self, **kwargs):
        self.attempts.append(kwargs)
        
        # Simulate OpenAI API rejecting the wrong parameter
        if self.reject_max_tokens and "max_tokens" in kwargs and "max_completion_tokens" not in kwargs:
            raise _BadRequestError(
                "Error code: 400 - {'error': {'message': \"Unsupported parameter: "
                "'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.\", "
                "'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}"
            )
        elif not self.reject_max_tokens and "max_completion_tokens" in kwargs and "max_tokens" not in kwargs:
            raise _BadRequestError(
                "Error code: 400 - {'error': {'message': \"Unsupported parameter: "
                "'max_completion_tokens' is not supported with this model. Use 'max_tokens' instead.\", "
                "'type': 'invalid_request_error', 'param': 'max_completion_tokens', 'code': 'unsupported_parameter'}}"
            )
        
        # Succeed if the right parameter is present
        return kwargs


class _APIErrorClient:
    def __init__(self, reject_max_tokens=True):
        self.chat = _Chat()
        self.chat.completions = _APIErrorCompletions(reject_max_tokens)


def test_api_error_retry_max_tokens_to_max_completion_tokens():
    """When OpenAI API rejects max_tokens, retry with max_completion_tokens."""
    client = _APIErrorClient(reject_max_tokens=True)
    
    # Use a model that our detection doesn't recognize as needing max_completion_tokens
    # This simulates a case where OpenAI adds a new model or changes requirements
    result = create_chat_completion(
        client,
        model="gpt-4-turbo",  # Detected as using max_tokens
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=150,
    )
    
    # Should have made 2 attempts (first with max_tokens, retry with max_completion_tokens)
    assert len(client.chat.completions.attempts) == 2
    
    # First attempt should have had max_tokens (our detection)
    assert "max_tokens" in client.chat.completions.attempts[0]
    
    # The successful result should have max_completion_tokens
    assert "max_completion_tokens" in result
    assert result["max_completion_tokens"] == 150
    assert "max_tokens" not in result


def test_api_error_retry_max_completion_tokens_to_max_tokens():
    """When OpenAI API rejects max_completion_tokens, retry with max_tokens."""
    client = _APIErrorClient(reject_max_tokens=False)
    
    # Use a model that our detection thinks needs max_completion_tokens
    # but OpenAI actually requires max_tokens (e.g., older model version)
    result = create_chat_completion(
        client,
        model="gpt-4o-mini",  # Detected as using max_completion_tokens
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=150,
    )
    
    # Should have made 2 attempts (first with max_completion_tokens, retry with max_tokens)
    assert len(client.chat.completions.attempts) == 2
    
    # First attempt should have had max_completion_tokens (our detection)
    assert "max_completion_tokens" in client.chat.completions.attempts[0]
    
    # The successful result should have max_tokens
    assert "max_tokens" in result
    assert result["max_tokens"] == 150
    assert "max_completion_tokens" not in result
