# UI Design System — MedHealth Billing Platform

## Typography
Font stacks (verbatim from code):
- --font-sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial
- --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New"

Scale: body 13–14px, labels 12px, h1 22px, h3 14px, h4 12px uppercase 0.4px tracking
Line height: 1.4–1.5 for body; 1.1 for headings

## Colour palette (verbatim hex — do not change)
| Token | Hex | Semantic use |
|---|---|---|
| --brand-900 | #0b3e5a | sidebar deep, hero BG base |
| --brand-800 | #0f567b | sidebar gradient end |
| --brand-700 | #13709f | links, active nav chip colour |
| --brand-600 | #0a86bd | primary button background |
| --brand-500 | #00a3d9 | accent highlight |
| --brand-200 | #cfefff | radial gradient fill, badge BG |
| --ink-900 | #0b1220 | body text, headings |
| --ink-700 | #2b3648 | secondary text, labels |
| --ink-500 | #55637a | muted text, placeholders |
| --line-200 | #e6edf5 | borders, dividers |
| --bg-50 | #f6f9fc | page background, mini-card fill |
| --card | #ffffff | card surface |
| --pass | #067647 | success semantic (from existing) |
| --fail | #b42318 | error semantic (from existing) |
| --warn | #b36b00 | warning semantic (from existing) |

## Status semantics (mapped from palette)
| Token | Value | Use |
|---|---|---|
| --color-success | #067647 | PASS, READY chips, toast success |
| --color-success-bg | #ecfdf5 | toast success background |
| --color-success-border | rgba(6,118,71,.35) | chip pass border |
| --color-warn | #b36b00 | WARN chips, toast warning |
| --color-warn-bg | #fffbeb | toast warning background |
| --color-warn-border | rgba(179,107,0,.35) | chip warn border |
| --color-error | #b42318 | FAIL, BLOCK chips, toast error |
| --color-error-bg | #fef2f2 | toast error background |
| --color-error-border | rgba(180,35,24,.35) | chip fail border |
| --color-info | #13709f | info chips, toast info |
| --color-info-bg | rgba(19,112,159,.06) | info background |
| --color-info-border | rgba(19,112,159,.35) | info border |

## Spacing (4-point scale)
--space-1: 4px | --space-2: 8px | --space-3: 12px | --space-4: 16px | --space-6: 24px | --space-8: 32px

## Shape
| Token | Value | Use |
|---|---|---|
| --radius | 18px | cards, drawers, hero |
| --radius-sm | 12px | chips, inputs, secondary cards |
| --radius-xs | 8px | tags, small badges, modals |
| --shadow | 0 10px 30px rgba(11,18,32,.08) | card elevation |
| --shadow-sm | 0 2px 8px rgba(11,18,32,.06) | chip hover, small elevations |

## Focus ring
--focus-ring: 0 0 0 3px rgba(10,134,189,.35)
Applied via :focus-visible on all interactive elements. Never remove focus indicators.

## Motion
| Token | Value | Use |
|---|---|---|
| --transition | 150ms ease | hover states, colour changes |
| --transition-slow | 220ms ease | drawer slide, toast appear/dismiss |

Rule: no animation on reduced-motion. Add @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } } in tokens.

## Component sizing standards
- Button: min-height 36px, padding 10px 16px, radius --radius-sm
- Chip: padding 3px 8px, radius 999px (pill), font-size 12px
- Input: padding 10px 12px, radius --radius-sm, border --line-200
- Table cell: padding 10px, font-size 13px
- Touch target: min 44×44px for mobile (applied via min-height on buttons)

## Accessibility rules
- All interactive elements: :focus-visible with --focus-ring
- Colour alone never the only status signal — always paired with text label
- Toasts: role="alert" for errors (assertive), role="status" for others (polite)
- Drawers: focus first interactive element on open; return focus to trigger on close; ESC to close
- ARIA live regions: toast-host has aria-live="polite" by default
