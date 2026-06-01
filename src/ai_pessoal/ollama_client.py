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
        if e.code == 404 and "model" in detail.lower() and "not found" in detail.lower():
            raise OllamaError(detail) from e
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


def resolve_chat_model(cfg: dict) -> str:
    """Usa model_default se existir no Ollama; senão o primeiro disponível."""
    preferred = str(cfg.get("ollama", {}).get("model_default", "")).strip()
    base = str(cfg.get("ollama", {}).get("base_url", "http://127.0.0.1:11434"))
    try:
        models = list_models(base, timeout=5)
    except OllamaError:
        return preferred or "llama3.2:3b"
    if not models:
        return preferred or "llama3.2:3b"
    if preferred and preferred in models:
        return preferred
    if preferred:
        base_name = preferred.split(":")[0]
        for name in models:
            if name == base_name or name.startswith(base_name + ":"):
                return name
    return models[0]


def model_not_found_hint(cfg: dict, tried: str) -> str:
    available = []
    try:
        available = list_models(str(cfg.get("ollama", {}).get("base_url", "")))
    except OllamaError:
        pass
    lines = [
        f"Modelo «{tried}» não está no Ollama.",
        "Opções:",
        f"  1) ollama pull {tried}",
    ]
    if available:
        lines.append(f"  2) Ou em config.json use: \"model_default\": \"{available[0]}\"")
        lines.append(f"     (instalados: {', '.join(available)})")
    return "\n".join(lines)


def embed_text(
    base_url: str,
    model: str,
    text: str,
    *,
    timeout: float = 60,
) -> list[float]:
    payload: dict[str, Any] = {"model": model, "input": text}
    try:
        data = _request(base_url, "/api/embed", method="POST", body=payload, timeout=timeout)
        embeddings = data.get("embeddings")
        if embeddings and isinstance(embeddings[0], list):
            return [float(x) for x in embeddings[0]]
    except OllamaError:
        pass

    legacy = _request(
        base_url,
        "/api/embeddings",
        method="POST",
        body={"model": model, "prompt": text},
        timeout=timeout,
    )
    emb = legacy.get("embedding")
    if not emb:
        raise OllamaError("Resposta de embedding vazia do Ollama.")
    return [float(x) for x in emb]


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
