#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Thème Martinique (rouge, vert, noir) : panneaux en verre sombre (glass_panel),
3 tuiles en « liquid glass » (interrupteur GLASS), drapeau sur la tuile LIEU.
Polices : Instrument Serif, Geist, Geist Mono.

Every card is a standalone SVG shown through <img>, so it can only use what GitHub
allows there: inline CSS animations, SMIL and fonts embedded as data URIs (no JS,
no external requests). Fonts are subset WOFFs in fonts/ (SIL OFL).

Live numbers come from data/contributions.json (fetch_contributions.py).

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import base64
import datetime
import json
import math
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
PORTRAIT = os.path.join(ROOT, "chris-ascii.svg")
# serpent fabriqué par Platane/snk dans le workflow (dist/ n'est pas versionné)
SNAKE = os.path.join(ROOT, "dist", "serpent.svg")
# qui mange la grille « Chaque jour, en vert » :
#   "bonhomme" (mon perso, dessiné ici), "crabe" (dessiné ici) ou "serpent" (snk)
CHASSEUR = "bonhomme"
# effet sur le portrait du terminal : "aucun", "cendres", "hash", "matrix", "glitch"
#   ou "cendres+glitch" (le mélange)
EFFET = "cendres+glitch"
# barres des 12 mois : "une-a-une" (chaque barre monte avec un rebond + son chiffre)
#   ou "ensemble" (toutes montent presque en même temps, l'ancienne version)
BARRES = "une-a-une"
GH_USER = "CHRIISHEART"
MOIS = ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]


# ---- brand tokens -----------------------------------------------------------
PAPER = "#f3f3f1"
PAPER_DEEP = "#e2e2de"
INK = "#111111"
INK_SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
TECH = "#2f55ff"
STUDIO = "#ef3b2d"
LEARN = "#ffc81a"
# couleurs du drapeau de la Martinique (rouge-vert-noir) pour les 3 tuiles
# (haut, bas) : un léger dégradé, couleurs vives mais douces
MQ_RED = ("#ff4f3d", "#e8263d")
MQ_GREEN = ("#1fcf8a", "#0b9e6e")
MQ_BLACK = ("#24303a", "#141b22")
# effet « liquid glass » sur les 3 tuiles : True = verre, False = B Tropical simple
GLASS = False

# ---- thème Martinique pour les grands panneaux (grille, contributions, codes) --
MQ_TXT = "#f2f5f7"       # texte principal
MQ_SOFT = "#93a4b1"      # texte secondaire
MQ_LINE = "#2a3640"      # séparateurs
MQ_R = "#ff4f3d"         # rouge (accent)
MQ_G = "#1fcf8a"         # vert (accent)
MQ_EMPTY = "#1d2830"     # case vide de la grille
MQ_LEVELS = [MQ_EMPTY, "#16a06c", "#1fcf8a", "#4fe3a4", "#8ff3c6", "#c8ffe6"]


def glass_panel(w, h, rx=16):
    """Fond en verre sombre (comme la tuile MAKOO) + ruban rouge-vert en haut."""
    return f"""
<defs>
  <clipPath id="pc"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
  <linearGradient id="pbg" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#202a33"/><stop offset="1" stop-color="#11171d"/></linearGradient>
  <filter id="pb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
  <linearGradient id="pgl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <linearGradient id="prim" x1="0" y1="0" x2=".2" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".45"/>
    <stop offset=".3" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#fff" stop-opacity=".18"/></linearGradient>
  <linearGradient id="rib" x1="0" x2="1"><stop offset="0" stop-color="{MQ_R}"/><stop offset=".5" stop-color="{MQ_G}"/><stop offset="1" stop-color="{MQ_G}" stop-opacity="0"/></linearGradient>
</defs>
<g clip-path="url(#pc)">
  <rect width="{w}" height="{h}" fill="url(#pbg)"/>
  <g filter="url(#pb)">
    <circle cx="{w * 0.15:.0f}" cy="0" r="{min(h, 220)}" fill="{MQ_R}" opacity=".16">
      <animate attributeName="cx" values="{w * 0.15:.0f};{w * 0.3:.0f};{w * 0.15:.0f}" dur="14s" repeatCount="indefinite"/></circle>
    <circle cx="{w * 0.85:.0f}" cy="{h}" r="{min(h, 240)}" fill="{MQ_G}" opacity=".14">
      <animate attributeName="cx" values="{w * 0.85:.0f};{w * 0.7:.0f};{w * 0.85:.0f}" dur="16s" repeatCount="indefinite"/></circle>
  </g>
  <rect x="8" y="6" width="{w - 16}" height="{min(h * 0.4, 120):.0f}" rx="{rx - 4}" fill="url(#pgl)"/>
  <rect x="32" y="0" width="140" height="3" rx="1.5" fill="url(#rib)"/>
  <rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .75}" fill="none" stroke="url(#prim)" stroke-width="1.5"/>
</g>"""
W = 880  # full card width, GitHub's README column at 100%

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
@keyframes growb{0%{transform:scaleY(0)}65%{transform:scaleY(1.12)}82%{transform:scaleY(.96)}100%{transform:scaleY(1)}}
.gb{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:growb .7s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
@keyframes bubin{from{opacity:0;transform:translateY(6px) scale(.9)}to{opacity:1;transform:none}}
.bp{opacity:0;transform-box:fill-box;animation:bubin .35s cubic-bezier(.23,1,.32,1) both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.gb,.p,.bp,.live,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


GAP = 12          # gap between cards, baked into the SVGs (GitHub's own spacing is uneven)
BOTTOM = 12       # bottom padding per row, matching GAP
COL = W / 3       # each card in a row of three is exactly a third of the column


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    """Card of w x h drawn at x=left inside a transparent canvas, padded so rows tile exactly."""
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC"):  # preview: show every animation at its end state
        css += ".r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):  # animation delay attribute
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines)
    )


# ---- 1 · hero -----------------------------------------------------------------
def hero():
    h = 420
    src = open(PORTRAIT, encoding="utf-8").read()
    rows = re.findall(r'<text xml:space="preserve"[^>]*\by="([\d.]+)"[^>]*>(.*?)</text>', src, re.S)
    n = len(rows)
    portrait = []
    for i, (y, txt) in enumerate(rows):
        # rows "print" top to bottom like a slow terminal
        portrait.append(
            f'<text class="f" style="animation-delay:{0.25 + i * 0.018:.3f}s;animation-duration:.35s" '
            f'xml:space="preserve" x="20" y="{y}" fill="{INK}" font-size="7.2" '
            f'textLength="800" lengthAdjust="spacing">{txt}</text>'
        )
    s = 0.41
    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{TECH}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0"
      keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">ÉTUDIANT · MARTINIQUE</text>
</g>
<text class="r" {d(0.15)} x="44" y="190" font-family="{SERIF}" font-size="116" letter-spacing="-2.5" fill="{INK}">Chriis</text>
<text class="r" {d(0.3)} x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="116" letter-spacing="-2.5" fill="url(#shine)">Heart</text>
<g class="r" {d(0.55)}>
  {text_lines(48, 338, ["J'apprends à coder et je construis", "mes propres projets."], 27, f'font-family="{SANS}" font-size="18" fill="{INK_SOFT}"')}
</g>
<g class="f" {d(0.8)}>
  <text x="48" y="396" font-family="{MONO}" font-size="13" fill="{INK}">github.com/CHRIISHEART</text>
  <text class="nu" x="222" y="396" font-family="{MONO}" font-size="13" fill="{TECH}">&#8599;</text>
</g>
<g transform="translate(520 46) scale({s}) translate(-20 -37)" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
  {''.join(portrait)}
