"""Diagnostico rapido do ambiente AI-Pessoal."""
from __future__ import annotations

import sys


def main() -> int:
    print("=== AI-Pessoal - diagnostico ===\n")
    try:
        import ai_pessoal
        from ai_pessoal.config import load_config
        from ai_pessoal.ollama_client import health_check as ollama_ok, resolve_chat_model
        from ai_pessoal.cortana_bridge import health_check as cortana_ok, is_cortana_enabled
    except ImportError as e:
        print(f"ERRO import: {e}")
        print("Rode: .\\install.ps1")
        return 1

    cfg, data_dir = load_config()
    print(f"Versao:     {ai_pessoal.__version__}")
    print(f"Dados:      {data_dir}")
    print(f"Config:     {data_dir / 'config.json'}")

    base = str(cfg["ollama"]["base_url"])
    model_cfg = cfg["ollama"]["model_default"]
    model = resolve_chat_model(cfg)
    ok = ollama_ok(base)
    print(f"\nOllama:     {'OK' if ok else 'OFFLINE'} ({base})")
    print(f"Modelo:     {model}" + (f" (config: {model_cfg})" if model != model_cfg else ""))

    sem = cfg.get("features", {}).get("semantic_search", False)
    print(f"Semantica:  {'on' if sem else 'off'}")

    if is_cortana_enabled(cfg):
        cok = cortana_ok(cfg)
        print(f"Cortana:    {'OK' if cok else 'OFFLINE'} ({cfg.get('cortana', {}).get('base_url')})")
    else:
        print("Cortana:    off (!cortana on)")

    cap = data_dir / "data" / "capture"
    n = len(list(cap.glob("*.md"))) if cap.exists() else 0
    print(f"\nCapturas:   {n}")

    if not ok:
        print("\n>>> Inicie: ollama serve")
        print(">>> Depois: ollama pull qwen2.5:7b")
        return 2

    print("\n>>> Pronto para: .\\run.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
