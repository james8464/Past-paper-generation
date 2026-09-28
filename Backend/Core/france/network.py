"""Keep French inference on the explicitly selected server, without proxy routing."""

from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Une redirection du serveur Ollama est interdite")


def open_ollama_request(request: Request, *, timeout: int):
    return build_opener(ProxyHandler({}), NoRedirects()).open(request, timeout=timeout)


def ollama_request(url: str, data: bytes, headers: dict, *, attempts: int = 2):
    # Transport failures are explicit. Only structured-response repairs are
    # retried by the French client; never silently switch inference endpoints.
    return open_ollama_request(
        Request(url, data=data, headers=headers, method="POST"), timeout=180
    )