</g>
"""
    write("hero.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                          "Chriis Heart. Étudiant en Martinique. J'apprends à coder et je construis mes propres projets."))


# ---- 2 · world tiles ----------------------------------------------------------
TILE_W, TILE_H = 880 / 3 - 8, 210  # 285.33: two 12px gaps across the row


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    """Number counts up from 0 with SMIL <set> frames (works inside <img>), easing out."""
    m = re.match(r"([\d.]+)(.*)", num)
    val, suf = float(m.group(1)), m.group(2)
    dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    if os.environ.get("STATIC"):
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else f"{val * e:.{dec}f}{suf}"
        on = begin + dur * i / frames
        if i == frames:
            # final value: visible by default (readable without SMIL), hidden until the count ends
            out.append(f'<text x="{x}" y="{y}" {attrs} opacity="1">{escape(txt)}{tail}'
                       f'<set attributeName="opacity" to="0" begin="0s" end="{on:.3f}s"/></text>')
            continue
        off = f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(txt)}{tail}'
                   f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>')
    return "".join(out)


def mq_flag(x, y, w=54):
    """Drapeau de la Martinique (rouge-vert-noir) : triangle rouge côté mât,
    bande verte en haut, bande noire en bas."""
    h = w * 2 / 3
    return (f'<g transform="translate({x:.1f} {y:.1f})">'
            f'<clipPath id="flag"><rect width="{w}" height="{h:.1f}" rx="4"/></clipPath>'
            f'<g clip-path="url(#flag)">'
            f'<rect width="{w}" height="{h/2:.1f}" fill="#00a650"/>'
            f'<rect y="{h/2:.1f}" width="{w}" height="{h/2:.1f}" fill="#000000"/>'
            f'<path d="M0,0 L{w*0.5:.1f},{h/2:.1f} L0,{h:.1f} Z" fill="#e4002b"/></g></g>')


def tile(name, label, color, on, num, word, blurb, delay, pos, flag=False):
    # carte LIEU : le drapeau prend la place du gros texte
    # sans phrase : drapeau plus grand, centré au milieu de la carte
    flag_w = 108 if blurb else 150
    flag_y = 52 if blurb else (TILE_H - flag_w * 2 / 3) / 2
    big = (mq_flag((TILE_W - flag_w) / 2, flag_y, flag_w) if flag else
           count_up(num, word, 22, 112, f'font-family="{SERIF}" font-size="44" fill="{on}"', delay + 0.45))
    corner = (f'<g class="ai" {d(delay + 0.5)}><text class="n" style="animation-delay:{delay + 1.3:.2f}s" '
              f'x="250" y="38" font-family="{MONO}" font-size="14" fill="{on}">&#8594;</text></g>')
    glass = f"""
    <g filter="url(#lb)">
      <circle cx="60" cy="40" r="70" fill="#fff" opacity=".28">
        <animate attributeName="cx" values="60;120;60" dur="9s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="40;70;40" dur="11s" repeatCount="indefinite"/></circle>
      <circle cx="{TILE_W - 50}" cy="{TILE_H - 30}" r="80" fill="#000" opacity=".22">
        <animate attributeName="cx" values="{TILE_W - 50};{TILE_W - 110};{TILE_W - 50}" dur="10s" repeatCount="indefinite"/></circle>
    </g>
    <rect width="{TILE_W}" height="{TILE_H}" fill="url(#deep)"/>
    <rect x="6" y="5" width="{TILE_W - 12}" height="{TILE_H * 0.46:.1f}" rx="11" fill="url(#gloss)"/>
    <ellipse cx="70" cy="16" rx="58" ry="7" fill="url(#spec)" opacity=".8"/>""" if GLASS else ""
    rim = (f'<rect x=".75" y=".75" width="{TILE_W - 1.5}" height="{TILE_H - 1.5}" rx="13.5" fill="none" stroke="url(#rim)" stroke-width="1.5"/>'
           if GLASS else f'<rect x="0.5" y="0.5" width="{TILE_W - 1}" height="{TILE_H - 1}" rx="14" fill="none" stroke="#ffffff" stroke-opacity=".14"/>')
    lines = wrap(blurb, 34)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{150 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{on}" opacity=".92">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="{flag_y - 4 if flag else 62}" width="{TILE_W}" height="{flag_w * 2 / 3 + 8 if flag else 62}"/></clipPath>
  <linearGradient id="tg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="{color[0]}"/><stop offset="1" stop-color="{color[1]}"/></linearGradient>
  <!-- liquid glass : reflet, bord lumineux, profondeur -->
  <filter id="lb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>
  <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".42"/>
    <stop offset=".55" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <linearGradient id="rim" x1="0" y1="0" x2=".4" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".85"/>
    <stop offset=".35" stop-color="#fff" stop-opacity=".12"/><stop offset=".75" stop-color="#fff" stop-opacity=".06"/>
    <stop offset="1" stop-color="#fff" stop-opacity=".4"/></linearGradient>
  <linearGradient id="deep" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="#000" stop-opacity="0"/>
    <stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient>
  <radialGradient id="spec" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="url(#tg)"/>
    {glass}
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
    {rim}
  </g>
  <text class="sl" {d(delay + 0.35)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{on}">{label}</text>
  {corner}
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.45)}>
    {big}
  </g></g>
  {blurb_svg}
</g>
"""
    write(f"{name}.svg", svg(TILE_W, TILE_H, body, ["serif", "serif-i", "sans", "mono"],
                             f"{label}: {num} {word}. {blurb}", left=4 * pos, right=8 - 4 * pos))


# ---- 3 · activity (monthly bars) ------------------------------------------------
def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    une = BARRES == "une-a-une"
    step = 0.28 if une else 0.07          # écart entre deux barres
    rise = "gb" if une else "g"            # gb = montée avec rebond
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = "url(#barR)" if is_best else "url(#barG)"
        glow = ' filter="url(#glowR)"' if is_best else ""
        label = MOIS[int(m["month"][5:7]) - 1]
        t = 2.2 + i * step
        bars.append(
            f'<rect class="{rise}" style="animation-delay:{t:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="5" fill="{fill}"{glow}><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{t:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MQ_SOFT}">{label}</text>'
        )
        if is_best:
            t_best = (t + 0.6) if une else 3.2
            bars.append(
                f'<text class="p" style="animation-delay:{t_best:.2f}s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MQ_R}">{m["total"]:,}</text>'
            )
        elif une and m["total"] > 0:
            # petit chiffre qui apparaît au-dessus de la barre quand elle arrive
            bars.append(
                f'<text class="p" style="animation-delay:{t + 0.55:.2f}s" x="{x + bw / 2:.1f}" y="{base - bh - 8}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MQ_SOFT}">{m["total"]:,}</text>'
            )
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "série en cours, la plus longue" if cs >= ls else f"série en cours, record {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic" fill="{MQ_R}">jour{"s" if cs > 1 else ""}</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="{MQ_SOFT}"> / {total_days}</tspan>', "jours avec un commit"),
        (f'{data["best_day"]["count"]}', "le jour le plus actif"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{MQ_TXT}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MQ_SOFT}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{MQ_LINE}"/>')
    body = f"""
{glass_panel(W, h)}
<defs>
  <linearGradient id="barG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{MQ_G}"/><stop offset="1" stop-color="#0f6b4c"/></linearGradient>
  <linearGradient id="barR" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff7a5c"/><stop offset="1" stop-color="{MQ_R}"/></linearGradient>
  <filter id="glowR" x="-80%" y="-30%" width="260%" height="160%"><feGaussianBlur stdDeviation="7" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MQ_SOFT}">MES 12 DERNIERS MOIS SUR GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{MQ_TXT}">{data["total_contributions"]:,} <tspan font-style="italic" fill="{MQ_G}">contribution{"s" if data["total_contributions"] > 1 else ""}</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write("activity.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                              f'{data["total_contributions"]:,} contributions sur un an, série de {cs} jours'))


# ---- 4 · repo cards -----------------------------------------------------------
REPO_W, REPO_H = 880 / 2 - 6, 196
REPOS = [
    ("IDATE", "Drop soon.", "Code", MQ_R),
    ("idsherlock", "Drop soon.", "Code", MQ_G),
]



def icon_message(x, y, size=64):
    """Icône d'app « message » (bulle + points qui s'animent), dégradé rouge."""
    k = size / 64
    dots = "".join(
        f'<circle cx="{22 + i * 10}" cy="30" r="3.4" fill="#e8263d">'
        f'<animate attributeName="opacity" values=".25;1;.25" dur="1.2s" begin="{i * .2:.1f}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -2.5;0 0" dur="1.2s" begin="{i * .2:.1f}s" repeatCount="indefinite"/></circle>'
        for i in range(3))
    return f"""<g transform="translate({x} {y}) scale({k})">
  <defs><linearGradient id="icm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff6a5a"/><stop offset="1" stop-color="#e8263d"/></linearGradient></defs>
  <rect width="64" height="64" rx="15" fill="url(#icm)"/>
  <rect x="1" y="1" width="62" height="30" rx="14" fill="#fff" opacity=".12"/>
  <path d="M32,13 C45,13 53,20.5 53,30 C53,39.5 45,47 32,47 C29.5,47 27.2,46.7 25,46.1 C22.5,48.6 18.6,50.6 14,51 C16.3,48.6 17.6,46 17.9,43.2 C13.6,40.2 11,35.4 11,30 C11,20.5 19,13 32,13 Z" fill="#fff"/>
  {dots}
</g>"""


def icon_loupe(x, y, size=64):
    """Icône d'app « loupe » (enquête), dégradé vert, la loupe balaie doucement."""
    k = size / 64
    return f"""<g transform="translate({x} {y}) scale({k})">
  <defs><linearGradient id="icl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3ddc97"/><stop offset="1" stop-color="#0b9e6e"/></linearGradient></defs>
  <rect width="64" height="64" rx="15" fill="url(#icl)"/>
  <rect x="1" y="1" width="62" height="30" rx="14" fill="#fff" opacity=".12"/>
  <g><animateTransform attributeName="transform" type="rotate" values="-8 32 32;8 32 32;-8 32 32" dur="3s" repeatCount="indefinite"/>
    <circle cx="28" cy="28" r="12" fill="#fff" fill-opacity=".18" stroke="#fff" stroke-width="5"/>
    <line x1="37" y1="37" x2="48" y2="48" stroke="#fff" stroke-width="6.5" stroke-linecap="round"/>
    <path d="M21,24 A8,8 0 0 1 27,19" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity=".8"/></g>
</g>"""


REPO_ICONS = {"IDATE": icon_message, "idsherlock": icon_loupe}


