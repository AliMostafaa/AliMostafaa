#!/usr/bin/env python3
"""
Build the README's SVG assets for both GitHub color schemes.

Design tokens, copy and character geometry mirror alimostafa.me:
  - lib/tokens.ts + app/globals.css  -> palette, radii, grain
  - lib/content.ts                   -> tagline, meta pairs, stack
  - components/sections/About.tsx    -> character avatar (disc/head/body)
  - app/globals.css `.label`         -> uppercase mono eyebrows/pills

Fonts (Satoshi + Cabinet Grotesk, OFL) are subset to the glyphs actually used
and embedded as base64 woff2, so every SVG is self-contained — GitHub serves
README images through camo and cannot fetch external resources.

Usage:  python3 scripts/build_assets.py
Output: assets/header-{light,dark}.svg   assets/stack-{light,dark}.svg
        assets/wordmark-{light,dark}.svg
"""

from __future__ import annotations

import base64
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"
BUILD = ROOT / ".build"

# ── Palette (app/globals.css @theme + [data-theme="dark"]) ──────────────────
LIGHT = dict(
    bg="#f4f4f3", ink="#0a0a0a", muted="#767674", line="#e2e2e0",
    surface="#f5f5f4", face="#efefed", body="#1f1f1f", stack_bg="#FFF",
)
DARK = dict(
    bg="#0e0e0d", ink="#f2f2f0", muted="#9b9b97", line="#2b2b28",
    surface="#161615", face="#1f1f1f", body="#efefed", stack_bg="#0D1117",
)
ORANGE = "#ffa31e"   # character orange — fixed brand ink
GREEN = "#79dd00"    # availability dot

# ── Copy (lib/content.ts) ───────────────────────────────────────────────────
NAME = "Ali Mostafa"
PILL = "AVAILABLE FROM JUNE 2026"
TAGLINE = (
    "Software Engineer & Designer · KairoDev Founder · "
    "50+ Projects · Egypt · Working Globally"
)
META = [
    ("Egypt Based", "Working Globally"),
    ("Building At", "KairoDev"),
    ("Availability", "June 2026"),
]
STACK_ROW_1 = ["Next.js", "React", "TypeScript", "Tailwind CSS", "Framer Motion", "Lenis"]
STACK_ROW_2 = ["Node.js", "Figma", "Shopify", "Vercel", "Flutter", "Supabase"]
WORDMARK = "alimostafa.me"

# Every glyph that appears in an SVG, per family — feeds pyftsubset.
CABINET_TEXT = NAME + WORDMARK
SATOSHI_TEXT = "".join(
    [TAGLINE] + [p for pair in META for p in pair] + STACK_ROW_1 + STACK_ROW_2
)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Font subsetting + embedding ─────────────────────────────────────────────
def subset(src: str, text: str, dst: pathlib.Path) -> None:
    subprocess.run(
        [
            "pyftsubset", str(FONTS / src),
            f"--text={text}",
            "--layout-features=*",
            "--flavor=woff2",
            f"--output-file={dst}",
        ],
        check=True, capture_output=True,
    )


def b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def font_face(name: str, data: str) -> str:
    return (
        f"@font-face{{font-family:'{name}';"
        f"src:url(data:font/woff2;base64,{data}) format('woff2');"
        f"font-weight:100 900;font-style:normal}}"
    )


STYLE = """<style>
{faces}
text{{font-family:'Satoshi',system-ui,sans-serif}}
.display{{font-family:'Cabinet Grotesk','Satoshi',sans-serif;font-weight:700}}
.mono{{font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
  font-weight:600;letter-spacing:0.08em}}
</style>"""


def defs(theme: dict, cabinet: bool, satoshi: bool) -> str:
    faces = []
    if cabinet:
        faces.append(font_face("Cabinet Grotesk", b64(BUILD / "cabinet.woff2")))
    if satoshi:
        faces.append(font_face("Satoshi", b64(BUILD / "satoshi.woff2")))
    return f"""<defs>
{STYLE.format(faces="\n".join(faces))}
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" stitchTiles="stitch"/>
</filter>
<filter id="pshadow" x="-40%" y="-40%" width="180%" height="180%">
  <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.28"/>
</filter>
<clipPath id="pfp"><circle cx="100" cy="100" r="100"/></clipPath>
</defs>"""


def grain(w: int, h: int) -> str:
    return f'<rect width="{w}" height="{h}" filter="url(#grain)" opacity="0.10"/>'


# ── Rough advance-width estimators (iterate visually against previews) ──────
def est_satoshi(text: str, size: float) -> float:
    return len(text) * size * 0.545


def est_mono(text: str, size: float) -> float:
    return len(text) * (size * 0.60 + size * 0.08)


