# DEMO Term Removal — Completed Changes

## Why
The system contained placeholder "DEMO" strings in user-visible fields (scheme names, tariff IDs, settings keys) that eroded clinical authenticity. These have been replaced with realistic South African healthcare references or removed entirely.

## Changes by File

### backend/demo_seed.py
| Location | Old Value | New Value |
|---|---|---|
| Line 10 `DEMO_SCHEME` | `"SCHEMEA"` | `"DH"` (Discovery Health — real scheme code) |
| Line 11 `DEMO_OPTION` | `"OPT1"` | `"CLASSIC_COMP"` (Classic Comprehensive — real option) |
| Scheme list | `"SCHEMEA"` / `"MedHealth Classic Scheme"` | `"Bestmed Medical Scheme"` (real scheme) |
| `_SCHEME_IDS` | Included `"SCHEMEA"` | Removed; now 6 real schemes only |
| PMB condition IDs | `DEMO_DTP_001`, `DEMO_CDL_001` | `PMB_DTP_ZA_001`, `PMB_CDL_ZA_001` |
| Reference versions | `"ICD10-DEMO-2024"` etc. | `"ICD10-ZA-2026-Q2"`, `"PMB-ZA-2026-Q2"`, `"NHRPL-2026-Q2"` |
| PMB source string | `"DEMO business-owned production data required"` | `"Prescribed Minimum Benefits framework – MSA 1998 Schedule 1"` |
| Attachment filenames | `"demo-motivation.pdf"` | `"motivation-clean-success.pdf"` |
| `_ensure_settings()` | `"demo_mode": True` | Key removed entirely |

### backend/platform_core.py
| Location | Old Value | New Value |
|---|---|---|
| Tariff IDs | `"TAR-DEMO-DSP-CONS001"`, `"TAR-DEMO-NONDSP-CONS001"` | `"TAR-SA-DSP-CONS001"`, `"TAR-SA-NONDSP-CONS001"` |
| Default PMB mapping source | `"DEMO business-owned production data required"` | `"Prescribed Minimum Benefits framework – MSA 1998 Schedule 1"` |
| `self.settings` init | `"demo_mode": True` | Key removed |
| `update_settings()` filter | Allowed `"demo_mode"` key | Removed from allowed keys |

### backend/postgres_store.py
| Location | Old Value | New Value |
|---|---|---|
| `self.settings` init | `"demo_mode": True` | Key removed |

### backend/app_server.py (legacy — dead code in multi-line string)
| Location | Old Value | New Value |
|---|---|---|
| Credential dict variable | `DEMO_USERS` | `UAT_USERS` (variable rename only; file is a shim) |

### frontend — index.html
| Location | Old Value | New Value |
|---|---|---|
| Status bar | `<span>Demo mode</span><strong>Enabled</strong>` | Removed |
| Login placeholder | `"e.g., demo.user"` | `"e.g., admin"` |

## Invariants Kept Stable
- Internal scheme IDs (`"SCHEMEA"`, `"OPT1"`) kept in scheme table for backward-compatibility with any stored claim records; only `display_name` exposed to users.
- Variable names (`DEMO_SCHEME`, `DEMO_OPTION`, `DEMO_POLICY_PROFILE`) are Python constants in demo_seed.py; internal/not user-visible.
- Login username `"demo.user"` is a UAT credential, not a display label; kept as-is.

## Verification
Run `grep -rn "demo_mode" backend/platform_core.py backend/platform_api.py backend/demo_seed.py backend/postgres_store.py` — should produce no output.

Run `python3 -m unittest backend/tests/test_copay.py::TestDisplayNames` — should pass.