def bubble(x, y, text, fill, fg, side, delay, w_char=7.4):
    """Bulle de message (côté « gauche » = reçu, « droite » = envoyé), qui pop."""
    w = len(text) * w_char + 28 + 10 * sum(ord(ch) > 0x2000 for ch in text)  # les emojis sont plus larges
    h = 32
    bx = x if side == "gauche" else x - w
    tail = (f'M{bx + 4},{y + h - 6} q-2,7 -8,9 q9,0 15,-5 z' if side == "gauche"
            else f'M{bx + w - 4},{y + h - 6} q2,7 8,9 q-9,0 -15,-5 z')
    origin = "left bottom" if side == "gauche" else "right bottom"   # la bulle sort de sa pointe
    return (f'<g class="bp" style="animation-delay:{delay:.2f}s;transform-origin:{origin}"><path d="{tail}" fill="{fill}"/>'
            f'<rect x="{bx:.0f}" y="{y}" width="{w:.0f}" height="{h}" rx="16" fill="{fill}"/>'
            f'<text x="{bx + 14:.0f}" y="{y + 21}" font-family="{SANS}" font-size="14" fill="{fg}">{escape(text)}</text></g>')


def typing(x, y, delay):
    """Bulle « en train d'écrire… » avec 3 points qui sautillent."""
    dots = "".join(
        f'<circle cx="{x + 16 + k * 11}" cy="{y + 16}" r="3.4" fill="{MQ_SOFT}">'
        f'<animate attributeName="opacity" values=".3;1;.3" dur="1.2s" begin="{k * .2:.1f}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="1.2s" begin="{k * .2:.1f}s" repeatCount="indefinite"/></circle>'
        for k in range(3))
    return (f'<g class="bp" style="animation-delay:{delay:.2f}s;transform-origin:left bottom"><path d="M{x + 4},{y + 26} q-2,7 -8,9 q9,0 15,-5 z" fill="{MQ_LINE}"/>'
            f'<rect x="{x}" y="{y}" width="54" height="32" rx="16" fill="{MQ_LINE}"/>{dots}</g>')


# conversation affichée dans chaque carte de projet : (question, réponse)
REPO_CHAT = {
    "IDATE": ("C'est quoi IDATE ?", "Drop soon… 👀"),
    "idsherlock": ("C'est quoi idsherlock ?", "Drop soon… 🔎"),
}


def repo_card(i, name, desc, lang, color, stars):
    """Carte de projet en forme de mini conversation de messagerie."""
    delay = 4.6 + i * 0.12
    q, a = REPO_CHAT.get(name, (f"C'est quoi {name} ?", desc))
    grad = ("#ff6a5a", "#e8263d") if color == MQ_R else ("#3ddc97", "#0b9e6e")
    body = f"""
{glass_panel(REPO_W, REPO_H, 14)}
<defs><linearGradient id="bub" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{grad[0]}"/><stop offset="1" stop-color="{grad[1]}"/></linearGradient></defs>
<g class="r" {d(delay)}>
  <circle cx="28" cy="34" r="5" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{MQ_TXT}">{escape(name)}</text>
</g>
{bubble(24, 58, q, MQ_LINE, MQ_TXT, "gauche", delay + .4)}
{bubble(REPO_W - 24, 100, a, "url(#bub)", "#ffffff", "droite", delay + 1.1)}
{typing(24, 142, delay + 1.8)}
"""
    write(f"repo-{name}.svg", svg(REPO_W, REPO_H, body, ["sans", "sans-b", "mono"], f"{name} : {q} {a}",
                                  left=6 * i, right=6 - 6 * i))


def section_title(text, italic, theme):
    fg = "#e6edf3" if theme == "dark" else INK
    body = (
        f'<text class="r" {d(4.4)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">{escape(text)} '
        f'<tspan font-style="italic" fill="{MQ_R}">{escape(italic)}</tspan></text>'
    )
    write(f"title-coding-{theme}.svg", svg(W, 64, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0))


