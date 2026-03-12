# Gif-Maker Software Bill of Materials (SBOM)

*Security tracking - update on every package install/remove*

## 2025-03-12 - Initial SBOM

| Package | Version | Purpose | License | Audit |
|---------|---------|---------|---------|-------|
| pyautogui | 0.9.54 | Screenshot capture, mouse control | BSD-3-Clause | OK |
| Pillow | >=10.4.0,<12 | Image processing, GIF creation | HPND | OK |

## Dependencies ( transitive )

- **pyautogui** pulls: pyscreeze, pygetwindow, pytweening, pymsgbox (Windows)
- **Pillow** pulls: none (optional: libjpeg, zlib for formats)

## Audit Notes

- Pillow 11.0.0: Security updates over 10.0.1, Python 3.8+ supported
- pyautogui 0.9.54: Latest stable, cross-platform

---

*Last Updated: 2025-03-12*
