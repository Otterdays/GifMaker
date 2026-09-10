<!-- PRESERVATION RULE: Never delete or replace content. Append or annotate only. -->

# Gif-Maker Development Scratchpad

*Active tasks, blockers, last 5 actions - NEVER delete, compact at 500 lines*

## 2026-09-10 Session (SBOM inventory — docs agent)

### Claim (parallel-safe)
- **DOCS/SBOM.md (+ light SUMMARY/SCRATCHPAD/AGENTS)** only — no `gif_maker/` / `tests/`
- P0/P1 agents: no conflict expected

### Active Tasks
- [x] Full transitive inventory + licenses
- [x] Document correct `pip-audit -r` vs whole-env noise
- [x] Flag GPLv3+ transitive (`mouseinfo`, `pymsgbox`)
- [x] Note v1.0.5 = code bump, deps same as 1.0.4 security floor

### Last 5 Actions
1. Appended `2026-09-10b` SBOM section
2. Reconfirmed `pip-audit -r requirements.txt` clean
3. SUMMARY security line + inventory pointer
4. Left code to P0/P1

### Blockers
- None

---

## 2026-09-10 Session (P1 reliability / UX — agent A)

### Claim (parallel-safe)
- Working **P1 only** — leave P0 encode/atomic + P2 settings/region_math alone
- Touched: `gui/main_window.py` (surgical), `core/constants.py`, README shortcuts, ARCHITECTURE amend, CHANGELOG 1.0.6
- Synced `gif_maker/version.py` → **1.0.6** (P2 SSOT; was stale 1.0.4)

### Active Tasks
- [x] Escape on region overlay: `focus_force` + `bind_all` Escape
- [x] UI-thread `time.sleep` → `root.after` (start record / browser size)
- [x] Preview O(n²): append one thumb, not rebuild all
- [x] Remap clear shortcut Ctrl+C → Ctrl+Shift+Delete
- [x] Capture fail soft-continue: abort after N consecutive fails + FAILSAFE tip
- [x] Align ARCHITECTURE ↔ screenshot lock reality

### Last 5 Actions
1. Claimed P1; left P0/P2 files alone where possible
2. Esc overlay + after delays + preview append + clear remap + fail abort
3. constants: `WINDOW_HIDE_DELAY_MS`, `MAX_CAPTURE_FAILURES`
4. Docs: CHANGELOG 1.0.6, ARCHITECTURE P1 amend, README shortcuts
5. pytest: **45 passed**; version SSOT synced

### Blockers
- None

### Next Steps
- Manual smoke: region Escape, record preview append, clear shortcut
- Other agents: rebase on main_window if still editing

---

## 2026-09-10 Session (P0 reliability — shipped)

### Claim
- Owner: this agent — **P0 done** (`gif_creator` atomic + `main_window` lock/snapshot/close)
- P1/P2 agents: watch merge conflicts on `main_window.py`

### Active Tasks
- [x] Lock/snapshot `screenshots`; disable Clear/Delete while busy
- [x] Atomic GIF save + overwrite confirm
- [x] `WM_DELETE_WINDOW` → `on_close`
- [x] `tests/test_gif_creator.py` — 24 tests pass; version **1.0.5**

### Last 5 Actions
1. `_atomic_save` in `gif_creator.py`
2. `_encoding_active` / `_snapshot_screenshots` / `_set_mutate_controls` / `on_close`
3. Encode worker takes frame snapshot
4. Docs CHANGELOG/SUMMARY/ARCHITECTURE; version bump
5. pytest: 24 passed

### Next Steps (for P1 agent)
- Escape overlay, UI sleep→after, preview O(n²), Ctrl+C remap — rebase on P0 lock helpers

---

## 2026-09-10 Session (P1 reliability / UX — agent A)

### Claim (parallel-safe)
- Working **P1 only** — leave P0 (race / RAM / corrupt GIF / DPI) and P2 for other agent
- Touch: `gui/main_window.py`, `core/constants.py`, shortcut docs, ARCHITECTURE amend if lock wording drift

### Active Tasks
- [ ] Escape on region overlay: `focus_force` + `bind_all` Escape
- [ ] UI-thread `time.sleep` → `root.after` (start record / browser size)
- [ ] Preview O(n²): append one thumb, not rebuild all
- [ ] Remap clear shortcut Ctrl+C → Ctrl+Shift+Delete
- [ ] Capture fail soft-continue: abort after N consecutive fails + FAILSAFE tip
- [ ] Align ARCHITECTURE ↔ screenshot lock reality

### Last 5 Actions
1. Claimed P1 slice (avoid overlap with parallel agent on P0/gif_creator)
2. (in progress)

### Blockers
- None — coordinate via this claim block

### Next Steps
- Surgical edits in main_window; no big refactor

---

## 2026-09-10 Session (P2 polish — agent A, light touch)