# ---- 5 · blue contribution graph -----------------------------------------------
BLUE = [PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", TECH, "#1a3be0"]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5



def snake_inline(x, y, w):
    """Intègre le SVG du serpent dans un panneau. Les classes et animations de
    snk (c, s, u, c0, u1...) sont préfixées « z » pour ne pas gêner les nôtres."""
    src = open(SNAKE, encoding="utf-8").read()
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    vx, vy, vw, vh = (float(v) for v in vb.split())
    inner = re.sub(r'^.*?<svg[^>]*>', '', src, count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner)
    inner = re.sub(r'<desc>.*?</desc>', '', inner, flags=re.S)
    inner = re.sub(r'\.([csu])(\d*)(?=[{.,:\s])', r'.z\1\2', inner)
    inner = re.sub(r'@keyframes ([csu])(\d+)', r'@keyframes z\1\2', inner)
    inner = re.sub(r'animation-name:([csu])(\d+)', r'animation-name:z\1\2', inner)
    inner = re.sub(r'class="([^"]+)"',
                   lambda m: 'class="' + " ".join("z" + c for c in m.group(1).split()) + '"', inner)
    h = w * vh / vw
    return (f'<svg x="{x}" y="{y}" width="{w}" height="{h:.1f}" viewBox="{vb}">{inner}</svg>', h)




def _rows_svg(rows, cls=True, t_art=1.1):
    out = []
    for i, (y, txt) in enumerate(rows):
        anim = (f'class="f" style="animation-delay:{t_art + i * 0.02:.3f}s;animation-duration:.3s" ' if cls else "")
        out.append(f'<text {anim}xml:space="preserve" x="20" y="{y}" font-size="7.2" textLength="800" '
                   f'lengthAdjust="spacing" fill="url(#pgr)">{txt}</text>')
    return out


def fx_cendres(rows, top, bot):
    """Le portrait part en poussière vers la droite, puis se reforme (boucle de 10 s)."""
    import random
    rnd = random.Random(7)
    P, NX, NY = 10.0, 18, 18
    art = '<g id="art">' + "".join(_rows_svg(rows, cls=False)) + '</g>'
    bw, bh = 800 / NX, (bot - top) / NY
    clips, blocks = [], []
    for bx in range(NX):
        for by in range(NY):
            x, y = 20 + bx * bw, top + by * bh
            cid = f"k{bx}_{by}"
            clips.append(f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{bw + .6:.1f}" height="{bh + .6:.1f}"/></clipPath>')
            s0 = 2.6 + bx / NX * 1.8 + rnd.random() * .5
            s1 = s0 + 1.1
            r0, r1 = 7.2 + (NX - bx) / NX * .5 + rnd.random() * .3, 0
            r1 = r0 + 1.0
            dx, dy = 70 + rnd.random() * 160, -20 - rnd.random() * 110
            kt = f"0;{s0 / P:.4f};{s1 / P:.4f};{r0 / P:.4f};{min(r1 / P, .999):.4f};1"
            blocks.append(
                f'<g clip-path="url(#{cid})"><g>'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;{dx:.0f} {dy:.0f};{dx:.0f} {dy:.0f};0 0;0 0" '
                f'keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/>'
                f'<use href="#art"/></g></g>')
    dust = []
    for _ in range(110):
        x, y = 20 + rnd.random() * 800, top + rnd.random() * (bot - top)
        s0 = 2.6 + (x - 20) / 800 * 1.8 + rnd.random() * .6
        e = s0 + 1.6 + rnd.random()
        dx, dy = 120 + rnd.random() * 260, -40 - rnd.random() * 160
        col = rnd.choice(["#8ff3c6", "#1fcf8a", "#14a56f", "#ff4f3d"])
        kt = f"0;{s0 / P:.4f};{e / P:.4f};1"
        dust.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{1.5 + rnd.random() * 3:.1f}" fill="{col}" opacity="0">'
            f'<animate attributeName="opacity" values="0;.9;0;0" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;{dx:.0f} {dy:.0f};{dx:.0f} {dy:.0f}" '
            f'keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></circle>')
    return f'<defs>{art}{"".join(clips)}</defs>{"".join(blocks)}{"".join(dust)}'


def fx_hash(rows, top, bot):
    """Des caractères au hasard défilent puis se figent en portrait (décryptage),
    toutes les 12 s le code se rebrouille un instant."""
    import random, html as _h
    rnd = random.Random(3)
    P, F, FD = 12.0, 7, .12
    pool = "!@#$%&*+=?<>/\\|01ABCDEFXZ"
    out = []
    for i, (y, txt) in enumerate(rows):
        raw = _h.unescape(txt)
        st = .3 + i * .016
        end = st + F * FD
        base = (f'xml:space="preserve" x="20" y="{y}" font-size="7.2" textLength="800" '
                f'lengthAdjust="spacing"')
        for j in range(F):
            scr = "".join(c if c == " " else rnd.choice(pool) for c in raw)
            a, b = st + j * FD, st + (j + 1) * FD
            g1, g2 = 11.2 + (j % 3) * .25, 11.2 + (j % 3 + 1) * .25
            out.append(
                f'<text {base} fill="{"#ff4f3d" if j % 3 == 0 else "#8ff3c6"}" opacity="0">{_h.escape(scr)}'
                f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0;1;0" '
                f'keyTimes="0;{a / P:.4f};{b / P:.4f};{g1 / P:.4f};{g2 / P:.4f}" dur="{P}s" repeatCount="indefinite"/></text>')
        out.append(
            f'<text {base} fill="url(#pgr)">{txt}'
            f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0;1" '
            f'keyTimes="0;{end / P:.4f};{11.2 / P:.4f};{11.95 / P:.4f}" dur="{P}s" repeatCount="indefinite"/></text>')
    return "".join(out)


def fx_matrix(rows, top, bot):
    """Pluie de code : des colonnes de caractères verts tombent sur le portrait."""
    import random
    rnd = random.Random(11)
    out = ['<g opacity=".92">'] + _rows_svg(rows) + ['</g>']
    H = bot - top
    pool = "01アイウエオカキクケコｱｲｳｴｵ#$%&*+<>"
    for k in range(34):
        x = 20 + k * (800 / 34) + rnd.random() * 8
        n = 10 + rnd.randint(0, 10)
        dur = 3 + rnd.random() * 4
        chars = "".join(
            f'<tspan x="{x:.0f}" dy="22" fill="{"#e9fff5" if j == n - 1 else "#1fcf8a"}" '
            f'fill-opacity="{0.15 + 0.85 * (j + 1) / n:.2f}">{rnd.choice(pool)}</tspan>' for j in range(n))
        out.append(
            f'<text font-size="20" font-weight="700">{chars}'
            f'<animateTransform attributeName="transform" type="translate" values="0 {top - n * 22 - 40:.0f};0 {bot + 20:.0f}" '
            f'dur="{dur:.2f}s" begin="-{rnd.random() * dur:.2f}s" repeatCount="indefinite"/></text>')
    return "".join(out)


def fx_glitch(rows, top, bot):
    """Le portrait bugge toutes les 4 s : bandes décalées, copies rouge et verte, flash."""
    import random
    rnd = random.Random(5)
    P, g0 = 4.0, 3.0
    kt = f"0;{g0 / P:.3f};{(g0 + .08) / P:.3f};{(g0 + .16) / P:.3f};{(g0 + .24) / P:.3f};{(g0 + .32) / P:.3f};1"
    bands, nb = [], 9
    per = (len(rows) + nb - 1) // nb
    for b in range(nb):
        part = _rows_svg(rows[b * per:(b + 1) * per], t_art=1.1 + b * per * .02)
        d1, d2, d3 = (rnd.choice([-1, 1]) * rnd.randint(4, 26) for _ in range(3))
        bands.append(
            f'<g>{"".join(part)}<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;{d1} 0;{d2} 0;{d3} 0;0 0;0 0" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></g>')
    art = '<g id="art2">' + "".join(_rows_svg(rows, cls=False)) + '</g>'
    ghost = lambda col, dx: (
        f'<g opacity="0" style="mix-blend-mode:screen"><use href="#art2" transform="translate({dx} 0)" style="fill:{col}"/>'
        f'<animate attributeName="opacity" values="0;0;.7;0;.6;0;0" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></g>')
    flash = (f'<rect x="20" y="{top:.0f}" width="800" height="{bot - top:.0f}" fill="#ff4f3d" opacity="0">'
             f'<animate attributeName="opacity" values="0;0;.12;0;.08;0;0" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></rect>')
    red = f'<defs>{art}<filter id="tr"><feColorMatrix values="1 0 0 0 .6  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter></defs>'
    gr = (f'<g opacity="0" filter="url(#tr)"><use href="#art2" transform="translate(-9 0)"/>'
          f'<animate attributeName="opacity" values="0;0;.75;0;.6;0;0" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></g>')
    return red + "".join(bands) + gr + flash



def _bursts(P, bursts, frames):
    """values/keyTimes SMIL : au repos `frames[0]` puis, à chaque instant de
    `bursts`, enchaîne `frames` toutes les 0,08 s."""
    pts = [(0.0, frames[0])]
    for g in bursts:
        for k, v in enumerate(frames):
            pts.append((g + k * .08, v))
        pts.append((g + len(frames) * .08, frames[0]))
    pts.append((P, frames[0]))
    vals = ";".join(v for _, v in pts)
    kts = ";".join(f"{t / P:.4f}" for t, _ in pts)
    return vals, kts


def fx_cendres_glitch(rows, top, bot, t_art=1.1):
    """Mélange : le portrait bugge (glitch), part en cendres vers la droite, se
    reforme, rebugge un coup, et ainsi de suite (boucle de 10 s).
    Version légère : chaque ligne est coupée en NX morceaux une seule fois,
    regroupés en NB bandes x NX colonnes (pas de copies du portrait)."""
    import random, html as _h
    rnd = random.Random(7)
    P, NX, NB = 10.0, 12, 12
    bursts = [1.4, 2.1, 8.5]
    per = (len(rows) + NB - 1) // NB
    out = ['<defs><filter id="tr"><feColorMatrix values="1 0 0 0 .6  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter></defs>']
    for b in range(NB):
        band_rows = rows[b * per:(b + 1) * per]
        if not band_rows:
            continue
        cols = []
        for c in range(NX):
            texts = []
            for k, (y, txt) in enumerate(band_rows):
                ri = b * per + k              # n° de ligne : apparition ligne par ligne (comme avant)
                raw = _h.unescape(txt)
                L = len(raw)
                a, e = round(c * L / NX), round((c + 1) * L / NX)
                seg = raw[a:e]
                if not seg.strip():
                    continue
                cw = 800 / L
                texts.append(f'<text class="f" style="animation-delay:{t_art + ri * 0.02:.3f}s;animation-duration:.3s" '
                             f'xml:space="preserve" x="{20 + a * cw:.1f}" y="{y}" font-size="7.2" '
                             f'textLength="{(e - a) * cw:.1f}" lengthAdjust="spacing" fill="url(#pgr)">{_h.escape(seg)}</text>')
            if not texts:
                continue
            s0 = 2.8 + c / NX * 1.8 + rnd.random() * .5
            s1 = s0 + 1.1
            r0 = 7.0 + (NX - c) / NX * .5 + rnd.random() * .3
            r1 = r0 + 1.0
            dx, dy = 70 + rnd.random() * 160, -20 - rnd.random() * 110
            kt = f"0;{s0 / P:.4f};{s1 / P:.4f};{r0 / P:.4f};{min(r1 / P, .999):.4f};1"
            cols.append(
                f'<g>{"".join(texts)}'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;{dx:.0f} {dy:.0f};{dx:.0f} {dy:.0f};0 0;0 0" '
                f'keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></g>')
        # glitch : toute la bande se décale pendant les bugs
        d = [rnd.choice([-1, 1]) * rnd.randint(4, 26) for _ in range(3)]
        vals, kts = _bursts(P, bursts, ["0 0"] + [f"{x} 0" for x in d])
        out.append(f'<g>{"".join(cols)}<animateTransform attributeName="transform" type="translate" '
                   f'values="{vals}" keyTimes="{kts}" dur="{P}s" repeatCount="indefinite"/></g>')
    # (reflet rouge retiré à la demande de l'utilisateur)
    fv, fkt = _bursts(P, bursts, ["0", ".12", "0", ".08"])
    out.append(f'<rect x="20" y="{top:.0f}" width="800" height="{bot - top:.0f}" fill="#ff4f3d" opacity="0">'
               f'<animate attributeName="opacity" values="{fv}" keyTimes="{fkt}" dur="{P}s" repeatCount="indefinite"/></rect>')
    # poussière : n'apparaît qu'au moment où le portrait s'envole
    for _ in range(90):
        x, y = 20 + rnd.random() * 800, top + rnd.random() * (bot - top)
        s0 = 2.8 + (x - 20) / 800 * 1.8 + rnd.random() * .6
        e = s0 + 1.6 + rnd.random()
        dx, dy = 120 + rnd.random() * 260, -40 - rnd.random() * 160
        col = rnd.choice(["#8ff3c6", "#1fcf8a", "#14a56f", "#ff4f3d"])
        kt = f"0;{(s0 - .01) / P:.4f};{s0 / P:.4f};{e / P:.4f};1"
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{1.5 + rnd.random() * 3:.1f}" fill="{col}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 0;{dx:.0f} {dy:.0f};{dx:.0f} {dy:.0f}" '
            f'keyTimes="{kt}" dur="{P}s" repeatCount="indefinite"/></circle>')
    # la boucle glitch + cendres ne démarre qu'une fois le portrait imprimé
    start = t_art + len(rows) * 0.02 + 0.8
    return "".join(out).replace('repeatCount="indefinite"', f'begin="{start:.2f}s" repeatCount="indefinite"')


