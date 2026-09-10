# AGENTS.md — GifMaker

Entry map for AI agents and contributors. Read before coding.

## Canonical docs (order)

1. [DOCS/SUMMARY.md](DOCS/SUMMARY.md) — status, structure, quick links  
2. [DOCS/SBOM.md](DOCS/SBOM.md) — packages / security (update on every dep change)  
3. [DOCS/SCRATCHPAD.md](DOCS/SCRATCHPAD.md) — active tasks, blockers, last actions  
4. [DOCS/STYLE_GUIDE.md](DOCS/STYLE_GUIDE.md) — conventions  
5. [DOCS/ARCHITECTURE.md](DOCS/ARCHITECTURE.md) — system design  
6. [DOCS/CHANGELOG.md](DOCS/CHANGELOG.md) — version history  

Root `SUMMARY.md` / `SCRATCHPAD.md` / `CHANGELOG.md` are **legacy pointers** → prefer `DOCS/`.

## Preservation

Every file under `DOCS/` keeps:

`<!-- PRESERVATION RULE: Never delete or replace content. Append or annotate only. -->`

Append or `[AMENDED YYYY-MM-DD]:` — never wipe history.

## Stack

- Python 3.8+ GUI app (tkinter)
- Package: `gif_maker/` (`gui/`, `core/`, `utils/`)
- Runtime deps: `pyautogui`, `Pillow` — see `requirements.txt` / `pyproject.toml`
- Tests: `python -m pytest tests/`

## Commands

```bat
pip install -r requirements.txt
pip install -e ".[dev]"
python -m gif_maker
python -m pytest tests/ -v
python -m pip_audit -r requirements.txt
```

Prefer a project venv; host packages can conflict (e.g. streamlit pinning older Pillow).

**SBOM rule:** After any dep change, update [DOCS/SBOM.md](DOCS/SBOM.md) and run `python -m pip_audit -r requirements.txt` (never bare whole-env `pip-audit` as project signal). Keep `requirements.txt` ↔ `pyproject.toml` runtime pins in sync.

## Scope rules

- Do not rename/refactor outside the task — note extras under SCRATCHPAD `Out-of-Scope Observations`
- Update SBOM when installing/removing packages
- Checkpoint SCRATCHPAD during work
