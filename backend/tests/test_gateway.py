import httpx
import pytest
from app.gateway import Gateway


def test_gateway_format_usage_retry_and_fallback(monkeypatch):
    requests = []
    real_client = httpx.Client

    def handler(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "id": "request-id",
                "model": "gpt-4o-mini",
                "choices": [{"message": {"content": '{"tool":"finish"}'}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 3},
            },
        )

    monkeypatch.setattr(
        "app.gateway.httpx.Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    result = Gateway().complete([{"role": "user", "content": "x"}], "openai/gpt-4o-mini", 10)
    assert len(requests) == 2
    assert requests[-1].url.path == "/v1/chat/completions"
    assert result["usage"]["prompt_tokens"] == 2
    assert result["request_id"] == "request-id"

    def changed(_):
        return httpx.Response(200, json={"model": "other-provider/model"})

    monkeypatch.setattr(
        "app.gateway.httpx.Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(changed), **kwargs),
    )
    with pytest.raises(RuntimeError, match="model changed"):
        Gateway().complete([], "openai/gpt-4o-mini", 10)


def test_gateway_unavailable_has_no_raw_error_or_secret(monkeypatch):
    real_client = httpx.Client
    monkeypatch.setattr(
        "app.gateway.httpx.Client",
        lambda **kwargs: real_client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(401, text="sensitive upstream details")
            ),
            **kwargs,
        ),
    )
    with pytest.raises(RuntimeError, match="gateway request failed") as error:
        Gateway().complete([], "openai/gpt-4o-mini", 10)
    assert "sensitive" not in str(error.value)