def portrait_panel():
    """Fenêtre de terminal en haut : `./portrait.sh` se tape, le portrait ASCII
    vert s'imprime ligne par ligne, puis `whoami` et un curseur qui clignote."""
    src = open(PORTRAIT, encoding="utf-8").read()
    rows = re.findall(r'<text xml:space="preserve"[^>]*\by="([\d.]+)"[^>]*>(.*?)</text>', src, re.S)
    ys = [float(y) for y, _ in rows]
    top, bot = min(ys) - 10, max(ys) + 4
    TB = 34                                    # barre de titre
    ph = 380                                   # hauteur du portrait
    pw = ph * 800 / (bot - top)
    p_y = TB + 50                              # le portrait commence sous la commande
    st_y = p_y + ph + 10                       # ligne de statut
    h = st_y + 46
    mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    t_cmd, t_art = 0.3, 1.1                    # début de la frappe, début du portrait
    fx = {"cendres": fx_cendres, "hash": fx_hash, "matrix": fx_matrix, "glitch": fx_glitch,
          "cendres+glitch": fx_cendres_glitch}.get(EFFET)
    lines = (fx_cendres_glitch(rows, top, bot, t_art) if EFFET == "cendres+glitch"
             else fx(rows, top, bot) if fx else "".join(_rows_svg(rows, t_art=t_art)))
    t_who = t_art + len(rows) * 0.02 + 0.3
    dots = "".join(f'<circle cx="{24 + k * 18}" cy="{TB / 2}" r="5.5" fill="{c}"/>'
                   for k, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]))

    def typed(x, y, text_svg, n_chars, begin, cid):
        """Texte révélé de gauche à droite (frappe) ; visible sans SMIL."""
        wpx = n_chars * 8.3 + 6
        return (f'<clipPath id="{cid}"><rect x="{x}" y="{y - 18}" width="{wpx:.0f}" height="26">'
                f'<animate attributeName="width" values="0;0;{wpx:.0f}" keyTimes="0;{begin / (begin + .6):.3f};1" '
                f'dur="{begin + .6:.2f}s" fill="freeze"/></rect></clipPath>'
                f'<g clip-path="url(#{cid})">{text_svg}</g>')

    cmd = (f'<text x="34" y="{TB + 32}" font-family="{mono}" font-size="15"><tspan fill="{MQ_G}">chriis@github</tspan>'
           f'<tspan fill="{MQ_SOFT}">:~$ </tspan><tspan fill="{MQ_TXT}">./portrait.sh</tspan></text>')
    who = (f'<text x="34" y="{st_y + 26}" font-family="{mono}" font-size="15"><tspan fill="{MQ_G}">chriis@github</tspan>'
           f'<tspan fill="{MQ_SOFT}">:~$ </tspan><tspan fill="{MQ_TXT}">whoami</tspan>'
           f'<tspan fill="{MQ_R}">  Chriis Heart</tspan></text>')
    who_len = len("chriis@github:~$ whoami  Chriis Heart")
    body = f"""
{glass_panel(W, h)}
<defs><linearGradient id="pgr" gradientUnits="userSpaceOnUse" x1="0" y1="{top:.0f}" x2="0" y2="{bot:.0f}">
  <stop offset="0" stop-color="#8ff3c6"/><stop offset=".55" stop-color="{MQ_G}"/><stop offset="1" stop-color="#14a56f"/></linearGradient></defs>
<rect x="1.5" y="1.5" width="{W - 3}" height="{TB}" rx="15" fill="#000" opacity=".25"/>
<rect x="1.5" y="{TB - 10}" width="{W - 3}" height="10" fill="#000" opacity=".25"/>
<line x1="1.5" y1="{TB + 1.5}" x2="{W - 1.5}" y2="{TB + 1.5}" stroke="{MQ_LINE}"/>
{dots}
<text x="{W / 2}" y="{TB / 2 + 4}" text-anchor="middle" font-family="{mono}" font-size="12" fill="{MQ_SOFT}">chriis@github: ~</text>
{typed(34, TB + 32, cmd, len("chriis@github:~$ ./portrait.sh"), t_cmd, "tc")}
<svg x="{(W - pw) / 2:.1f}" y="{p_y}" width="{pw:.1f}" height="{ph}" viewBox="20 {top:.1f} 800 {bot - top:.1f}"
  font-family="{mono}" overflow="hidden">{lines}</svg>
<line x1="1.5" y1="{st_y}" x2="{W - 1.5}" y2="{st_y}" stroke="{MQ_LINE}"/>
{typed(34, st_y + 26, who, who_len, t_who, "tw")}
<rect x="{34 + who_len * 8.3 + 4:.0f}" y="{st_y + 13}" width="9" height="17" fill="{MQ_G}">
  <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect>
"""
    write("portrait.svg", svg(W, h, body, [], "Terminal : portrait ASCII de Chriis Heart"))


def heatmap(data):
    if CHASSEUR in ("crabe", "bonhomme"):
        return heatmap_crab(data)
    if os.path.exists(SNAKE):
        return heatmap_snake(data)
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # sunday = 0
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()
    last_active = max((x["date"] for x in days if x["count"]), default="")
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, MOIS[date.month - 1]))
        c = day["count"]
        delay = 1.0 + col * 0.03 + row * 0.02
        # dernier jour actif : case entourée de rouge
        today = ' stroke="#ff4f3d" stroke-width="2"' if day["date"] == last_active else ""
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{MQ_LEVELS[level_for(c)]}"{today}>'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MQ_SOFT}">{m}</text>'
        for col, m in months if col < ncols - 12
    )
    legend_x = right - len(MQ_LEVELS) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(MQ_LEVELS)
    )
    h = gy + 7 * step + 44
    body = f"""
{glass_panel(W, h)}
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{MQ_TXT}">Chaque jour, <tspan font-style="italic" fill="{MQ_G}">en vert</tspan></text>
<g class="f" {d(0.8)}><circle class="live" cx="{right - 196}" cy="56" r="4" fill="{MQ_R}"/>
<text x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MQ_SOFT}">MIS À JOUR CHAQUE JOUR</text></g>
{''.join(cells)}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MQ_SOFT}">moins</text>
{legend}
<text x="{legend_x + len(MQ_LEVELS) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MQ_SOFT}">plus</text></g>
"""
    write("heatmap.svg", svg(W, h, body, ["serif", "serif-i", "mono"],
                             f'Calendrier : {data["total_contributions"]:,} contributions sur un an'))




def crab_svg():
    """Petit crabe rouge (original), centré sur 0,0, pinces qui claquent."""
    claw = lambda sx: (
        f'<g transform="translate({sx * 11} -6)"><g>'
        f'<animateTransform attributeName="transform" type="rotate" values="0;{-sx * 28};0" dur=".32s" repeatCount="indefinite"/>'
        f'<path d="M0,0 l{sx * 4},-6 a4,4 0 1 1 {sx * 2},6 z" fill="{MQ_R}"/>'
        f'<path d="M0,0 l{sx * 6},-1 a3.5,3.5 0 0 1 {-sx * 1},5 z" fill="#ff7a5c"/></g></g>')
    legs = "".join(
        f'<path d="M{sx * 6},{1 + k * 2.6} l{sx * 5},{1.5 + k}" stroke="{MQ_R}" stroke-width="1.6" stroke-linecap="round"/>'
        for sx in (-1, 1) for k in range(3))
    return (
        '<g>'
        f'<animateTransform attributeName="transform" type="translate" values="0,0;0,-1.2;0,0" dur=".24s" repeatCount="indefinite" additive="sum"/>'
        f'{legs}{claw(-1)}{claw(1)}'
        f'<ellipse cx="0" cy="2" rx="9" ry="6.5" fill="{MQ_R}"/>'
        f'<ellipse cx="0" cy="0" rx="6" ry="3" fill="#ff8a70" opacity=".6"/>'
        '<line x1="-3" y1="-4" x2="-3.5" y2="-8" stroke="#ff4f3d" stroke-width="1.4"/>'
        '<line x1="3" y1="-4" x2="3.5" y2="-8" stroke="#ff4f3d" stroke-width="1.4"/>'
        '<circle cx="-3.6" cy="-8.6" r="2" fill="#fff"/><circle cx="3.6" cy="-8.6" r="2" fill="#fff"/>'
        '<circle cx="-3.4" cy="-8.4" r="1" fill="#111"/><circle cx="3.8" cy="-8.4" r="1" fill="#111"/>'
        '</g>')



