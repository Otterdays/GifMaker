<!-- PRESERVATION RULE: Never delete or replace content. Append or annotate only. -->

# Gif-Maker Software Bill of Materials (SBOM)

*Security tracking - update on every package install/remove*

## 2026-09-10b - Full inventory pass (parallel-safe)

*[Agent claim: SBOM docs only — no app code. Other agents own P0/P1 code.]*  
*[AMENDED same day: app version moved to **1.0.5** by P0 agent — **dependency pins unchanged**; inventory still valid.]*

### Sources of truth

| Artifact | Role |
|----------|------|
| `requirements.txt` | Runtime install pin |
| `pyproject.toml` `[project].dependencies` | Packaging / editable install |
| `pyproject.toml` `[project.optional-dependencies].dev` | Dev extras |
| `pyproject.toml` `[build-system]` | Build isolation only |

Pins must stay **in sync** across `requirements.txt` ↔ `pyproject.toml` runtime deps.

### Observed installed versions (host Python 3.13.15 — 2026-09-10)

| Package | Installed | Latest on PyPI (spot-check) | Pin in project | License | Role |
|---------|-----------|-----------------------------|----------------|---------|------|
| pyautogui | 0.9.54 | 0.9.54 | >=0.9.54 | BSD | Direct runtime |
| Pillow | 12.3.0 | 12.3.0 | >=12.3.0,<13 | MIT-CMU | Direct runtime |
| pytest | 8.4.1 | (dev) | >=7.0 (optional) | MIT | Dev |
| setuptools | 80.9.0 | (build) | >=61.0 (build-system) | MIT | Build |
| mouseinfo | 0.1.3 | 0.1.3 | transitive via pyautogui | **GPLv3+** | Transitive |
| pyscreeze | 1.0.1 | 1.0.1 | transitive | MIT | Transitive (screenshots) |
| pygetwindow | 0.0.9 | 0.0.9 | transitive | BSD | Transitive |
| pytweening | 1.2.0 | 1.2.0 | transitive | MIT | Transitive |
| pymsgbox | 1.0.9 | 2.0.1 available | transitive (pulled 1.0.9) | **GPLv3+** | Transitive |

### Stdlib / bundled (not pip)

| Module | Purpose | Notes |
|--------|---------|-------|
| tkinter | GUI | OS/Python install; not in requirements |
| threading | Recording / GIF workers | Stdlib |
| pathlib / os / subprocess / platform | FS + open-file helpers | Stdlib |

### Native / binary notes (Pillow)

Pillow wheels typically ship or link: libjpeg / zlib / freetype / etc. (platform wheel). No separate pip packages required for GifMaker GIF path.

### License watch

- **Direct deps**: BSD (pyautogui) + MIT-CMU (Pillow) — permissive
- **Transitive GPLv3+**: `mouseinfo`, `pymsgbox` via pyautogui — relevant if distributing proprietary binaries; app LICENSE is proprietary. Flag for legal review before commercial redistribution of bundled interpreter+deps.
- GifMaker does not import mouseinfo/pymsgbox directly; they ride along with pyautogui.

### Audit procedure (use this, not whole-env)

```bat
python -m pip_audit -r requirements.txt
```

Optional with dev extras resolved from project:

```bat
pip install -e ".[dev]"
python -m pip_audit -r requirements.txt
```

**Do not** treat bare `python -m pip_audit` (no `-r`) as project signal — host site-packages can report hundreds of unrelated vulns (observed ~467 / 48 pkgs on this machine).

### Re-verify this pass

- `python -m pip_audit -r requirements.txt` → **No known vulnerabilities found** (rechecked 2026-09-10b)
- Direct pins unchanged this pass (already at secure floor from 1.0.4 bump)
- Transitive: all at latest except **pymsgbox** (1.0.9 installed; 2.0.1 on PyPI) — version chosen by pyautogui resolver; no forced bump without testing pyautogui

### Out of SBOM scope (other agents)

- App code P0/P1 reliability work — not dep inventory
- Adding lockfile (`uv.lock` / `requirements.lock`) — optional future hardening

---

## 2026-09-10 - Security audit refresh (v1.0.4)

### Direct runtime dependencies (current pin)

| Package | Version pin | Purpose | License | Audit |
|---------|-------------|---------|---------|-------|
| pyautogui | >=0.9.54 | Screenshot capture, mouse control | BSD-3-Clause | OK — latest 0.9.54 |
| Pillow | >=12.3.0,<13 | Image processing, GIF creation | HPND-style / MIT-CMU | OK — `pip-audit` clean at 12.3.0 |

### Dev dependencies

| Package | Version pin | Purpose | License | Audit |
|---------|-------------|---------|---------|-------|
| pytest | >=7.0 | Unit testing | MIT | OK — local env had 8.4.1 |
| setuptools | >=61.0 | build-system only | MIT | OK |

### Transitive (pyautogui, Windows)

- mouseinfo, pyscreeze, pygetwindow, pytweening, pymsgbox

### Audit findings → actions

| Finding | Severity | Action |
|---------|----------|--------|
| Old pin `Pillow>=10.4.0,<12` resolved into vulnerable line (pip-audit: 35 hits vs 11.3.0 resolver path; CVEs fixed across 12.1.1 / 12.2.0 / **12.3.0**) | High | Bumped to `>=12.3.0,<13` in `requirements.txt` + `pyproject.toml` |
| Installed env previously on Pillow 10.4.0 while docs claimed 11.x | Medium | Documented; pin now forces patched major |
| Global env streamlit 1.48.1 wants `pillow<12` | Info | Conflict is host-wide, not GifMaker runtime. Prefer venv for this project |
| pyautogui | Low | Still current; no pip-audit hits |

### Verification (2026-09-10)

- Python: 3.13.15
- Tests: `20 passed` after Pillow 12.3.0 install
- `python -m pip_audit -r` with new pin: **No known vulnerabilities found**
- Tool used: `pip-audit` (via `python -m pip_audit`)

### Risk note (app-specific)

GifMaker mostly screenshots + writes GIFs (trusted local capture). Many Pillow CVEs need crafted hostile image files (PSD/EPS/McIDAS/etc.). Still upgrade — defense in depth if user ever loads external frames / browse paths.

---

## 2025-03-12 - Initial SBOM

| Package | Version | Purpose | License | Audit |
|---------|---------|---------|---------|-------|
| pyautogui | 0.9.54 | Screenshot capture, mouse control | BSD-3-Clause | OK |
| Pillow | >=10.4.0,<12 | Image processing, GIF creation | HPND | OK |

## Dependencies ( transitive )

- **pyautogui** pulls: pyscreeze, pygetwindow, pytweening, pymsgbox (Windows)
- **Pillow** pulls: none (optional: libjpeg, zlib for formats)

## Dev Dependencies

| Package | Version | Purpose | License | Audit |
|---------|---------|---------|---------|-------|
| pytest | >=7.0 | Unit testing | MIT | OK |

## Audit Notes

- Pillow 11.0.0: Security updates over 10.0.1, Python 3.8+ supported
- pyautogui 0.9.54: Latest stable, cross-platform
- pytest: Dev-only, not shipped

[AMENDED 2026-09-10]: Prior `<12` pin and “Pillow 11.0.0 OK” notes are **stale**. See 2026-09-10 section. Do not use `<12` anymore.

---

*Last Updated: 2026-09-10b (full inventory)*
