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
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
PORTRAIT = os.path.join(ROOT, "chris-ascii.svg")
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
GLASS = True

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
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
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
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
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
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = "url(#barR)" if is_best else "url(#barG)"
        label = MOIS[int(m["month"][5:7]) - 1]
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="5" fill="{fill}"{' filter="url(#glowR)"' if is_best else ""}><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MQ_SOFT}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MQ_R}">{m["total"]:,}</text>'
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
REPO_W, REPO_H = 880 / 2 - 6, 176
REPOS = [
    ("IDATE", "Drop soon.", "Code", MQ_R),
    ("idsherlock", "Drop soon.", "Code", MQ_G),
]


def repo_card(i, name, desc, lang, color, stars):
    delay = 4.6 + i * 0.12
    meta = f"{lang}  ·  ★ {stars}" if stars else f"{lang}  ·  drop soon"
    body = f"""
{glass_panel(REPO_W, REPO_H, 14)}
<g class="r" {d(delay)}>
  <circle cx="28" cy="34" r="5" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{MQ_TXT}">{escape(name)}</text>
  {text_lines(24, 72, wrap(desc, 52), 21, f'font-family="{SANS}" font-size="14" fill="{MQ_SOFT}"')}
  <text x="24" y="{REPO_H - 24}" font-family="{MONO}" font-size="12" fill="{MQ_SOFT}">{escape(meta)}</text>
</g>
"""
    write(f"repo-{name}.svg", svg(REPO_W, REPO_H, body, ["sans", "sans-b", "mono"], f"{name}: {desc}",
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


def heatmap(data):
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