def bonhomme_svg(pose="marche", T=45.0, run=0.8, t_sit=0.83):
    """Petit bonhomme d'après ma photo : peau marron, cheveux bouclés courts et
    arrondis (ligne droite sur le front), sourcils froncés avec plis sur le front,
    t-shirt noir col rond.
    pose="marche" : il marche (jambes et bras) et croque (la bouche s'ouvre un peu).
    pose="assis"  : assis sous le cocotier, yeux fermés, un coco à la main, « Zzz ».
    Dans les deux poses, son ventre gonfle pendant qu'il mange (0 → run) puis
    dégonfle pendant la sieste (il digère)."""
    import math
    skin, skin_d, hair, tee = "#a0673f", "#80502f", "#141414", "#1c1c1c"
    walking = pose == "marche"

    def limb(x1, y1, x2, y2, col, w, a, dur):
        anim = (f'<animateTransform attributeName="transform" type="rotate" values="{a} {x1} {y1};{-a} {x1} {y1};{a} {x1} {y1}" '
                f'dur="{dur}s" repeatCount="indefinite"/>' if walking else "")
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" stroke-linecap="round">'
                f'{anim}</line>')

    if walking:
        limbs = (limb(-2.5, 8, -2.5, 13.5, "#0e0e0e", 2.6, 25, .45)
                 + limb(2.5, 8, 2.5, 13.5, "#0e0e0e", 2.6, -25, .45)
                 + limb(-6.2, 1.5, -8, 7.5, skin, 2.2, -30, .45)
                 + limb(6.2, 1.5, 8, 7.5, skin, 2.2, 30, .45))
    else:  # assis : jambes écartées vers l'avant, bras gauche posé
        limbs = (limb(-2.5, 8, -7.5, 11.5, "#0e0e0e", 2.6, 0, 0)
                 + limb(2.5, 8, 7.5, 11.5, "#0e0e0e", 2.6, 0, 0)
                 + limb(-6.2, 1.5, -9, 7, skin, 2.2, 0, 0))

    # ventre qui gonfle puis dégonfle (même horloge que le tour)
    shirt = (f'<path d="M-7,3 Q-7,-0.5 -3.5,-0.8 L3.5,-0.8 Q7,-0.5 7,3 L7,9 Q7,10 6,10 L-6,10 Q-7,10 -7,9 Z" fill="{tee}"/>'
             f'<path d="M-2.6,-0.8 Q0,1.6 2.6,-0.8" fill="none" stroke="#2c2c2c" stroke-width="1"/>')
    belly = (f'<g transform="translate(0 4.6)"><g>'
             f'<animateTransform attributeName="transform" type="scale" values="1 1;1.32 1.08;1.32 1.08;1 1;1 1" '
             f'keyTimes="0;{run};{t_sit + .02:.3f};.97;1" dur="{T}s" repeatCount="indefinite"/>'
             f'<g transform="translate(0 -4.6)">{shirt}</g></g></g>')

    # cheveux bouclés : un dôme + petites boucles sur le contour
    curls = "".join(f'<circle cx="{7.4 * math.cos(a):.2f}" cy="{-10 + 7.2 * math.sin(a):.2f}" r="2.2" fill="{hair}"/>'
                    for a in [math.radians(d) for d in range(180, 361, 22)])
    if walking:
        eyes = ('<path d="M-4.6,-5.2 Q-2.8,-6.2 -1.2,-5.2 Q-2.8,-4.3 -4.6,-5.2 Z" fill="#fff" stroke="#111" stroke-width=".4"/>'
                '<path d="M4.6,-5.2 Q2.8,-6.2 1.2,-5.2 Q2.8,-4.3 4.6,-5.2 Z" fill="#fff" stroke="#111" stroke-width=".4"/>'
                '<circle cx="-1.9" cy="-5.2" r=".75" fill="#111"/><circle cx="3.6" cy="-5.2" r=".75" fill="#111"/>')
        mouth = ('<ellipse cx="0" cy="-1.1" rx="1.2" ry=".35" fill="#5a2a1a">'
                 '<animate attributeName="ry" values=".3;.9;.3" dur=".45s" repeatCount="indefinite"/></ellipse>')
    else:  # yeux fermés, petite bouche tranquille
        eyes = '<path d="M-4.4,-5 Q-2.9,-4.1 -1.4,-5 M4.4,-5 Q2.9,-4.1 1.4,-5" stroke="#111" stroke-width=".7" stroke-linecap="round" fill="none"/>'
        mouth = '<ellipse cx="0" cy="-1.1" rx=".9" ry=".3" fill="#5a2a1a"/>'

    face = (f'<rect x="-1.6" y="-2.6" width="3.2" height="2.4" fill="{skin_d}"/>'
            f'<ellipse cx="0" cy="-10.5" rx="7.6" ry="6.8" fill="{hair}"/>{curls}'
            f'<ellipse cx="-6.4" cy="-6.8" rx="1.7" ry="2.2" fill="{skin}"/><ellipse cx="6.4" cy="-6.8" rx="1.7" ry="2.2" fill="{skin}"/>'
            f'<ellipse cx="-6.4" cy="-6.8" rx=".8" ry="1.2" fill="{skin_d}"/><ellipse cx="6.4" cy="-6.8" rx=".8" ry="1.2" fill="{skin_d}"/>'
            f'<path d="M-6,-9.5 L6,-9.5 L5.8,-4 Q5,0 0,0.6 Q-5,0 -5.8,-4 Z" fill="{skin}"/>'
            f'<rect x="-6.2" y="-11.2" width="12.4" height="2" fill="{hair}"/>'
            f'<path d="M-0.9,-9 Q-0.4,-7.6 -0.9,-6.6 M0.9,-9 Q0.4,-7.6 0.9,-6.6" stroke="{skin_d}" stroke-width=".55" fill="none"/>'
            '<path d="M-5,-7.4 Q-3,-7.9 -1.1,-6.3 M5,-7.4 Q3,-7.9 1.1,-6.3" stroke="#111" stroke-width="1.2" stroke-linecap="round" fill="none"/>'
            f'{eyes}'
            f'<path d="M-0.8,-2.6 Q0,-2 0.8,-2.6" stroke="{skin_d}" stroke-width=".6" fill="none"/>'
            f'{mouth}')

    if walking:
        bob = '<animateTransform attributeName="transform" type="translate" values="0,1.5;0,0.3;0,1.5" dur=".45s" repeatCount="indefinite"/>'
        return f'<g>{bob}{limbs}{belly}{face}</g>'

    # assis : bras droit qui tient un coco (avec sa paille) + des « Zzz » qui montent
    coco = (f'<line x1="6.2" y1="1.5" x2="9.4" y2="4.6" stroke="{skin}" stroke-width="2.2" stroke-linecap="round"/>'
            '<circle cx="11.2" cy="4" r="3.3" fill="#6b4423"/><circle cx="10.2" cy="3" r="1" fill="#8d6038"/>'
            f'<line x1="11.6" y1="1" x2="12.8" y2="-4" stroke="{MQ_R}" stroke-width=".9" stroke-linecap="round"/>')
    zzz = "".join(
        f'<text x="{6 + i * 4.5}" y="{-15 - i * 5}" font-family="{SANS}" font-weight="600" font-size="{5 + i * 1.8:.1f}" '
        f'fill="{MQ_TXT}" opacity="0">z'
        f'<animate attributeName="opacity" values="0;.9;0" dur="2.4s" begin="{i * .6:.1f}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 2;2 -3" dur="2.4s" begin="{i * .6:.1f}s" repeatCount="indefinite"/></text>'
        for i in range(3))
    return f'<g>{limbs}{belly}{face}{coco}{zzz}</g>'


MADRAS_DEFS = (
    # petit motif madras (carreaux jaune / rouge / vert / orange) pour le chapeau et le foulard
    '<pattern id="madras" width="4" height="4" patternUnits="userSpaceOnUse">'
    '<rect width="4" height="4" fill="#f2c200"/>'
    '<rect width="4" height="1.4" fill="#d7263d" opacity=".85"/>'
    '<rect width="1.4" height="4" fill="#1fa35b" opacity=".8"/>'
    '<rect x="2.6" width=".5" height="4" fill="#e8742a"/></pattern>')


