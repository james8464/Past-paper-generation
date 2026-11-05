# Keep French inference on the explicitly selected server, without proxy routing.

from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


def validate_endpoint(url: str, *, allow_remote: bool):
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Adresse Ollama invalide") from None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or port == 0
    ):
        raise ValueError("Adresse Ollama invalide")
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        if not allow_remote:
            raise ValueError(
                "Un serveur Ollama distant nécessite votre accord explicite"
            )
        if parsed.scheme != "https":
            raise ValueError("Un serveur distant doit utiliser HTTPS")


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Une redirection du serveur Ollama est interdite")


def open_ollama_request(request: Request, *, timeout: int):
    return build_opener(ProxyHandler({}), NoRedirects()).open(request, timeout=timeout)


def ollama_request(
    url: str,
    data: bytes,
    headers: dict,
    *,
    attempts: int = 2,
    timeout_seconds: int = 900,
):
    # Transport failures are explicit. Only structured-response repairs are
    # retried by the French client; never silently switch inference endpoints.
    # A 12B model can need more than three minutes for this route's large,
    # schema-constrained exercise payload on a memory-limited Mac.
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 900:
        raise ValueError("Ollama timeout must be an integer from 1 to 900 seconds.")
    return open_ollama_request(
        Request(url, data=data, headers=headers, method="POST"), timeout=timeout_seconds
    )
