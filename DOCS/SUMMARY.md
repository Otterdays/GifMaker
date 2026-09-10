<!-- PRESERVATION RULE: Never delete or replace content. Append or annotate only. -->

# Gif-Maker Project Summary

*Last Updated: 2026-09-10* [AMENDED: simplified timing UX → v1.0.9]

## Quick Links

- [ARCHITECTURE](ARCHITECTURE.md) - System design, data flow
- [STYLE_GUIDE](STYLE_GUIDE.md) - Coding conventions
- [SBOM](SBOM.md) - Security/package tracking
- [SCRATCHPAD](SCRATCHPAD.md) - Active tasks, blockers
- [CHANGELOG](CHANGELOG.md) - Version history (canonical under DOCS/)
- [tests/](../tests/) - Unit tests (`python -m pytest tests/`)
- [AGENTS](../AGENTS.md) - Agent entrypoint / doc map

---

## Project Overview

**Gif-Maker V1.0** is a professional Python GUI application for creating high-quality animated GIFs from screen recordings. Built with tkinter, pyautogui, and Pillow.

### Core Mission
Transform multi-tool GIF creation into a single, intuitive application.

## Key Achievements

- **Visual Region Selection**: Custom overlay system, reliable across platforms
- **Research-Based Quality**: Optimal settings via 20+ algorithm tests
- **Multi-threaded Architecture**: Responsive UI during all operations

## Technical Stack

- Python 3.8+ | tkinter | pyautogui | Pillow (>=12.3.0) | threading | pytest (dev)

## Project Structure

```
GifMaker/
├── gif_maker/            # Main application package (gui/, core/, utils/)
├── tests/                # Unit tests
├── requirements.txt
├── pyproject.toml
├── install.bat / launch.bat
├── AGENTS.md             # Agent / contributor entry
├── DOCS/
│   ├── SUMMARY.md        # This file (canonical)
│   ├── SBOM.md           # Package security
│   ├── SCRATCHPAD.md     # Active tasks
│   ├── CHANGELOG.md      # Version history (canonical)
│   ├── ARCHITECTURE.md
│   └── STYLE_GUIDE.md
├── README.md
├── SUMMARY.md            # Legacy pointer → DOCS/SUMMARY.md
└── SCRATCHPAD.md         # Legacy pointer → DOCS/SCRATCHPAD.md
```

## Current Status

- **Version**: 1.0.9
- **Status**: Production Ready (simplified timing UX 2026-09-10)
- **Platform**: Windows (primary), macOS/Linux compatible
- **Tests**: 62 unit tests (`python -m pytest tests/`) — last run: all pass
- **Security**: Pillow pin raised to `>=12.3.0,<13`; `pip-audit` clean on direct deps
- **SBOM**: Full inventory pass 2026-09-10b (transitive versions/licenses + audit how-to) — see [SBOM.md](SBOM.md)

### [AMENDED 2026-09-10] Simplified timing (v1.0.9)
- Capture rate + Playback feel (true 1× Match recording); quality engine still drives look
- Prior: P2 complete in v1.0.8 (cancel encode, Pick Window)

### [AMENDED 2026-09-10] P2 complete (v1.0.8)
- Cancel mid-encode; Pick Window (pygetwindow); explicit `pygetwindow` pin
- Prior partial (v1.0.7): settings persist, version SSOT, region_math/tests

### [AMENDED 2026-09-10] P2 polish partial (v1.0.7)
- Persist region/settings (`~/.gifmaker/settings.json`); UI version SSOT; region_math helpers
- New tests: settings_store, region_math, image_utils / quality paths
- Deferred: cancel mid-encode, real window picker *[AMENDED: shipped in 1.0.8]*

### [AMENDED 2026-09-10] P0 reliability (v1.0.5)
- Frame-list lock/snapshot; atomic GIF save; overwrite confirm; safe window close
- New tests: `tests/test_gif_creator.py`

### [AMENDED 2026-09-10] Audit snapshot
- Package layout from v1.0.3 intact; `pyproject.toml` version was stale at 1.0.1 → aligned to 1.0.4
- Root `CHANGELOG.md` had been removed; canonical changelog is `DOCS/CHANGELOG.md`
- Largest module: `gui/main_window.py` (~1397 lines) — split still optional

---

*Previous content preserved in root SUMMARY.md*