### Claim (avoid clash with other agents on P0/P1 / encode)
- Owner: this agent — **P2 only**, leave cancel-encode (#12) + window-picker (#13) alone (heavy `main_window`)
- [ ] P2#14 UI version string → `__version__` (pyproject already 1.0.4)
- [ ] P2#11 Persist last region/settings (`utils/settings_store.py` + light GUI hooks)
- [ ] P2#15 Tests: `make_thumbnail`, region math, settings_store (skip rewriting other agent's `test_gif_creator.py`)
- Deferred: #12 cancel mid-encode, #13 real window picker

### Last 5 Actions
1. Claimed P2 narrow scope (no encode cancel / window picker)
2. (in progress)

---

## 2026-09-10 Session (Project audit + SBOM)

### Active Tasks
- [x] Full project audit (code layout, deps, tests, docs drift)
- [x] Security bump Pillow → `>=12.3.0,<13` (pip-audit clean)
- [x] Sync version to **1.0.4** (`pyproject.toml`, `__version__`)
- [x] Refresh SBOM / SUMMARY / SCRATCHPAD / CHANGELOG / README links
- [x] Add root `AGENTS.md` (was missing)
- [ ] Optional: split `gui/main_window.py` (1397 lines; over 400-line guideline)
- [ ] Optional: project venv (avoid host streamlit/Pillow pin clash)

### Last 5 Actions
1. Ran pytest: **20 passed**; Python 3.13.15
2. pip-audit: old `<12` pin → 35 vulns; new `12.3.0` pin → clean
3. Bumped deps + set package version 1.0.4
4. Updated DOCS (SBOM, SUMMARY, SCRATCHPAD, CHANGELOG) + root pointers
5. Fixed CHANGELOG path drift (canonical = `DOCS/CHANGELOG.md`)

### Audit verdict
- **Status**: Production-ready package layout (v1.0.3 work) still sound
- **Blocker cleared**: vulnerable Pillow upper bound
- **Docs drift**: SUMMARY/SCRATCHPAD last touch 2025-03; pyproject still said 1.0.1; root CHANGELOG deleted vs README link — fixed this session

### Out-of-Scope Observations
- `gif_maker/gui/main_window.py` ~1397 lines (monolith GUI; region overlay + recording still coupled)
- No CI workflow in repo
- Root `SUMMARY.md` / `SCRATCHPAD.md` are legacy mirrors — DOCS/ is canonical

### Blockers
- None

### Next Steps
- Prefer `python -m venv .venv` then `pip install -e ".[dev]"` for clean deps
- Consider splitting main_window (preview / region / recorder) if next feature lands
- Re-run `python -m pip_audit -r requirements.txt` after any dep change

---

## 2025-03-19 Session (Docs Refresh)

### Last 5 Actions
1. Added PRESERVATION RULE header to all DOCS
2. Updated SUMMARY: version 1.0.3, tests link, Python 3.8+
3. Updated ARCHITECTURE with [AMENDED] package structure
4. Updated STYLE_GUIDE import example for package
5. Updated README: Testing section, version 1.0.3

---

## 2025-03-19 Session (Modernization)

### Active Tasks
- [x] Add pytest unit tests (validate_settings_logic, estimate_gif_size_logic, parse_speed_frame_duration, parse_quality_params)
- [x] Split gif_maker.py into package (gui/, core/, utils/)
- [x] Modernize packaging (pyproject.toml entrypoint)

### Last 5 Actions
1. Added tests/test_settings_logic.py with 20 unit tests
2. Added pyproject.toml with pytest config and gif-maker console script
3. Extracted validate_settings_logic and estimate_gif_size_logic as pure helpers
4. All 20 tests pass

### Test Targets
- validate_settings_logic, estimate_gif_size_logic, parse_speed_frame_duration, parse_quality_params

---

## 2025-03-12 Session

### Active Tasks
- [x] Docs update (SUMMARY, SBOM, SCRATCHPAD in DOCS)
- [x] Modernize dependencies (Pillow 11.x)
- [x] Code review fixes (duplicates, quality check, constants)
- [x] Minor refactoring + GUI improvements

### Last 5 Actions
1. Created DOCS/SBOM.md for security tracking
2. Created DOCS/SUMMARY.md, DOCS/SCRATCHPAD.md per user rules
3. Updated requirements.txt (Pillow 11.0.0)
4. Fixed start_recording duplicate code, quality check bug, added COLOR_BROWSE
5. GUI: ttk styling, improved spacing, Browse button constant

### Blockers
- None

### Next Steps
- Consider unit tests for validate_settings, estimate_gif_size
- Optional: modularization if codebase grows

---

## Previous Context (compact)

**Tech**: Python 3.7+, tkinter, pyautogui, Pillow, threading
**Architecture**: Single-file GIFMaker class, visual region overlay, multi-threaded recording/GIF creation
**Key breakthroughs**: Custom overlay (pyautogui crashes), quality paradox (lower=better gradients), root.after() for thread-safe UI
**Recent (Dec 2024)**: Type hints, constants, keyboard shortcuts, file size estimation, thread safety

---

*Compact at 500 lines. Last Updated: 2026-09-10*
