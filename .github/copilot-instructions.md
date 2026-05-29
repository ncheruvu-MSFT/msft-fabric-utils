# Copilot Instructions — Content Posting Workspace

## Draw.io Diagram Dark Background Theme (MANDATORY)

ALL `.drawio` diagrams created in this workspace MUST use the dark background theme. Never use a white/light background.

### Color Palette

| Element | Color | Notes |
|---------|-------|-------|
| Page background | `#16213e` | Set on `<mxGraphModel>` `background` attr |
| Canvas rounded rect | `fillColor=#1a1a2e;strokeColor=#2a2a4a` | Full-page rect behind all content |
| Title text | `fontColor=#FFFFFF` | White on dark |
| Subtitle text | `fontColor=#88AADD` | Light blue |
| Body/flow text | `fontColor=#CCCCDD` | Light gray |
| Edge label background | `labelBackgroundColor=#1a1a2e` | Matches canvas |

### Section Backgrounds (Architectural Tiers)

Each diagram must have tinted rounded-rect backgrounds behind logical sections:

| Section | Fill | Stroke | Label Color |
|---------|------|--------|-------------|
| Application Tier | `#0d1b3e` | `#1565C0` | `#4488CC` |
| Service Layer | `#1a0d2e` | `#7B1FA2` | `#BB88DD` |
| Azure Platform | `#0d1a2e` | `#283593` | `#6688BB` |
| Governance | `#0d2e1a` | `#2E7D32` | `#66BB88` |
| Pipeline | `#1a0d3e` | `#6644AA` | `#AA88DD` |
| Generation | `#2e0d1a` | `#C62828` | `#DD8888` |

### Edge Colors (Brightened for Dark Background)

| Flow Type | Stroke | Label Font |
|-----------|--------|------------|
| Data Flow | `#4499DD` | `#88BBEE` |
| Auth Flow | `#55BB66` | `#88DD99` |
| Cert Flow | `#BB88DD` | `#CC99EE` |
| Error Flow | `#FF5555` | `#FF8888` |

### Implementation Reference

- `src/drawio-bridge.js` — `LAYOUT_RULES.darkTheme` object contains all colors programmatically
- `skills/SKILL.md` — Rule 11 documents the full convention
- Section background rects must appear FIRST in XML (z-order: behind content)