def compagnon_svg(pose="marche"):
    """Claude en vrai petit personnage (perso original, pas le logo) : peau
    terracotta (la couleur de Claude), grands yeux, sourire, joues roses ;
    tenue antillaise : chapeau bakoua avec ruban madras, chemise madras,
    pantalon blanc et sandales.
    pose="marche" : il marche (jambes et bras). pose="assis" : il se balance,
    yeux fermés, et des notes de musique s'envolent (ambiance zouk)."""
    skin, skin_d, straw, straw_d = "#d97757", "#b85f43", "#e6c77e", "#b8964d"
    pants, sandal = "#f1efe8", "#7a4a24"
    walking = pose == "marche"

    def limb(x1, y1, x2, y2, col, w, a, begin=0):
        anim = (f'<animateTransform attributeName="transform" type="rotate" values="{a} {x1} {y1};{-a} {x1} {y1};{a} {x1} {y1}" '
                f'dur=".45s" begin="{begin}s" repeatCount="indefinite"/>' if walking else "")
        return (f'<g>{anim}<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
                f'<ellipse cx="{x2}" cy="{y2 + .8}" rx="1.9" ry=".9" fill="{sandal}"/></g>' if col == pants else
                f'<g>{anim}<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/></g>')

    if walking:
        legs = limb(-2.4, 8, -2.4, 13.6, pants, 2.8, 25, .22) + limb(2.4, 8, 2.4, 13.6, pants, 2.8, -25, .22)
        arms = limb(-6.3, 1.6, -8.2, 7.6, skin, 2.2, -30, .22) + limb(6.3, 1.6, 8.2, 7.6, skin, 2.2, 30, .22)
    else:  # assis : jambes vers l'avant, une main levée qui bat la mesure
        legs = limb(-2.4, 8, -7.6, 11.4, pants, 2.8, 0) + limb(2.4, 8, 7.6, 11.4, pants, 2.8, 0)
        arms = (limb(-6.3, 1.6, -9, 7, skin, 2.2, 0)
                + f'<g><animateTransform attributeName="transform" type="rotate" values="0 6.3 1.6;-25 6.3 1.6;0 6.3 1.6" dur=".7s" repeatCount="indefinite"/>'
                  f'<line x1="6.3" y1="1.6" x2="10" y2="-2.5" stroke="{skin}" stroke-width="2.2" stroke-linecap="round"/></g>')

    # chemise madras à manches courtes, col en V
    shirt = ('<path d="M-7.2,3 Q-7.2,-0.6 -3.6,-0.9 L3.6,-0.9 Q7.2,-0.6 7.2,3 L7.2,9 Q7.2,10 6.2,10 L-6.2,10 Q-7.2,10 -7.2,9 Z" '
             'fill="url(#madras)" stroke="#b81f33" stroke-width=".35"/>'
             f'<path d="M-2.4,-0.9 L0,2.6 L2.4,-0.9 Z" fill="{skin}"/>'
             '<path d="M-7.2,1.2 L-9,3.6 L-6.6,4.6 Z M7.2,1.2 L9,3.6 L6.6,4.6 Z" fill="url(#madras)"/>'
             '<circle cx="0" cy="4.6" r=".5" fill="#fff"/><circle cx="0" cy="7" r=".5" fill="#fff"/>')
    neck = f'<rect x="-1.5" y="-2.8" width="3" height="2.4" fill="{skin_d}"/>'
    head = (f'<ellipse cx="-6.3" cy="-7" rx="1.5" ry="2" fill="{skin}"/><ellipse cx="6.3" cy="-7" rx="1.5" ry="2" fill="{skin}"/>'
            f'<ellipse cx="0" cy="-7.6" rx="6.4" ry="6.6" fill="{skin}"/>'
            '<circle cx="-4" cy="-4.8" r="1.3" fill="#ff8f8f" opacity=".55"/><circle cx="4" cy="-4.8" r="1.3" fill="#ff8f8f" opacity=".55"/>')
    if walking:
        eyes = ('<ellipse cx="-2.4" cy="-7.4" rx="1.4" ry="1.7" fill="#fff"/><ellipse cx="2.4" cy="-7.4" rx="1.4" ry="1.7" fill="#fff"/>'
                '<circle cx="-2.1" cy="-7.2" r=".85" fill="#2b1a12"/><circle cx="2.7" cy="-7.2" r=".85" fill="#2b1a12"/>'
                '<circle cx="-1.8" cy="-7.6" r=".3" fill="#fff"/><circle cx="3" cy="-7.6" r=".3" fill="#fff"/>')
    else:
        eyes = '<path d="M-3.6,-7.2 Q-2.4,-8.4 -1.2,-7.2 M1.2,-7.2 Q2.4,-8.4 3.6,-7.2" stroke="#2b1a12" stroke-width=".7" stroke-linecap="round" fill="none"/>'
    mouth = '<path d="M-1.8,-4.4 Q0,-2.6 1.8,-4.4" stroke="#5a2a1a" stroke-width=".7" stroke-linecap="round" fill="none"/>'
    # chapeau bakoua : cône de paille pointu + ruban madras
    hat = (f'<path d="M-10.5,-11.6 Q0,-14.4 10.5,-11.6 L0,-22.6 Z" fill="{straw}" stroke="{straw_d}" stroke-width=".5"/>'
           f'<path d="M-3.2,-19.4 L3.2,-19.4 M-6,-16.2 L6,-16.2" stroke="{straw_d}" stroke-width=".45"/>'
           f'<path d="M-7.4,-13.4 Q0,-15.6 7.4,-13.4 L6.8,-12 Q0,-14.1 -6.8,-12 Z" fill="url(#madras)"/>'
           f'<circle cx="0" cy="-23" r="1" fill="{straw_d}"/>')
    perso = f'{legs}{arms}{shirt}{neck}{head}{eyes}{mouth}{hat}'
    if walking:
        bob = '<animateTransform attributeName="transform" type="translate" values="0,0.3;0,1.5;0,0.3" dur=".45s" repeatCount="indefinite"/>'
        return f'<g>{bob}{perso}</g>'
    notes = "".join(
        f'<text x="{-12 - i * 3}" y="{-16 - i * 4}" font-size="{7 + i}" fill="{["#f2c200", "#1fcf8a", "#ff4f3d"][i]}" opacity="0">{"♪♫♪"[i]}'
        f'<animate attributeName="opacity" values="0;1;0" dur="2.1s" begin="{i * .7:.1f}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 2;-3 -6" dur="2.1s" begin="{i * .7:.1f}s" repeatCount="indefinite"/></text>'
        for i in range(3))
    sway = '<animateTransform attributeName="transform" type="rotate" values="-4 0 9;4 0 9;-4 0 9" dur="1.4s" repeatCount="indefinite"/>'
    return f'<g><g>{sway}{perso}</g>{notes}</g>'


def cocotier(x, ground):
    """Petit cocotier (tronc penché, palmes qui se balancent, 2 cocos) + sable."""
    top_x, top_y = x - 5, ground - 40
    trunk = (f'<path d="M{x},{ground} Q{x + 3},{ground - 22} {top_x},{top_y}" fill="none" stroke="#8a5a2b" '
             f'stroke-width="4.5" stroke-linecap="round"/>'
             + "".join(f'<path d="M{x - 2.2 + k * .2:.1f},{ground - 6 - k * 7} l4.6,-1" stroke="#6b4423" stroke-width="1"/>' for k in range(5)))
    leaf = lambda ang, ln: (
        f'<path transform="rotate({ang} {top_x} {top_y})" d="M{top_x},{top_y} q{ln * .5},{-9} {ln},2 '
        f'q{-ln * .5},{-3} {-ln},-2 z" fill="{MQ_G}"/>')
    leaves = "".join(leaf(a, 19) for a in (-160, -120, -60, -20, 20))
    return (f'<ellipse cx="{x - 8}" cy="{ground + 1}" rx="26" ry="3.5" fill="#c9a66b" opacity=".22"/>'
            f'{trunk}<g>'
            f'<animateTransform attributeName="transform" type="rotate" values="-3 {top_x} {top_y};3 {top_x} {top_y};-3 {top_x} {top_y}" '
            f'dur="3.2s" repeatCount="indefinite"/>{leaves}'
            f'<circle cx="{top_x - 2}" cy="{top_y + 3}" r="2.4" fill="#6b4423"/><circle cx="{top_x + 2.5}" cy="{top_y + 3.5}" r="2.4" fill="#7a4a24"/></g>')


# petites phrases en créole martiniquais, au-dessus de sa tête pendant qu'il mange
# (moment dans le tour, de 0 à 1 ; texte)
# (moment dans le tour de 0 à 1, + secondes de décalage, texte)
PHRASES = [(0.12, 0, "An faim fow réel !"), (0.12, 5.0, "Sa vré boss !"), (0.48, 0, "Bon bagay ! 😋")]


def bulle_creole(text, t0, T, show=2.2, fill="#e9fff5", fg="#0d1117", side="droite", top=-43):
    """Bulle au-dessus d'un perso, qui sort de sa pointe. side="droite" : la bulle
    part vers la droite (pointe en bas à gauche) ; "gauche" : l'inverse.
    top : hauteur du haut de la bulle (plus haut pour Claude et son chapeau)."""
    # largeur mesurée sur la police Geist 600 en 11 px (~5,1 px par lettre),
    # les emojis sont plus larges ; 8 px de marge de chaque côté
    emo = sum(ord(ch) > 0x2000 for ch in text)
    w = (len(text) - emo) * 5.1 + emo * 15 + 16
    t1 = min(t0 + show / T, .98)                     # reste dans le tour (même en aperçu rapide)
    fade = min(.25 / T, (t1 - t0) / 3)
    kt = f"0;{t0:.4f};{t0 + fade:.4f};{t1 - fade:.4f};{t1:.4f};1"
    yb = top + 18                                    # bas de la bulle
    if side == "droite":
        rx, tail = -8, f"M-1,{yb} q-1,5 -5,7 q7,0 11,-6 z"
    else:
        rx, tail = 8 - w, f"M1,{yb} q1,5 5,7 q-7,0 -11,-6 z"
    return (f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" dur="{T}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 4;0 4;0 0;0 0;0 -2;0 -2" keyTimes="{kt}" '
            f'dur="{T}s" repeatCount="indefinite"/>'
            f'<path d="{tail}" fill="{fill}"/>'
            f'<rect x="{rx:.0f}" y="{top}" width="{w:.0f}" height="19" rx="9.5" fill="{fill}"/>'
            f'<text x="{rx + 8:.0f}" y="{top + 13.5}" font-family="{SANS}" font-weight="600" font-size="11" fill="{fg}">{escape(text)}</text></g>')


# ce que Claude répond (un peu après moi), et ce qu'il dit sous le cocotier
# (même format) : Claude parle 2,5 s après ma première bulle, puis je lui réponds
REPONSES = [(0.12, 2.5, "Ni an pyé koko la !"), (0.48, 2.5, "Sé vré menm !")]
# ce que Claude dit sous le cocotier : (secondes après qu'il s'est assis, texte)
PHRASE_SIESTE = [(0.4, "Je t'avais dit ça bon !"), (3.4, "Maintenant je vais râler une douss 😴")]


