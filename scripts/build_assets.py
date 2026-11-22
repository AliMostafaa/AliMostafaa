#!/usr/bin/env python3
"""
Build the README's SVG assets for both GitHub color schemes.

Design tokens, copy and character geometry mirror alimostafa.me:
  - lib/tokens.ts + app/globals.css  -> palette, radii, grain
  - lib/content.ts                   -> tagline, meta pairs, stack, hero words
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
    surface="#f5f5f4", face="#efefed", body="#1f1f1f",
    glass=(0.32, 0.06), shadow=0.30,
)
DARK = dict(
    bg="#0e0e0d", ink="#f2f2f0", muted="#9b9b97", line="#2b2b28",
    surface="#161615", face="#1f1f1f", body="#efefed",
    glass=(0.16, 0.04), shadow=0.55,
)
ORANGE = "#ffa31e"   # character orange — fixed brand ink
CHARCOAL = "#1f1f1f" # --color-charcoal — never flips
GREEN = "#79dd00"    # availability dot
WHITE = "#ffffff"

# ── Copy (lib/content.ts) ───────────────────────────────────────────────────
NAME = "Ali Mostafa"
SUB = "SOFTWARE ENGINEER & DESIGNER"
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
HERO_WORDS = ["MAKES", "YOU", "GO", "WOW!"]  # lib/content.ts HERO_WORDS
STACK_ROW_1 = ["Next.js", "React", "TypeScript", "Tailwind CSS", "Framer Motion", "Lenis"]
STACK_ROW_2 = ["Node.js", "Figma", "Shopify", "Vercel", "Flutter", "Supabase"]
WORDMARK = "alimostafa.me"

# Every glyph that appears in an SVG, per family — feeds pyftsubset.
CABINET_TEXT = "".join(HERO_WORDS + [NAME, WORDMARK])
SATOSHI_TEXT = "".join(
    [TAGLINE, SUB] + [p for pair in META for p in pair] + STACK_ROW_1 + STACK_ROW_2
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
    g1, g2 = theme["glass"]
    return f"""<defs>
{STYLE.format(faces="\n".join(faces))}
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" stitchTiles="stitch"/>
</filter>
<filter id="shadow" x="-25%" y="-25%" width="150%" height="175%">
  <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#000" flood-opacity="{theme['shadow']}"/>
</filter>
<filter id="pshadow" x="-40%" y="-40%" width="180%" height="180%">
  <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.28"/>
</filter>
<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#fff" stop-opacity="{g1}"/>
  <stop offset="0.45" stop-color="#fff" stop-opacity="{g2}"/>
  <stop offset="1" stop-color="#fff" stop-opacity="0.02"/>
</linearGradient>
<clipPath id="pfp"><circle cx="100" cy="100" r="100"/></clipPath>
</defs>"""


def grain(w: int, h: int) -> str:
    return f'<rect width="{w}" height="{h}" filter="url(#grain)" opacity="0.10"/>'


# ── Rough advance-width estimators (iterate visually against previews) ──────
def est_cabinet(text: str, size: float) -> float:
    return len(text) * size * 0.64


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
    W, H, PAD = 1280, 672, 56

    # Hero word blocks — row of rounded blocks, charcoal + orange "WOW!"
    BY, BH, GAP, FS, R = 200, 248, 16, 96, 40
    avail = W - 2 * PAD - GAP * (len(HERO_WORDS) - 1)
    est = [est_cabinet(w, FS) + 72 for w in HERO_WORDS]
    scale = avail / sum(est)
    xs, x = [], float(PAD)
    for e in est:
        xs.append((x, e * scale))
        x += e * scale + GAP

    blocks = []
    for i, (word, (bx, bw)) in enumerate(zip(HERO_WORDS, xs)):
        fill = ORANGE if word == "WOW!" else CHARCOAL
        blocks.append(f"""<g>
<rect x="{bx:.1f}" y="{BY}" width="{bw:.1f}" height="{BH}" rx="{R}" fill="{fill}"/>
<rect x="{bx:.1f}" y="{BY}" width="{bw:.1f}" height="{BH}" rx="{R}" fill="url(#glass)"/>
<text class="display" x="{bx + bw / 2:.1f}" y="{BY + BH / 2 + FS * 0.35:.1f}"
  font-size="{FS}" letter-spacing="-2.9" fill="{WHITE}"
  text-anchor="middle">{esc(word)}</text></g>""")

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
        cols.append(f"""<text x="{cx:.1f}" y="584" font-size="19" font-weight="500"
  fill="{t['ink']}">{esc(label)}</text>
<text x="{cx:.1f}" y="614" font-size="19" font-weight="500"
  fill="{t['muted']}">{esc(value)}</text>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
  viewBox="0 0 {W} {H}" role="img" aria-label="{esc(NAME)} — {esc(TAGLINE)}">
{defs(t, True, True)}
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
{avatar(t, PAD, 48, 88)}
<text class="display" x="164" y="86" font-size="40" letter-spacing="-1"
  fill="{t['ink']}">{esc(NAME)}</text>
<text class="mono" x="164" y="118" font-size="13" fill="{t['muted']}">{esc(SUB)}</text>
{pill}
<g filter="url(#shadow)">{"".join(blocks)}</g>
<text x="{PAD}" y="508" font-size="25" font-weight="500"
  fill="{t['ink']}">{esc(TAGLINE)}</text>
<line x1="{PAD}" y1="546" x2="{W - PAD}" y2="546" stroke="{t['line']}" stroke-width="1"/>
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
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
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