# ── Character avatar (components/sections/About.tsx, viewBox 0 0 200 200) ──
def avatar(t: dict, x: float, y: float, size: float) -> str:
    s = size / 200
    return f"""<g transform="translate({x},{y}) scale({s:.4f})" filter="url(#pshadow)">
<circle cx="100" cy="100" r="100" fill="{t['face']}"/>
<g clip-path="url(#pfp)">
  <ellipse cx="100" cy="210" rx="80" ry="76" fill="{t['body']}"/>
  <circle cx="100" cy="84" r="40" fill="{ORANGE}"/>
</g></g>"""


# ── Header ──────────────────────────────────────────────────────────────────
def header(t: dict) -> str:
    W, H, PAD = 1280, 480, 56

    # Availability pill (top-right)
    pw = 24 + 12 + 10 + est_mono(PILL, 12.5) + 26
    px, py, ph = W - PAD - pw, 70, 44
    pill = f"""<g>
<rect x="{px:.1f}" y="{py}" width="{pw:.1f}" height="{ph}" rx="{ph / 2}"
  fill="none" stroke="{t['line']}" stroke-width="1.5"/>
<circle cx="{px + 24:.1f}" cy="{py + ph / 2}" r="6" fill="{GREEN}"/>
<text class="mono" x="{px + 44:.1f}" y="{py + ph / 2 + 4.5:.1f}" font-size="12.5"
  fill="{t['ink']}">{PILL}</text></g>"""

    # Meta pairs (chrome/MetaBar.tsx — label ink, value muted)
    cols = []
    col_w = (W - 2 * PAD) / 3
    for i, (label, value) in enumerate(META):
        cx = PAD + i * col_w
        cols.append(f"""<text x="{cx:.1f}" y="392" font-size="19" font-weight="500"
  fill="{t['ink']}">{esc(label)}</text>
<text x="{cx:.1f}" y="424" font-size="19" font-weight="500"
  fill="{t['muted']}">{esc(value)}</text>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
  viewBox="0 0 {W} {H}" role="img" aria-label="{esc(NAME)} — {esc(TAGLINE)}">
{defs(t, True, True)}
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
{avatar(t, PAD, 48, 88)}
{pill}
<text class="display" x="{PAD}" y="252" font-size="116" letter-spacing="-3.5"
  fill="{t['ink']}">{esc(NAME)}</text>
<text x="{PAD}" y="310" font-size="25" font-weight="500"
  fill="{t['ink']}">{esc(TAGLINE)}</text>
<line x1="{PAD}" y1="350" x2="{W - PAD}" y2="350" stroke="{t['line']}" stroke-width="1"/>
{"".join(cols)}
{grain(W, H)}
</svg>"""


# ── Stack strip ─────────────────────────────────────────────────────────────
def stack(t: dict) -> str:
    W, H, PAD, GAP = 1280, 200, 56, 14
    rows = []
    for row_i, row in enumerate([STACK_ROW_1, STACK_ROW_2]):
        y = 32 + row_i * 80
        x = float(PAD)
        for chip in row:
            w = est_satoshi(chip, 20) + 56
            rows.append(f"""<g>
<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="56" rx="28"
  fill="none" stroke="{t['line']}" stroke-width="1.5"/>
<text x="{x + w / 2:.1f}" y="{y + 35}" font-size="20" font-weight="500"
  fill="{t['ink']}" text-anchor="middle">{esc(chip)}</text></g>""")
            x += w + GAP
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
  viewBox="0 0 {W} {H}" role="img" aria-label="Tech stack">
{defs(t, None, SATOSHI_TEXT)}
<rect width="{W}" height="{H}" fill="{t['stack_bg']}"/>
{"".join(rows)}
{grain(W, H)}
</svg>"""


# ── Footer wordmark (components/sections/Footer.tsx — giant alimostafa.me) ──
def wordmark(t: dict) -> str:
    W, H = 1280, 240
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
  viewBox="0 0 {W} {H}" role="img" aria-label="{WORDMARK}">
{defs(t, CABINET_TEXT, None)}
<rect width="{W}" height="{H}" fill="{t['surface']}"/>
<text class="display" x="{W / 2}" y="196" font-size="214" letter-spacing="-9"
  fill="{t['ink']}" text-anchor="middle">{WORDMARK}</text>
{grain(W, H)}
</svg>"""


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    subset("CabinetGrotesk-Variable.woff2", CABINET_TEXT, BUILD / "cabinet.woff2")
    subset("Satoshi-Variable.woff2", SATOSHI_TEXT, BUILD / "satoshi.woff2")

    OUT.mkdir(exist_ok=True)
    for name, theme in (("light", LIGHT), ("dark", DARK)):
        for stem, fn in (("header", header), ("stack", stack), ("wordmark", wordmark)):
            path = OUT / f"{stem}-{name}.svg"
            path.write_text(fn(theme), encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