def heatmap_crab(data):
    """Panneau « Chaque jour, en vert » : le bonhomme (ou le crabe) parcourt la
    grille colonne par colonne (en zigzag) et mange les cases vertes. Le bonhomme
    grossit, lâche des phrases en créole et des « +N » sur les gros jours, puis va
    faire la sieste sous un cocotier pendant que les cases repoussent."""
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
    cell, step, gx, gy = 12, 15, 44, 110
    ncols = (len(days) + lead + 6) // 7
    perso = CHASSEUR == "bonhomme"
    # trajet en zigzag : descend la colonne 0, remonte la 1, etc.
    order = []
    for col in range(ncols):
        rows = range(7) if col % 2 == 0 else range(6, -1, -1)
        order += [(col, r) for r in rows]
    n = len(order)
    T = float(os.environ.get("TOUR", 45))   # durée d'un tour complet (s) ; TOUR=12 pour un aperçu rapide
    run = 0.80 if perso else 0.9     # part du tour où il mange
    t_sit = 0.83                     # il arrive au cocotier
    t_wake = 0.985                   # fin de la sieste
    when = {cr: i / (n - 1) * run for i, cr in enumerate(order)}
    cx = lambda c: gx + c * step + cell / 2
    cy = lambda r: gy + r * step + cell / 2
    pts = [(cx(c), cy(r)) for c, r in order]
    ground = gy + 7 * step + 40
    tree_x = gx + ncols * step + 12
    sit = (tree_x - 26, ground - 11)

    # repousse en vague de gauche à droite pendant la sieste (ou la pause du crabe)
    w0, w1 = (t_sit + .015, .95) if perso else (run, run + .07)

    cells, months, seen = [], [], set()
    counts = sorted((d["count"] for d in days if d["count"]), reverse=True)
    seuil = counts[min(len(counts) - 1, 40)] if counts else 1   # ~40 plus gros jours → « +N »
    seuil = max(seuil, 2)
    plus = []
    for i, day in enumerate(days):
        col, row = divmod(i + lead, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, MOIS[date.month - 1]))
        c = day["count"]
        x, y = gx + col * step, gy + row * step
        if not c:
            cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{MQ_EMPTY}"/>')
            continue
        k = when[(col, row)]
        e = min(k + 0.004, 0.999)
        # case verte : croquée quand il passe (elle rétrécit et s'efface),
        # puis repousse en vague de gauche à droite
        k2 = k + 0.3 / T                              # 0,3 s pour rétrécir
        b = w0 + col / ncols * (w1 - w0)              # moment où elle repousse
        b2 = b + 0.5 / T                              # 0,5 s pour repousser
        kt = f"0;{k:.4f};{k2:.4f};{b:.4f};{b2:.4f};1"
        sp = "0 0 1 1;.23 1 .32 1;0 0 1 1;.23 1 .32 1;0 0 1 1"   # courbe vive (ease-out fort)
        h2 = cell / 2
        cells.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{MQ_EMPTY}"/>'
            f'<g transform="translate({x + h2} {y + h2})">'
            f'<rect x="{-h2}" y="{-h2}" width="{cell}" height="{cell}" rx="3" fill="{MQ_LEVELS[level_for(c)]}">'
            f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{kt}" calcMode="spline" keySplines="{sp}" '
            f'dur="{T}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="scale" values="1;1;.35;.6;1;1" keyTimes="{kt}" '
            f'calcMode="spline" keySplines="{sp}" dur="{T}s" repeatCount="indefinite"/>'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect></g>'
            # petit éclat rouge au moment où il croque
            f'<circle cx="{x + cell / 2}" cy="{y + cell / 2}" r="3" fill="none" stroke="{MQ_R}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;{k:.4f};{e:.4f};{min(e + .02, .99):.4f};1" dur="{T}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="3;3;3;12;12" keyTimes="0;{k:.4f};{e:.4f};{min(e + .02, .99):.4f};1" dur="{T}s" repeatCount="indefinite"/></circle>'
        )
        if perso and c >= seuil:
            # « +N » qui s'envole sur les gros jours
            p1, p2 = k + .3 / T, k + 1.2 / T
            pk = f"0;{k:.4f};{p1:.4f};{p2:.4f};1"
            plus.append(
                f'<text x="{x + h2}" y="{y - 2}" text-anchor="middle" font-family="{MONO}" font-weight="600" font-size="10" '
                f'fill="#8ff3c6" opacity="0">+{c}'
                f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{pk}" dur="{T}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -6;0 -18;0 -18" keyTimes="{pk}" '
                f'dur="{T}s" repeatCount="indefinite"/></text>')
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MQ_SOFT}">{m}</text>'
        for col, m in months if col < ncols - 12)

    if perso:
        # trajet : la grille en zigzag, puis il marche jusqu'au cocotier
        L1 = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        L2 = math.dist(pts[-1], sit)
        f = L1 / (L1 + L2)
        path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts + [sit])
        bulles = "".join(bulle_creole(t, t0 + dt / T, T) for t0, dt, t in PHRASES)
        walker = (f'<g>{bonhomme_svg("marche", T, run, t_sit)}{bulles}'
                  f'<animateMotion path="{path}" dur="{T}s" repeatCount="indefinite" '
                  f'keyPoints="0;{f:.4f};1;1" keyTimes="0;{run};{t_sit};1" calcMode="linear"/>'
                  f'<animate attributeName="opacity" values="1;0" keyTimes="0;{t_sit}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
        sitter = (f'<g transform="translate({sit[0]:.1f} {sit[1] + 1:.1f})" opacity="0">{bonhomme_svg("assis", T, run, t_sit)}'
                  f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{t_sit};{t_wake}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
        # compagnon inspiré de Claude : il suit quelques cases derrière, puis s'assoit à côté
        lag = 7 / (n - 1) * run                       # retard de 7 cases
        sit2 = (sit[0] - 24, sit[1] + 2)
        L2b = math.dist(pts[-1], sit2)
        f2 = L1 / (L1 + L2b)
        path2 = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts + [sit2])
        t_sit2 = t_sit + lag
        CL, CL_TXT = "#d97757", "#ffffff"               # bulles de Claude : terracotta
        rep = "".join(bulle_creole(txt, t0 + dt / T, T, fill=CL, fg=CL_TXT, top=-49)
                      for t0, dt, txt in REPONSES)
        dodo = "".join(bulle_creole(txt, t_sit2 + dt / T, T, show=2.8, fill=CL, fg=CL_TXT, side="gauche", top=-49)
                       for dt, txt in PHRASE_SIESTE)
        pote = (f'<g>{compagnon_svg("marche")}{rep}'
                f'<animateMotion path="{path2}" dur="{T}s" repeatCount="indefinite" '
                f'keyPoints="0;0;{f2:.4f};1;1" keyTimes="0;{lag:.4f};{run + lag:.4f};{t_sit2:.4f};1" calcMode="linear"/>'
                f'<animate attributeName="opacity" values="1;0" keyTimes="0;{t_sit2:.4f}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>'
                f'<g transform="translate({sit2[0]:.1f} {sit2[1]:.1f})" opacity="0">{compagnon_svg("assis")}{dodo}'
                f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{t_sit2:.4f};{t_wake}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
        chasseur = f'<defs>{MADRAS_DEFS}</defs>' + cocotier(tree_x, ground) + pote + walker + sitter
        h = ground + 14
    else:
        path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        chasseur = (f'<g>{crab_svg()}<animateMotion path="{path}" dur="{T}s" repeatCount="indefinite" '
                    f'keyPoints="0;1;1" keyTimes="0;{run};1" calcMode="linear"/></g>')
        h = gy + 7 * step + 44
    body = f"""
{glass_panel(W, h)}
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{MQ_TXT}">Chaque jour, <tspan font-style="italic" fill="{MQ_G}">en vert</tspan></text>
<g class="f" {d(0.8)}><circle class="live" cx="{right - 196}" cy="56" r="4" fill="{MQ_R}"/>
<text x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MQ_SOFT}">MIS À JOUR CHAQUE JOUR</text></g>
{''.join(cells)}
<g class="f" {d(1.2)}>{labels}</g>
{chasseur}
{''.join(plus)}
"""
    write("heatmap.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                             f'{"Mon petit bonhomme" if perso else "Un crabe"} mange ma grille : {data["total_contributions"]:,} contributions sur un an'))


def heatmap_snake(data):
    """Panneau « Chaque jour, en vert » où le serpent mange la grille."""
    snake, sh = snake_inline(16, 70, W - 32)
    h = int(70 + sh + 18)
    right = W - 42
    body = f"""
{glass_panel(W, h)}
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{MQ_TXT}">Chaque jour, <tspan font-style="italic" fill="{MQ_G}">en vert</tspan></text>
<g class="f" {d(0.8)}><circle class="live" cx="{right - 196}" cy="56" r="4" fill="{MQ_R}"/>
<text x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MQ_SOFT}">MIS À JOUR CHAQUE JOUR</text></g>
<g class="f" {d(1.0)}>{snake}</g>
"""
    write("heatmap.svg", svg(W, h, body, ["serif", "serif-i", "mono"],
                             f'Serpent qui mange ma grille : {data["total_contributions"]:,} contributions sur un an'))


def repo_stars():
    stars = {}
    try:
        import requests

        for name, *_ in REPOS:
            r = requests.get(f"https://api.github.com/repos/{GH_USER}/{name}", timeout=10)
            if r.ok:
                stars[name] = r.json().get("stargazers_count", 0)
    except Exception as e:  # offline: keep going without stars
        print(f"stars unavailable: {e}")
    return stars


if __name__ == "__main__":
    data = json.load(open(DATA, encoding="utf-8"))
    # hero()  # bandeau « Chriis Heart » retiré du profil le 2026-11-25
    portrait_panel()
    tile("build", "CODE", MQ_RED, "#ffffff", "2", "projets",
         "IDATE, idsherlock · drop soon", 3.1, 0)
    tile("brand", "LIEU", MQ_GREEN, "#ffffff", "972", "Martinique",
         "", 3.35, 1, flag=True)
    tile("learn", "MAKOO", MQ_BLACK, "#ffffff", "1", "équipe",
         "Mon équipe et mes projets chez MAKOO.", 3.6, 2)
    activity(data)
    stars = repo_stars()
    for i, (name, desc, lang, color) in enumerate(REPOS):
        repo_card(i, name, desc, lang, color, stars.get(name))
    section_title("Mes", "codes", "dark")
    section_title("Mes", "codes", "light")
    heatmap(data)
