from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class OllamaError(Exception):
    pass


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    timeout: float = 120,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise OllamaError(f"HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise OllamaError(
            f"Não foi possível conectar ao Ollama em {base_url}. "
            "Verifique se o serviço está rodando (ollama serve)."
        ) from e


def health_check(base_url: str, timeout: float = 5) -> bool:
    try:
        _request(base_url, "/api/tags", timeout=timeout)
        return True
    except (OllamaError, json.JSONDecodeError):
        return False


def list_models(base_url: str, timeout: float = 10) -> list[str]:
    data = _request(base_url, "/api/tags", timeout=timeout)
    models = data.get("models") or []
    return [str(m.get("name", "")) for m in models if m.get("name")]


def chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    timeout: float = 120,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    data = _request(base_url, "/api/chat", method="POST", body=payload, timeout=timeout)
    message = data.get("message") or {}
    content = message.get("content")
    if not content:
        raise OllamaError("Resposta vazia do Ollama.")
    return str(content).strip()
