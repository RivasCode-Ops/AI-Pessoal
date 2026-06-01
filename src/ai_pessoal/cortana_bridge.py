from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ai_pessoal.capture import CaptureEntry, save_capture
from ai_pessoal.config import get_active_project


class CortanaError(Exception):
    pass


def cortana_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return cfg.get("cortana", {})


def is_cortana_enabled(cfg: dict[str, Any]) -> bool:
    if cfg.get("features", {}).get("cortana_bridge") is True:
        return True
    return bool(cortana_cfg(cfg).get("enabled", False))


def cortana_base_url(cfg: dict[str, Any]) -> str:
    return str(cortana_cfg(cfg).get("base_url", "http://127.0.0.1:8787")).rstrip("/")


def _request(
    cfg: dict[str, Any],
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    timeout: float = 30,
) -> Any:
    url = cortana_base_url(cfg) + path
    data = None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise CortanaError(f"Cortana HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise CortanaError(
            f"Cortana inacessível em {cortana_base_url(cfg)}. "
            "Suba o Cortana (npm run dev) e o SearXNG."
        ) from e
    except json.JSONDecodeError as e:
        raise CortanaError("Resposta inválida do Cortana.") from e


def health_check(cfg: dict[str, Any], timeout: float = 5) -> bool:
    try:
        data = _request(cfg, "/api/health", timeout=timeout)
        return bool(data.get("ok"))
    except CortanaError:
        return False


def start_search(
    cfg: dict[str, Any],
    demand: str,
    *,
    output_type: str | None = None,
) -> str:
    payload: dict[str, Any] = {"demand": demand.strip()}
    out = output_type or cortana_cfg(cfg).get("default_output_type")
    if out:
        payload["outputType"] = out
    data = _request(cfg, "/api/searches", method="POST", body=payload, timeout=60)
    search_id = str(data.get("id", "")).strip()
    if not search_id:
        raise CortanaError("Cortana não retornou id da pesquisa.")
    return search_id


def get_progress(cfg: dict[str, Any], search_id: str) -> dict[str, Any]:
    return _request(cfg, f"/api/searches/{search_id}/progress", timeout=15)


def get_search_detail(cfg: dict[str, Any], search_id: str) -> dict[str, Any]:
    data = _request(cfg, f"/api/searches/{search_id}", timeout=60)
    if not data or not data.get("search"):
        raise CortanaError(f"Pesquisa {search_id} não encontrada no Cortana.")
    return data


def wait_for_search(
    cfg: dict[str, Any],
    search_id: str,
    *,
    on_progress: Any | None = None,
) -> None:
    poll = float(cortana_cfg(cfg).get("poll_seconds", 3))
    timeout = float(cortana_cfg(cfg).get("timeout_seconds", 600))
    deadline = time.time() + timeout
    while time.time() < deadline:
        prog = get_progress(cfg, search_id)
        status = str(prog.get("status", ""))
        if on_progress:
            on_progress(prog)
        if status == "completed":
            return
        if status == "failed":
            raise CortanaError(str(prog.get("error") or "Pesquisa Cortana falhou."))
        time.sleep(poll)
    raise CortanaError(f"Timeout ({int(timeout)}s) aguardando pesquisa Cortana.")


def _format_sources(report: dict[str, Any] | None) -> str:
    if not report:
        return ""
    raw = report.get("sources_json") or "[]"
    try:
        sources = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return ""
    if not isinstance(sources, list):
        return ""
    lines: list[str] = []
    for item in sources[:10]:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("link") or "").strip()
        title = str(item.get("title") or url or "fonte").strip()
        if url:
            lines.append(f"- {title}: {url}")
    return "\n".join(lines)


def build_aprendi_body(detail: dict[str, Any], *, max_chars: int = 4500) -> str:
    search = detail.get("search") or {}
    report = detail.get("report")
    if not report or not str(report.get("content", "")).strip():
        raise CortanaError("Relatório Cortana vazio ou ainda não gerado.")

    content = str(report["content"]).strip()
    if len(content) > max_chars:
        content = content[: max_chars - 3] + "..."

    search_id = str(search.get("id", ""))
    demand = str(search.get("demand", "")).strip()
    parts: list[str] = []
    if demand:
        parts.append(f"Pergunta pesquisada: {demand}")
    parts.append(content)
    parts.append(f"Fonte: Cortana pesquisa {search_id}")
    links = _format_sources(report)
    if links:
        parts.append(f"Links:\n{links}")
    return "\n\n".join(parts)


def run_search_and_import(
    data_dir: Path,
    cfg: dict[str, Any],
    demand: str,
    *,
    on_progress: Any | None = None,
) -> tuple[CaptureEntry, str]:
    """Executa pesquisa no Cortana e grava como aprendi:."""
    search_id = start_search(cfg, demand)
    wait_for_search(cfg, search_id, on_progress=on_progress)
    detail = get_search_detail(cfg, search_id)
    body = build_aprendi_body(detail)
    entry = save_capture(
        data_dir,
        "aprendi",
        body,
        active_project=get_active_project(cfg),
        cfg=cfg,
    )
    return entry, search_id


def import_existing_search(
    data_dir: Path,
    cfg: dict[str, Any],
    search_id: str,
) -> CaptureEntry:
    detail = get_search_detail(cfg, search_id.strip())
    search = detail.get("search") or {}
    status = str(search.get("status", ""))
    if status != "completed":
        raise CortanaError(
            f"Pesquisa em status «{status}». Aguarde concluir no Cortana ou use cortana: pergunta"
        )
    body = build_aprendi_body(detail)
    return save_capture(
        data_dir,
        "aprendi",
        body,
        active_project=get_active_project(cfg),
        cfg=cfg,
    )
