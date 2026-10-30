"""Credentialed vendor transport must not follow redirects or echo its key."""

import io
import json
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler

import pytest

from Backend.Core.providers import HostedLLMClient

KEY = "fictional-private-vendor-token-for-transport-test"


def complete_response(provider):
    reply = (
        {"status": "completed", "output_text": '{"answer":42}'}
        if provider == "openai"
        else {
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": '{"answer":42}'}],
        }
    )
    return io.BytesIO(json.dumps(reply).encode())


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
@pytest.mark.parametrize("destination", ["cross_host", "http", "same_host"])
def test_vendor_redirects_never_forward_credentials(monkeypatch, provider, destination):
    vendor = {"openai": "api.openai.com", "anthropic": "api.anthropic.com"}[provider]
    target = {
        "cross_host": "https://unrelated.invalid/collect",
        "http": f"http://{vendor}/collect",
        "same_host": f"https://{vendor}/elsewhere",
    }[destination]
    forwarded = []

    def simulate_redirect(request, handler):
        redirect = handler.redirect_request(request, None, 302, "Found", {}, target)
        if redirect is None:
            raise HTTPError(
                request.full_url, 302, "Found", {}, io.BytesIO(b"redirect refused")
            )
        # The unprotected standard-library handler forwards these headers.
        assert any(KEY in value for _, value in redirect.header_items())
        forwarded.append(redirect.header_items())
        return complete_response(provider)

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, **kwargs: simulate_redirect(request, HTTPRedirectHandler()),
    )

    class ProtectedOpener:
        def __init__(self, handler):
            self.handler = handler

        def open(self, request, **kwargs):
            assert request.full_url.startswith(f"https://{vendor}/")
            return simulate_redirect(request, self.handler)

    monkeypatch.setattr("urllib.request.build_opener", ProtectedOpener)
    with pytest.raises(RuntimeError, match="HTTP 302"):
        HostedLLMClient(provider=provider, model="fixture", api_key=KEY).generate_json(
            "Return JSON."
        )
    assert not forwarded


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_arbitrary_vendor_key_echo_is_redacted(monkeypatch, provider):
    def reject(request, **kwargs):
        raise HTTPError(
            request.full_url,
            401,
            "Denied",
            {},
            io.BytesIO(f"rejected credential {KEY}".encode()),
        )

    monkeypatch.setattr("urllib.request.urlopen", reject)

    class ProtectedOpener:
        def __init__(self, _handler):
            pass

        open = staticmethod(reject)

    monkeypatch.setattr("urllib.request.build_opener", ProtectedOpener)
    with pytest.raises(RuntimeError, match="HTTP 401") as failure:
        HostedLLMClient(provider=provider, model="fixture", api_key=KEY).generate_json(
            "Return JSON."
        )
    assert KEY not in str(failure.value)
    assert "[redacted]" in str(failure.value)
