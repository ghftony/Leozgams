#!/usr/bin/env python3
"""Build "Steal a Gobo" as a Scratch 3 project file (Steal_a_Gobo.sb3).

A "Steal a Brainrot" style game with Gobos: buy Gobos from the red carpet, keep them in
your base so they make money, and press the STEAL button to sneak into another player's
base and steal one random Gobo (once every 1 minute 30 seconds).

Run:  python3 build_sb3.py
Then open the .sb3 at https://scratch.mit.edu -> Create -> File -> Load from your computer.
"""
import hashlib
import io
import json
import math
import struct
import wave
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "Steal_a_Gobo.sb3"

# ---------------------------------------------------------------- Gobo types

#        name               tier          price     $/sec  chance (out of 10000)
GOBOS = [("Gobo",            "Common",        10,       1, 2999),
         ("Bubblegum Gobo",  "Common",        15,       2, 2200),
         ("Leaf Gobo",       "Uncommon",      50,       4, 1500),
         ("Choco Gobo",      "Uncommon",      80,       6, 1100),
         ("Ice Gobo",        "Rare",         250,      15,  800),
         ("Ocean Gobo",      "Rare",         400,      22,  550),
         ("Fire Gobo",       "Epic",        1200,      60,  350),
         ("Ninja Gobo",      "Epic",        2000,      90,  230),
         ("Robo Gobo",       "Legendary",   6000,     250,  120),
         ("Pirate Gobo",     "Legendary",   9000,     350,   80),
         ("Galaxy Gobo",     "Mythic",     25000,     900,   35),
         ("Ghost Gobo",      "Mythic",     40000,    1300,   20),
         ("Golden Gobo",     "Gobo God",  120000,    3500,    8),
         ("Diamond Gobo",    "Gobo God",  200000,    5500,    5),
         ("Rainbow Gobo",    "Secret",    600000,   15000,    2),
         ("Dragon Gobo",     "Secret",   1000000,   25000,    1)]
CUMULATIVE = [sum(g[4] for g in GOBOS[:i + 1]) for i in range(len(GOBOS))]
assert CUMULATIVE[-1] == 10000
N_GOBOS = len(GOBOS)
RARE_FROM = 9   # Gobo number 9 (Robo) and up get a "WOW!" announcement

# ---------------------------------------------------------------- art (SVG)

SPARK = '<path d="M{x} {y} l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2 z" fill="{c}"/>'
INK = "#2b1a0a"   # comic-book outline colour


def gobo_svg(body, edge, extra_back="", extra_front="", defs="", blink=False, mouth=None):
    """Gobo: a round little creature with a spiky flame-like top and big eyes, drawn cartoon style."""
    if blink:
        eyes = ('<path d="M22.5 41 Q28 46 33.5 41" fill="none" stroke="{0}" stroke-width="2.4" stroke-linecap="round"/>'
                '<path d="M36.5 41 Q42 46 47.5 41" fill="none" stroke="{0}" stroke-width="2.4" stroke-linecap="round"/>'
                ).format(INK)
    else:
        eyes = f'''<ellipse cx="28" cy="40" rx="6" ry="7" fill="#fff" stroke="{INK}" stroke-width="1.6"/>
<ellipse cx="42" cy="40" rx="6" ry="7" fill="#fff" stroke="{INK}" stroke-width="1.6"/>
<circle cx="29" cy="41" r="3.4" fill="{INK}"/>
<circle cx="43" cy="41" r="3.4" fill="{INK}"/>
<circle cx="30.2" cy="39.5" r="1.2" fill="#fff"/>
<circle cx="44.2" cy="39.5" r="1.2" fill="#fff"/>'''
    mouth = mouth or f'<path d="M30 50 Q35 56 40 50" fill="#e0505a" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="70" height="72" viewBox="0 0 70 72">
<defs>{defs}</defs>
{extra_back}
<ellipse cx="25" cy="66" rx="7.5" ry="4.5" fill="{edge}" stroke="{INK}" stroke-width="2"/>
<ellipse cx="45" cy="66" rx="7.5" ry="4.5" fill="{edge}" stroke="{INK}" stroke-width="2"/>
<path d="M17 40 Q8 42 6 50 Q13 50 18 46 Z" fill="{body}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>
<path d="M53 40 Q62 42 64 50 Q57 50 52 46 Z" fill="{body}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>
<path d="M35 3 L39 19 L50 7 L48 22 L60 17 L53 31 Q60 46 52 57 Q35 70 18 57 Q10 46 17 31 L9 22 L22 24 L21 9 L30 20 Z"
 fill="{body}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
<path d="M18 50 Q35 66 52 50 Q50 60 35 63 Q20 60 18 50 Z" fill="{edge}" opacity="0.45"/>
<ellipse cx="22" cy="30" rx="4" ry="6" fill="#fff" opacity="0.45" transform="rotate(25 22 30)"/>
<ellipse cx="21" cy="48" rx="3.5" ry="2" fill="#ff7a8a" opacity="0.55"/>
<ellipse cx="49" cy="48" rx="3.5" ry="2" fill="#ff7a8a" opacity="0.55"/>
{eyes}
{mouth}
{extra_front}
</svg>'''


def grad(gid, *stops, radial=False):
    tag = "radialGradient" if radial else "linearGradient"
    attrs = 'cx="0.4" cy="0.4" r="0.75"' if radial else 'x1="0" y1="0" x2="0" y2="1"'
    s = "".join(f'<stop offset="{i / (len(stops) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(stops))
    return f'<{tag} id="{gid}" {attrs}>{s}</{tag}>'


GOBO_STYLES = [
    dict(body="#FFBF1F", edge="#E08A00"),
    dict(body="#FF8FC8", edge="#D0458A",
         mouth=f'<circle cx="35" cy="55" r="7" fill="#FFB3DD" stroke="{INK}" stroke-width="1.6"/>'
               '<ellipse cx="32.5" cy="52.5" rx="2" ry="1.3" fill="#fff"/>'),
    dict(body="#7ED957", edge="#3B8F2B",
         extra_front=f'<path d="M35 4 Q46 -2 50 6 Q42 10 35 4 Z" fill="#3B8F2B" stroke="{INK}" stroke-width="1.5"/>'),
    dict(body="#9A6234", edge="#5A3410",
         extra_front="".join(f'<rect x="{x}" y="{y}" width="5" height="2" rx="1" fill="{c}" transform="rotate({r} {x} {y})"/>'
                             for x, y, c, r in ((24, 17, "#ff5e9e", 30), (40, 14, "#5ec8ff", -20), (45, 27, "#ffe066", 40),
                                                (18, 30, "#7ED957", -35), (33, 24, "#fff", 10), (50, 34, "#ff5e9e", 15)))),
    dict(body="#AEEFFF", edge="#2A8FC8",
         extra_front=SPARK.format(x=8, y=12, c="#fff") + SPARK.format(x=58, y=34, c="#fff")),
    dict(body="#3FA9F5", edge="#1B5E9A",
         extra_back='<circle cx="8" cy="20" r="4" fill="none" stroke="#bfe8ff" stroke-width="1.5"/>'
                    '<circle cx="62" cy="10" r="3" fill="none" stroke="#bfe8ff" stroke-width="1.5"/>'
                    '<circle cx="64" cy="26" r="2" fill="none" stroke="#bfe8ff" stroke-width="1.5"/>',
         extra_front='<path d="M20 58 Q25 54 30 58 Q35 62 40 58 Q45 54 50 58" fill="none" stroke="#bfe8ff" stroke-width="2"/>'),
    dict(body="#FF7A2F", edge="#B8330A",
         extra_back=f'<path d="M35 0 L44 14 L56 4 L54 20 L68 18 L58 34 L12 34 L2 18 L16 20 L14 4 L26 14 Z" '
                    f'fill="#FFD23F" stroke="#FF9A2F" stroke-width="2"/>'),
    dict(body="#3a3a4a", edge="#15151f",
         extra_front=f'<rect x="13" y="29" width="44" height="6" rx="2" fill="#e02a2a" stroke="{INK}" stroke-width="1.2"/>'
                     f'<path d="M56 31 L68 26 L66 33 Z M56 33 L67 38 L60 40 Z" fill="#e02a2a" stroke="{INK}" stroke-width="1"/>'),
    dict(body="#B8C2CC", edge="#5A6570",
         extra_back=f'<path d="M35 6 L35 -6" stroke="{INK}" stroke-width="2"/>',
         extra_front='<circle cx="35" cy="2" r="3" fill="#ff3030"/>'
                     '<circle cx="18" cy="34" r="1.6" fill="#5A6570"/><circle cx="52" cy="34" r="1.6" fill="#5A6570"/>'
                     '<circle cx="20" cy="56" r="1.6" fill="#5A6570"/><circle cx="50" cy="56" r="1.6" fill="#5A6570"/>',
         mouth=f'<rect x="28" y="49" width="14" height="6" rx="1" fill="#333" stroke="{INK}" stroke-width="1.2"/>'
               '<path d="M31.5 49 V55 M35 49 V55 M38.5 49 V55" stroke="#8cf" stroke-width="1"/>'),
    dict(body="#F2A65A", edge="#A0521A",
         extra_front=f'<path d="M12 22 Q35 -4 58 22 Q35 14 12 22 Z" fill="#222" stroke="{INK}" stroke-width="1.5"/>'
                     '<circle cx="35" cy="14" r="3" fill="#fff"/>'
                     f'<path d="M16 31 L56 43" stroke="{INK}" stroke-width="1.5"/>'
                     f'<ellipse cx="42" cy="40" rx="7" ry="7.5" fill="#222" stroke="{INK}" stroke-width="1"/>'),
    dict(body="url(#gal)", edge="#3A1F80", defs=grad("gal", "#B58CFF", "#3B1A8C", radial=True),
         extra_front=SPARK.format(x=22, y=24, c="#fff") + SPARK.format(x=48, y=54, c="#FFE66D")
         + '<circle cx="18" cy="54" r="1.5" fill="#fff"/><circle cx="52" cy="26" r="1.5" fill="#fff"/>'),
    dict(body="#F4F7FF", edge="#9AA8C8",
         extra_back='<circle cx="35" cy="38" r="34" fill="#dfe8ff" opacity="0.5"/>',
         mouth=f'<ellipse cx="35" cy="53" rx="4" ry="5" fill="{INK}"/>'),
    dict(body="url(#gold)", edge="#A87400", defs=grad("gold", "#FFF3A0", "#FFB800"),
         extra_front=f'<path d="M24 12 L28 2 L32 10 L35 0 L38 10 L42 2 L46 12 Z" fill="#FFD700" '
                     f'stroke="{INK}" stroke-width="1.5"/>' + SPARK.format(x=6, y=28, c="#fff")),
    dict(body="url(#dia)", edge="#39A6D6", defs=grad("dia", "#FFFFFF", "#9BE7FF", "#4FC3F7"),
         extra_front='<path d="M20 30 L35 22 L50 30 M20 30 L35 60 L50 30 M35 22 L35 60" fill="none" stroke="#fff" '
                     'stroke-width="1.2" opacity="0.8"/>' + SPARK.format(x=6, y=10, c="#fff")
                     + SPARK.format(x=58, y=40, c="#fff")),
    dict(body="url(#rainbow)", edge="#7a3cc8",
         defs=grad("rainbow", "#FF5E5E", "#FFD23F", "#6BE06B", "#5EC8FF", "#B36BFF"),
         extra_back='<circle cx="35" cy="38" r="34" fill="#FFF7B0" opacity="0.6"/>',
         extra_front=SPARK.format(x=6, y=12, c="#fff") + SPARK.format(x=60, y=30, c="#fff")),
    dict(body="#E0413A", edge="#8A1A12",
         extra_back=f'<path d="M14 36 L-2 20 L4 40 L-2 48 L14 46 Z M56 36 L72 20 L66 40 L72 48 L56 46 Z" '
                    f'fill="#7a3cc8" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>',
         extra_front=f'<path d="M22 22 L16 6 L28 18 Z M48 22 L54 6 L42 18 Z" fill="#FFE066" stroke="{INK}" '
                     'stroke-width="1.5" stroke-linejoin="round"/>'
                     '<path d="M24 58 L28 54 L32 58 L36 54 L40 58 L44 54" fill="none" stroke="#FFD23F" stroke-width="1.5"/>'),
]
assert len(GOBO_STYLES) == N_GOBOS
GOBO_ART = [gobo_svg(**st) for st in GOBO_STYLES]
GOBO_BLINK = [gobo_svg(**st, blink=True) for st in GOBO_STYLES]


def person_svg(shirt, stripe, hat, mask, frame=0):
    """The thief. frame 0 = standing, 1 and 2 = walking (legs and arms swing, body bounces)."""
    lift = 0 if frame == 0 else 2
    legs = {0: (15, 29), 1: (11, 31), 2: (18, 26)}[frame]
    arms = {0: (8, 40), 1: (6, 42), 2: (10, 38)}[frame]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="56" height="68" viewBox="0 0 56 68">
<ellipse cx="28" cy="65" rx="16" ry="3" fill="#000" opacity="0.15"/>
<rect x="{legs[0] + 2}" y="{57 - lift}" width="9" height="{9 + lift}" rx="3" fill="#333" stroke="{INK}" stroke-width="1.5"/>
<rect x="{legs[1] + 2}" y="{57 - lift}" width="9" height="{9 + lift}" rx="3" fill="#333" stroke="{INK}" stroke-width="1.5"/>
<circle cx="{arms[0] + 2}" cy="{46 - lift}" r="4" fill="#F2C29B" stroke="{INK}" stroke-width="1.5"/>
<circle cx="{54 - arms[0]}" cy="{arms[1] + 4 - lift}" r="4" fill="#F2C29B" stroke="{INK}" stroke-width="1.5"/>
<g transform="translate(2 {-lift})">
<rect x="14" y="36" width="24" height="22" rx="6" fill="{shirt}" stroke="{INK}" stroke-width="2"/>
<rect x="15" y="41" width="22" height="4" fill="{stripe}"/>
<rect x="15" y="49" width="22" height="4" fill="{stripe}"/>
<circle cx="26" cy="24" r="14" fill="#F2C29B" stroke="{INK}" stroke-width="2"/>
<path d="M11 18 Q26 2 41 18 Z" fill="{hat}" stroke="{INK}" stroke-width="1.5"/>
<rect x="9" y="16" width="34" height="4" rx="2" fill="{hat}" stroke="{INK}" stroke-width="1.5"/>
<rect x="12" y="20" width="28" height="8" rx="4" fill="{mask}"/>
<circle cx="21" cy="24" r="2.6" fill="#fff"/>
<circle cx="31" cy="24" r="2.6" fill="#fff"/>
<circle cx="22" cy="24" r="1.3" fill="#000"/>
<circle cx="32" cy="24" r="1.3" fill="#000"/>
<path d="M20 31 Q26 37 32 31" fill="#fff" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>
</g>
</svg>'''


PLAYER_FRAMES = [person_svg("#2f6fd6", "#ffffff", "#1d3f8a", "#111", frame=f) for f in range(3)]

COIN = f'''<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 26 26">
<circle cx="13" cy="13" r="11.5" fill="#FFD23F" stroke="{INK}" stroke-width="2"/>
<circle cx="13" cy="13" r="8" fill="none" stroke="#E0A000" stroke-width="1.5"/>
<text x="13" y="18" font-family="Sans Serif" font-size="13" font-weight="bold" fill="#A87400" text-anchor="middle">$</text>
</svg>'''


def starburst(label, fill, text_color, w=150, h=100, points=14, size=30):
    cx, cy = w / 2, h / 2
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points
        r = 1.0 if i % 2 == 0 else 0.68
        pts.append(f"{cx + math.cos(a) * r * (w / 2 - 3):.1f},{cy + math.sin(a) * r * (h / 2 - 3):.1f}")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
<text x="{cx + 2}" y="{cy + size / 3 + 2}" font-family="Marker" font-size="{size}" fill="{INK}" text-anchor="middle">{label}</text>
<text x="{cx}" y="{cy + size / 3}" font-family="Marker" font-size="{size}" fill="{text_color}" text-anchor="middle">{label}</text>
</svg>'''


BURSTS = {"kaching": starburst("KA-CHING!", "#FFE066", "#1f9e3a", size=24),
          "wow": starburst("WOW!", "#FF5EC8", "#fff"),
          "sold": starburst("SOLD!", "#7ED957", "#fff"),
          "zoom": starburst("ZOOM!", "#5EC8FF", "#fff"),
          "yoink": starburst("YOINK!", "#FFD23F", "#e0202a")}


def flash_svg(label, ray1, ray2, text_color, sub=""):
    """A full-screen comic flash with speed-line rays and a big word."""
    rays = []
    for i in range(24):
        a1, a2 = 2 * math.pi * i / 24, 2 * math.pi * (i + 0.5) / 24
        rays.append(f'<polygon points="240,180 {240 + 600 * math.cos(a1):.0f},{180 + 600 * math.sin(a1):.0f} '
                    f'{240 + 600 * math.cos(a2):.0f},{180 + 600 * math.sin(a2):.0f}" fill="{ray2}"/>')
    size = 54 if len(label) <= 8 else 38
    burst = starburst(label, "#fff", text_color, w=420, h=190, points=18, size=size).split(">", 1)[1].rsplit("</svg>", 1)[0]
    subtext = (f'<text x="240" y="318" font-family="Sans Serif" font-size="20" font-weight="bold" fill="#fff" '
               f'stroke="{INK}" stroke-width="1" text-anchor="middle">{sub}</text>') if sub else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect width="480" height="360" fill="{ray1}"/>
{"".join(rays)}
<g transform="translate(30 85)">{burst}</g>
{subtext}
</svg>'''


FLASHES = {"sneak": flash_svg("SNEAK ATTACK!", "#4b2a8a", "#6b3fd0", "#6b3fd0", "Steal ONE Gobo!"),
           "yoink": flash_svg("YOINK!", "#ff9a1f", "#ffd23f", "#e0202a", "Got it! Running home..."),
           "tooslow": flash_svg("TOO SLOW!", "#555", "#777", "#555", "You got nothing this time"),
           "rebirth": flash_svg("REBIRTH!", "#1aa38a", "#5EC8FF", "#b36bff", "Your Gobos make more money now!")}

CLOUD = f'''<svg xmlns="http://www.w3.org/2000/svg" width="90" height="44" viewBox="0 0 90 44">
<path d="M14 38 Q2 38 4 28 Q6 18 18 20 Q20 6 36 8 Q46 0 58 8 Q72 4 76 18 Q88 20 86 30 Q84 38 74 38 Z"
 fill="#fff" stroke="#b8d8f0" stroke-width="2"/>
</svg>'''


def steal_button_svg(ready):
    """A big shiny STEAL button (ready) or a grey WAIT button (cooling down)."""
    if ready:
        top, bottom, rim1, rim2, glow, label, size = "#ff5a5a", "#b8001c", "#fff3a0", "#ffb800", "#ffd23f", "STEAL!", 32
    else:
        top, bottom, rim1, rim2, glow, label, size = "#9aa3ad", "#4a525c", "#e6e9ee", "#8a939e", "#b8c0ca", "WAIT...", 28
    mask = ('<path d="M22 34 Q34 26 46 32 Q52 28 58 32 Q70 26 82 34 Q80 48 66 48 Q58 48 55 40 L49 40 Q46 48 38 48 '
            'Q24 48 22 34 Z" fill="#111" transform="translate(-6 0)"/>'
            '<ellipse cx="33" cy="38" rx="5" ry="3.5" fill="#fff"/><ellipse cx="60" cy="38" rx="5" ry="3.5" fill="#fff"/>'
            if ready else
            '<circle cx="44" cy="38" r="15" fill="#fff" stroke="#4a525c" stroke-width="3"/>'
            '<path d="M44 29 V38 L51 42" fill="none" stroke="#4a525c" stroke-width="3" stroke-linecap="round"/>')
    sparks = (SPARK.format(x=196, y=6, c="#fff") + SPARK.format(x=18, y=58, c="#fff")) if ready else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="220" height="80" viewBox="0 0 220 80">
<defs>
<linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>
<linearGradient id="rim" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{rim1}"/><stop offset="1" stop-color="{rim2}"/></linearGradient>
</defs>
<rect x="1" y="1" width="218" height="78" rx="39" fill="{glow}" opacity="0.25"/>
<rect x="5" y="5" width="210" height="70" rx="35" fill="{glow}" opacity="0.35"/>
<rect x="10" y="12" width="200" height="60" rx="30" fill="#000" opacity="0.3"/>
<rect x="10" y="8" width="200" height="60" rx="30" fill="url(#rim)"/>
<rect x="16" y="13" width="188" height="50" rx="25" fill="url(#face)"/>
<rect x="26" y="15" width="168" height="18" rx="9" fill="#fff" opacity="0.28"/>
{mask}
<text x="134" y="52" font-family="Marker" font-size="{size}" fill="#000" opacity="0.35" text-anchor="middle">{label}</text>
<text x="132" y="49" font-family="Marker" font-size="{size}" fill="#fff" text-anchor="middle">{label}</text>
{sparks}
</svg>'''


STEAL_READY = steal_button_svg(True)
STEAL_WAIT = steal_button_svg(False)


def slot_x(i):
    """Stage x of base slot i (1..8)."""
    return -230 + i * 55


MY_Y = -118


def house(x, roof, wall):
    return (f'<rect x="{x - 22}" y="70" width="44" height="40" fill="{wall}" stroke="#333" stroke-width="1.5"/>'
            f'<path d="M{x - 28} 72 L{x} 46 L{x + 28} 72 Z" fill="{roof}" stroke="#333" stroke-width="1.5"/>'
            f'<rect x="{x - 7}" y="92" width="14" height="18" fill="#6b3a10"/>'
            f'<rect x="{x - 18}" y="78" width="9" height="9" fill="#bfe8ff"/><rect x="{x + 9}" y="78" width="9" height="9" fill="#bfe8ff"/>')


def backdrop():
    """Home: Gobo Town at the top (with the STEAL button), the carpet, and your base."""
    pads = "".join(f'<ellipse cx="{240 + slot_x(i)}" cy="{180 - MY_Y + 22}" rx="24" ry="7" fill="#8fb6e8" '
                   f'stroke="#2f7fd6" stroke-width="2"/>' for i in range(1, 9))
    studs = "".join(f'<circle cx="{x}" cy="{y}" r="2.2" fill="#ffd23f"/>'
                    for x in range(20, 480, 30) for y in (144, 196))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect width="480" height="360" fill="#7ccf5a"/>
<rect x="0" y="0" width="480" height="126" fill="#9ed8ff"/>
<circle cx="440" cy="52" r="16" fill="#ffe066"/>
<rect x="0" y="108" width="480" height="20" fill="#6cbf4a"/>
{house(45, "#7a4bd6", "#e6d6ff")}{house(105, "#1aa38a", "#d0fff4")}{house(375, "#d9731a", "#ffe2c4")}{house(435, "#d63a3a", "#ffd6d6")}
<rect x="0" y="0" width="480" height="30" fill="#2d3748" opacity="0.35"/>
<text x="75" y="124" font-family="Sans Serif" font-size="10" font-weight="bold" fill="#1d4a1d" text-anchor="middle">OTHER PLAYERS' BASES</text>
<text x="405" y="124" font-family="Sans Serif" font-size="10" font-weight="bold" fill="#1d4a1d" text-anchor="middle">OTHER PLAYERS' BASES</text>
<rect x="0" y="140" width="480" height="60" fill="#c8202a"/>
<rect x="0" y="140" width="480" height="4" fill="#ffd23f"/>
<rect x="0" y="196" width="480" height="4" fill="#ffd23f"/>
{studs}
<path d="M0 132 Q30 120 48 150 L48 200 L0 200 Z" fill="#5a4a3a"/>
<path d="M4 150 Q22 138 36 158 L36 200 L4 200 Z" fill="#1a1410"/>
<text x="240" y="176" font-family="Sans Serif" font-size="13" font-weight="bold" fill="#ffd23f" text-anchor="middle" opacity="0.8">GOBO CARPET</text>
<rect x="3" y="258" width="474" height="99" rx="10" fill="#d6ecff" stroke="#2f7fd6" stroke-width="4"/>
<text x="470" y="352" font-family="Sans Serif" font-size="12" font-weight="bold" fill="#1f5fae" text-anchor="end">YOUR BASE</text>
{pads}
</svg>'''


def raid_x(i):
    return -165 + ((i - 1) % 4) * 110


def raid_y(i):
    return 60 - ((i - 1) // 4) * 100


def raid_backdrop(owner, floor, edge, ground):
    """Another player's base, full screen. Gobos stand on the 8 podiums."""
    pads = "".join(f'<ellipse cx="{240 + raid_x(i)}" cy="{180 - raid_y(i) + 22}" rx="30" ry="9" fill="{edge}" '
                   f'opacity="0.55"/>' for i in range(1, 9))
    tiles = "".join(f'<rect x="{x}" y="{y}" width="40" height="40" fill="#fff" opacity="0.18"/>'
                    for x in range(40, 440, 80) for y in (62, 142, 222))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect width="480" height="360" fill="{ground}"/>
<rect x="0" y="0" width="480" height="30" fill="#2d3748" opacity="0.35"/>
<rect x="24" y="40" width="432" height="262" rx="18" fill="{floor}" stroke="{edge}" stroke-width="8"/>
{tiles}
<rect x="190" y="292" width="100" height="20" fill="{floor}"/>
<rect x="200" y="300" width="80" height="50" rx="6" fill="#a0522d" opacity="0.8"/>
<rect x="150" y="30" width="180" height="30" rx="15" fill="{edge}"/>
<text x="240" y="52" font-family="Sans Serif" font-size="17" font-weight="bold" fill="#fff" text-anchor="middle">{owner}'S BASE</text>
{pads}
<text x="240" y="340" font-family="Sans Serif" font-size="12" font-weight="bold" fill="#fff" text-anchor="middle">Steal ONE Gobo: touch it and press E!</text>
</svg>'''


RAID_BASES = [("BOB", "#e6d6ff", "#7a4bd6", "#4b3a6b"),
              ("ZARA", "#d0fff4", "#1aa38a", "#2a5a52"),
              ("MAX", "#ffe2c4", "#d9731a", "#6b4a2a"),
              ("LUNA", "#ffe0f0", "#d63a8a", "#5a2a45")]


def card(title, title_color, lines):
    rows, y = [], 128
    for text, size, color in lines:
        rows.append(f'<text x="240" y="{y}" font-family="Sans Serif" font-size="{size}" '
                    f'font-weight="bold" fill="{color}" text-anchor="middle">{text}</text>')
        y += size + 8
    left = GOBO_ART[0].split(">", 1)[1].rsplit("</svg>", 1)[0]
    right = GOBO_ART[14].split(">", 1)[1].rsplit("</svg>", 1)[0].replace('id="', 'id="t_').replace("url(#", "url(#t_")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect x="16" y="12" width="448" height="336" rx="24" fill="#fffaf0" stroke="#e08a00" stroke-width="6" opacity="0.97"/>
<g transform="translate(30 16)">{left}</g>
<g transform="translate(380 16)">{right}</g>
<text x="240" y="72" font-family="Marker" font-size="38" fill="{title_color}" text-anchor="middle">{title}</text>
<text x="240" y="98" font-family="Sans Serif" font-size="13" fill="#888" text-anchor="middle">16 Gobos to collect, from Common to the SECRET Dragon Gobo!</text>
{"".join(rows)}
</svg>'''


TITLE_CARD = card("STEAL A GOBO!", "#e0600a", [
    ("Walk: Arrow keys or W A S D", 15, "#333"),
    ("Buy a Gobo on the red carpet: touch it + press E", 15, "#333"),
    ("Gobos in YOUR BASE make money every second", 15, "#333"),
    ("Click the STEAL button to sneak into a player's base!", 15, "#b02a2a"),
    ("Steal ONE Gobo (touch it + E), then you go back home", 15, "#b02a2a"),
    ("You can steal once every 1 minute and 30 seconds", 15, "#1f5fae"),
    ("X = sell  •  U = faster shoes  •  R = rebirth", 15, "#1f5fae"),
    ("Press SPACE to start", 22, "#e0600a"),
])

# ---------------------------------------------------------------- sounds (WAV)


def tone_wav(parts, rate=22050):
    """parts: list of (start_hz, end_hz, seconds, wave_kind)."""
    frames = bytearray()
    phase = 0.0
    for f0, f1, secs, kind in parts:
        n = int(rate * secs)
        for i in range(n):
            t = i / n
            f = f0 + (f1 - f0) * t
            phase += 2 * math.pi * f / rate
            s = math.sin(phase) if kind == "sine" else (1.0 if math.sin(phase) > 0 else -1.0) * 0.5
            env = min(1.0, i / 200) * (1 - t) ** 0.6
            frames += struct.pack("<h", int(s * env * 12000))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return bytes(buf.getvalue()), len(frames) // 2, rate


POP = tone_wav([(400, 1200, 0.12, "sine")])
CASH = tone_wav([(988, 988, 0.09, "sine"), (1319, 1319, 0.25, "sine")])
OUCH = tone_wav([(500, 150, 0.45, "square")])
WHOOSH = tone_wav([(200, 1400, 0.35, "sine")])

# ---------------------------------------------------------------- block DSL


class B:
    """A Scratch block. Inputs are UPPERCASE kwargs; fields go in `fields`."""

    def __init__(self, opcode, fields=None, mutation=None, **inputs):
        self.opcode, self.fields, self.mutation, self.inputs = opcode, fields or {}, mutation, inputs


class V:
    """Variable reporter."""

    def __init__(self, name):
        self.name = name


class BC:
    """Broadcast message input."""

    def __init__(self, name):
        self.name = name


MENUS = {
    ("sensing_touchingobject", "TOUCHINGOBJECTMENU"): ("sensing_touchingobjectmenu", "TOUCHINGOBJECTMENU"),
    ("looks_switchbackdropto", "BACKDROP"): ("looks_backdrops", "BACKDROP"),
    ("sensing_keypressed", "KEY_OPTION"): ("sensing_keyoptions", "KEY_OPTION"),
    ("sensing_distanceto", "DISTANCETOMENU"): ("sensing_distancetomenu", "DISTANCETOMENU"),
    ("motion_pointtowards", "TOWARDS"): ("motion_pointtowards_menu", "TOWARDS"),
    ("sensing_of", "OBJECT"): ("sensing_of_object_menu", "OBJECT"),
    ("looks_switchcostumeto", "COSTUME"): ("looks_costume", "COSTUME"),
    ("control_create_clone_of", "CLONE_OPTION"): ("control_create_clone_of_menu", "CLONE_OPTION"),
    ("sound_play", "SOUND_MENU"): ("sound_sounds_menu", "SOUND_MENU"),
}
TEXT_INPUTS = {"OPERAND1", "OPERAND2", "STRING1", "STRING2", "MESSAGE", "ITEM"}
STOP_MUTATION = {"tagName": "mutation", "children": [], "hasnext": "false"}

GLOBAL_VARS = ["Money", "Income", "Rebirths", "Multiplier", "Rebirth Cost", "Speed", "Upgrade Cost",
               "Scene", "Steal Cooldown", "Raid Time", "Home X", "Home Y", "Tip",
               "Flash", "FX", "FX X", "FX Y"]
LISTS = {"My Slots": [0] * 8,
         "Names": [g[0] for g in GOBOS], "Tiers": [g[1] for g in GOBOS],
         "Prices": [g[2] for g in GOBOS], "Rates": [g[3] for g in GOBOS], "Chances": CUMULATIVE}
BROADCASTS = ["title", "start", "tip", "raid start", "raid end", "flash", "fx"]


def vid(name):
    return "var-" + name.lower().replace(" ", "-")


def lid(name):
    return "list-" + name.lower().replace(" ", "-")


def bid(name):
    return "bc-" + name.replace(" ", "-")


class Compiler:
    def __init__(self, prefix, local_vars=()):
        self.prefix, self.n, self.blocks = prefix, 0, {}
        self.local = {v: f"{prefix}-{vid(v)}" for v in local_vars}

    def var_id(self, name):
        if name in self.local:
            return self.local[name]
        assert name in GLOBAL_VARS, name
        return vid(name)

    def new_id(self):
        self.n += 1
        return f"{self.prefix}-{self.n}"

    def emit(self, node, parent):
        i = self.new_id()
        blk = {"opcode": node.opcode, "next": None, "parent": parent, "inputs": {}, "fields": {},
               "shadow": False, "topLevel": False}
        self.blocks[i] = blk
        for name, val in node.inputs.items():
            blk["inputs"][name] = self.input(node.opcode, name, val, i)
        for name, val in node.fields.items():
            if name == "VARIABLE":
                blk["fields"][name] = [val, self.var_id(val)]
            elif name == "LIST":
                assert val in LISTS, val
                blk["fields"][name] = [val, lid(val)]
            elif name == "BROADCAST_OPTION":
                blk["fields"][name] = [val, bid(val)]
            else:
                blk["fields"][name] = [val, None]
        if node.mutation:
            blk["mutation"] = node.mutation
        return i

    def reporter(self, val, pid):
        if isinstance(val, V):
            return [12, val.name, self.var_id(val.name)]
        return self.emit(val, pid)

    def input(self, op, name, val, pid):
        shadow_type = 10 if name in TEXT_INPUTS else 7 if name == "INDEX" else 4
        if (op, name) in MENUS:
            sop, field = MENUS[(op, name)]
            sid = self.new_id()
            literal = val if isinstance(val, str) else ""
            self.blocks[sid] = {"opcode": sop, "next": None, "parent": pid, "inputs": {},
                                "fields": {field: [literal, None]}, "shadow": True, "topLevel": False}
            if isinstance(val, (V, B)):
                return [3, self.reporter(val, pid), sid]
            return [1, sid]
        if isinstance(val, list):
            return [2, self.stack(val, pid)]
        if isinstance(val, BC):
            return [1, [11, val.name, bid(val.name)]]
        if isinstance(val, (V, B)):
            if isinstance(val, B) and (name == "CONDITION" or op in ("operator_and", "operator_or", "operator_not")):
                return [2, self.emit(val, pid)]
            return [3, self.reporter(val, pid), [shadow_type, ""]]
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return [1, [shadow_type, str(val)]]

    def stack(self, nodes, parent):
        first = prev = None
        for node in flat(nodes):
            i = self.emit(node, prev if prev else parent)
            if prev:
                self.blocks[prev]["next"] = i
            else:
                first = i
            prev = i
        return first

    def script(self, nodes, x, y):
        first = self.stack(nodes, None)
        self.blocks[first].update(topLevel=True, x=x, y=y)


def flat(nodes):
    """Allow helpers that return a list of blocks inside a script list."""
    out = []
    for n in nodes:
        out.extend(flat(n) if isinstance(n, list) else [n])
    return out


# Handy shortcuts ---------------------------------------------------------------
def flag():                 return B("event_whenflagclicked")
def when_msg(m):            return B("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": m})
def when_key(k):            return B("event_whenkeypressed", fields={"KEY_OPTION": k})
def broadcast(m):           return B("event_broadcast", BROADCAST_INPUT=BC(m))
def broadcast_wait(m):      return B("event_broadcastandwait", BROADCAST_INPUT=BC(m))
def set_var(n, v):          return B("data_setvariableto", fields={"VARIABLE": n}, VALUE=v)
def change_var(n, v):       return B("data_changevariableby", fields={"VARIABLE": n}, VALUE=v)
def item(lst, i):           return B("data_itemoflist", fields={"LIST": lst}, INDEX=i)
def replace(lst, i, v):     return B("data_replaceitemoflist", fields={"LIST": lst}, INDEX=i, ITEM=v)
def clear_list(lst):        return B("data_deletealloflist", fields={"LIST": lst})
def add_to(lst, v):         return B("data_addtolist", fields={"LIST": lst}, ITEM=v)
def forever(body):          return B("control_forever", SUBSTACK=body)
def repeat_until(c, body):  return B("control_repeat_until", CONDITION=c, SUBSTACK=body)
def wait_until(c):          return B("control_wait_until", CONDITION=c)
def wait(s):                return B("control_wait", DURATION=s)
def if_(c, body):           return B("control_if", CONDITION=c, SUBSTACK=body)
def if_else(c, a, b):       return B("control_if_else", CONDITION=c, SUBSTACK=a, SUBSTACK2=b)
def eq(a, b):               return B("operator_equals", OPERAND1=a, OPERAND2=b)
def lt(a, b):               return B("operator_lt", OPERAND1=a, OPERAND2=b)
def gt(a, b):               return B("operator_gt", OPERAND1=a, OPERAND2=b)
def and_(a, b, *more):      return and_(B("operator_and", OPERAND1=a, OPERAND2=b), *more) if more else B("operator_and", OPERAND1=a, OPERAND2=b)
def or_(a, b):              return B("operator_or", OPERAND1=a, OPERAND2=b)
def not_(a):                return B("operator_not", OPERAND=a)
def add(a, b):              return B("operator_add", NUM1=a, NUM2=b)
def sub(a, b):              return B("operator_subtract", NUM1=a, NUM2=b)
def mul(a, b):              return B("operator_multiply", NUM1=a, NUM2=b)
def div(a, b):              return B("operator_divide", NUM1=a, NUM2=b)
def mathop(op, a):          return B("operator_mathop", fields={"OPERATOR": op}, NUM=a)
def round_(a):              return B("operator_round", NUM=a)
def rand(a, b):             return B("operator_random", FROM=a, TO=b)
def join(*parts):           return parts[0] if len(parts) == 1 else B("operator_join", STRING1=parts[0], STRING2=join(*parts[1:]))
def key(k):                 return B("sensing_keypressed", KEY_OPTION=k)
def touching(s):            return B("sensing_touchingobject", TOUCHINGOBJECTMENU=s)
def distance_to(s):         return B("sensing_distanceto", DISTANCETOMENU=s)
def prop_of(p, s):          return B("sensing_of", fields={"PROPERTY": p}, OBJECT=s)
def timer():                return B("sensing_timer")
def goto_xy(x, y):          return B("motion_gotoxy", X=x, Y=y)
def glide(s, x, y):         return B("motion_glidesecstoxy", SECS=s, X=x, Y=y)
def set_y(y):               return B("motion_sety", Y=y)
def set_x(x):               return B("motion_setx", X=x)
def change_x(d):            return B("motion_changexby", DX=d)
def change_y(d):            return B("motion_changeyby", DY=d)
def x_pos():                return B("motion_xposition")
def y_pos():                return B("motion_yposition")
def point_dir(d):           return B("motion_pointindirection", DIRECTION=d)
def rot_style(s):           return B("motion_setrotationstyle", fields={"STYLE": s})
def say(m):                 return B("looks_say", MESSAGE=m)
def say_for(m, s):          return B("looks_sayforsecs", MESSAGE=m, SECS=s)
def costume(c):             return B("looks_switchcostumeto", COSTUME=c)
def switch_backdrop(b):     return B("looks_switchbackdropto", BACKDROP=b)
def show_var(n):            return B("data_showvariable", fields={"VARIABLE": n})
def hide_var(n):            return B("data_hidevariable", fields={"VARIABLE": n})
def when_clicked():         return B("event_whenthisspriteclicked")
def show():                 return B("looks_show")
def hide():                 return B("looks_hide")
def size(n):                return B("looks_setsizeto", SIZE=n)
def front():                return B("looks_gotofrontback", fields={"FRONT_BACK": "front"})
def back():                 return B("looks_gotofrontback", fields={"FRONT_BACK": "back"})
def play(s):                return B("sound_play", SOUND_MENU=s)
def clone_me():             return B("control_create_clone_of", CLONE_OPTION="_myself_")
def when_cloned():          return B("control_start_as_clone")
def delete_clone():         return B("control_delete_this_clone")


def tip(*parts):
    """Show a message in the player's speech bubble."""
    return [set_var("Tip", join(*parts)), broadcast("tip")]


def find_free(lst):
    """Set local `found` to the first empty slot of `lst` (0 if full). Unrolled so it runs in one frame."""
    return [set_var("found", 0)] + [if_(eq(item(lst, i), 0), [set_var("found", i)]) for i in range(8, 0, -1)]


def any_key(*keys):
    cond = key(keys[0])
    for k in keys[1:]:
        cond = or_(cond, key(k))
    return cond


NAME = item("Names", V("rarity"))
TIER = item("Tiers", V("rarity"))
PRICE = item("Prices", V("rarity"))
RATE = item("Rates", V("rarity"))
BOB = round_(mul(3, mathop("sin", add(mul(timer(), 300), mul(V("slot"), 45)))))
SLOT_X = add(-230, mul(V("slot"), 55))
HOME_X, HOME_Y = 0, -160      # player start, inside YOUR BASE
SAFE_Y = -80                  # the player is home once below this line

def sin_(deg):              return mathop("sin", deg)
def mod(a, b):              return B("operator_mod", NUM1=a, NUM2=b)
def change_size(n):         return B("looks_changesizeby", CHANGE=n)
def set_effect(e, v):       return B("looks_seteffectto", fields={"EFFECT": e}, VALUE=v)
def change_effect(e, v):    return B("looks_changeeffectby", fields={"EFFECT": e}, CHANGE=v)
def clear_effects():        return B("looks_cleargraphiceffects")
def repeat(n, body):        return B("control_repeat", TIMES=n, SUBSTACK=body)


def wobble(amount, speed, phase):
    """Rock gently left and right, like a cartoon."""
    return point_dir(add(90, mul(amount, sin_(add(mul(timer(), speed), phase)))))


def flash(name):
    """Full-screen comic flash (SNEAK ATTACK!, YOINK!, ...)."""
    return [set_var("Flash", name), broadcast("flash")]


def fx_here(name, back_to_kind):
    """Pop a comic starburst (KA-CHING!, WOW!, ...) where this Gobo is."""
    return [set_var("fx", name), set_var("kind", 8), clone_me(), set_var("kind", back_to_kind)]


# ---------------------------------------------------------------- Stage

STEAL_COOLDOWN = 90   # seconds between steals (1 minute 30 seconds)
RAID_SECONDS = 20     # time you have inside another player's base

stage = Compiler("stage")
init = [set_var("Money", 50), set_var("Income", 0), set_var("Rebirths", 0), set_var("Multiplier", 1),
        set_var("Rebirth Cost", 20000), set_var("Speed", 4), set_var("Upgrade Cost", 200),
        set_var("Scene", 1), set_var("Steal Cooldown", 0), set_var("Raid Time", 0), set_var("Tip", ""),
        clear_list("My Slots")] + [add_to("My Slots", 0) for _ in range(8)]
income = [set_var("Income", 0)] + [
    if_(gt(item("My Slots", i), 0), [change_var("Income", item("Rates", item("My Slots", i)))])
    for i in range(1, 9)] + [set_var("Income", mul(V("Income"), V("Multiplier")))]
stage.script([
    flag(), *init, switch_backdrop("Gobo Land"), hide_var("Raid Time"),
    broadcast_wait("title"),
    broadcast("start"),
    forever([
        wait(1),
        *income,
        change_var("Money", V("Income")),
        if_(gt(V("Steal Cooldown"), 0), [change_var("Steal Cooldown", -1)]),
        if_(eq(V("Scene"), 2), [
            change_var("Raid Time", -1),
            if_(lt(V("Raid Time"), 1), [*flash("tooslow"), *tip("Too slow! You went home with nothing."),
                                        broadcast("raid end")]),
        ]),
    ]),
], 20, 20)
stage.script([
    when_msg("raid start"),
    switch_backdrop(rand(2, 1 + len(RAID_BASES))),
    show_var("Raid Time"),
], 20, 600)
stage.script([
    when_msg("raid end"),
    set_var("Scene", 1),
    switch_backdrop("Gobo Land"),
    hide_var("Raid Time"),
], 20, 750)

# ---------------------------------------------------------------- STEAL button

button = Compiler("button", local_vars=["found"])
button.script([flag(), rot_style("all around"), point_dir(90), goto_xy(0, 100), costume("ready"), size(100),
               front(), say(""), show()], 20, 20)
button.script([
    when_msg("start"),
    forever([
        if_else(eq(V("Scene"), 2), [hide()], [
            show(),
            if_else(gt(V("Steal Cooldown"), 0),
                    [costume("wait"), size(90), point_dir(90), say(join("Ready in ", V("Steal Cooldown"), "s"))],
                    [costume("ready"), say(""), wobble(4, 350, 0),
                     if_else(touching("_mouse_"),
                             [size(add(114, mul(3, sin_(mul(timer(), 900)))))],
                             [size(add(100, mul(6, sin_(mul(timer(), 400)))))])]),
        ]),
    ]),
], 20, 160)
button.script([
    when_clicked(),
    if_(eq(V("Scene"), 1), [
        if_else(gt(V("Steal Cooldown"), 0),
                [*tip("You can steal again in ", V("Steal Cooldown"), " seconds!"),
                 repeat(3, [point_dir(80), wait(0.05), point_dir(100), wait(0.05)]), point_dir(90)],
                [*find_free("My Slots"),
                 if_else(eq(V("found"), 0),
                         tip("Your base is full! Sell a Gobo (X) first."),
                         [size(80), wait(0.08), size(125), wait(0.08),
                          set_var("Scene", 2),
                          set_var("Steal Cooldown", STEAL_COOLDOWN),
                          set_var("Raid Time", RAID_SECONDS),
                          set_var("Home X", prop_of("x position", "Player")),
                          set_var("Home Y", prop_of("y position", "Player")),
                          play("whoosh"),
                          *flash("sneak"),
                          broadcast("raid start"),
                          *tip("Sneaky sneaky... Touch ONE Gobo and press E!")])]),
    ]),
], 480, 20)

# ---------------------------------------------------------------- Player

player = Compiler("player", local_vars=["step", "moving"])
player.script([
    flag(), rot_style("left-right"), point_dir(90), goto_xy(HOME_X, HOME_Y), costume("idle"), size(100),
    show(), front(), say(""),
], 20, 20)
player.script([
    when_msg("start"),
    forever([
        set_var("step", V("Speed")), set_var("moving", 0),
        if_(any_key("right arrow", "d"), [point_dir(90), change_x(V("step")), set_var("moving", 1)]),
        if_(any_key("left arrow", "a"), [point_dir(-90), change_x(sub(0, V("step"))), set_var("moving", 1)]),
        if_(any_key("up arrow", "w"), [change_y(V("step")), set_var("moving", 1)]),
        if_(any_key("down arrow", "s"), [change_y(sub(0, V("step"))), set_var("moving", 1)]),
        if_(gt(y_pos(), 148), [set_y(148)]),
        if_(lt(y_pos(), -160), [set_y(-160)]),
        # Walking animation: swap legs 8 times a second.
        if_else(eq(V("moving"), 1),
                [costume(join("walk", add(1, mod(mathop("floor", mul(timer(), 8)), 2))))],
                [costume("idle")]),
    ]),
], 20, 200)
player.script([when_msg("tip"), say_for(V("Tip"), 2)], 480, 20)
player.script([when_msg("raid start"), goto_xy(0, -112), point_dir(90), front()], 480, 120)
player.script([when_msg("raid end"), goto_xy(V("Home X"), V("Home Y")), front()], 480, 200)
player.script([
    when_key("u"),
    if_else(lt(V("Money"), V("Upgrade Cost")),
            tip("Faster shoes cost $", V("Upgrade Cost")),
            [change_var("Money", sub(0, V("Upgrade Cost"))),
             change_var("Speed", 0.5),
             set_var("Upgrade Cost", mul(V("Upgrade Cost"), 3)),
             set_var("FX", "zoom"), set_var("FX X", x_pos()), set_var("FX Y", add(y_pos(), 45)), broadcast("fx"),
             *tip("Zoom! Your speed is now ", V("Speed"))]),
], 480, 300)
player.script([
    when_key("r"),
    if_else(or_(lt(V("Money"), V("Rebirth Cost")), eq(V("Scene"), 2)),
            tip("Rebirth costs $", V("Rebirth Cost"), ". It resets your Gobos but you earn more!"),
            [set_var("Money", 0),
             *[replace("My Slots", i, 0) for i in range(1, 9)],
             change_var("Rebirths", 1),
             set_var("Multiplier", add(1, mul(V("Rebirths"), 0.5))),
             set_var("Rebirth Cost", mul(20000, mul(add(V("Rebirths"), 1), add(V("Rebirths"), 1)))),
             *flash("rebirth"),
             *tip("REBIRTH! Now your Gobos make x", V("Multiplier"), " money!")]),
], 480, 560)

# ---------------------------------------------------------------- Gobo (all Gobos are clones)
# kind: 1 = on the carpet, 2 = in my base, 6 = in another player's base (can be stolen),
#       7 = a coin popping out of one of my Gobos, 8 = a comic starburst

pick_rarity = [set_var("r", rand(1, 10000)), set_var("rarity", 1)] + [
    if_(gt(V("r"), item("Chances", k)), [set_var("rarity", k + 1)]) for k in range(1, N_GOBOS)]
E = any_key("e", "space")
LOOK = [  # blink now and then
    if_else(eq(V("blink"), 1),
            [if_(eq(rand(1, 4), 1), [set_var("blink", 0)])],
            [if_(eq(rand(1, 150), 1), [set_var("blink", 1)])]),
    costume(add(V("rarity"), mul(N_GOBOS, V("blink")))),
]

gobo = Compiler("gobo", local_vars=["kind", "rarity", "slot", "found", "r", "orig", "blink", "fx"])
gobo.script([flag(), hide(), rot_style("all around"), point_dir(90), clear_effects(),
             set_var("kind", 0), set_var("orig", 1), set_var("blink", 0)], 20, 20)
gobo.script([
    when_msg("start"),
    forever([wait_until(eq(V("Scene"), 1)), set_var("kind", 1), clone_me(), wait(rand(1.5, 3))]),
], 20, 160)
gobo.script([
    # Fill the other player's base with random Gobos.
    when_msg("raid start"),
    if_(eq(V("orig"), 1), [
        set_var("kind", 6),
        *[[set_var("slot", i), *pick_rarity, clone_me()] for i in range(1, 9)],
    ]),
], 20, 280)
gobo.script([when_msg("raid end"), if_(eq(V("kind"), 6), [delete_clone()])], 20, 800)
gobo.script([
    # A starburst somewhere else on screen (for example ZOOM! over the player).
    when_msg("fx"),
    if_(eq(V("orig"), 1), [goto_xy(V("FX X"), V("FX Y")), set_var("fx", V("FX")), set_var("kind", 8), clone_me()]),
], 20, 900)

carpet = [
    *pick_rarity,
    costume(V("rarity")), size(60), goto_xy(-225, 12), back(),
    if_(not_(lt(V("rarity"), RARE_FROM)), [
        *tip("WOW! A ", TIER, " ", NAME, " is on the carpet!"), play("cash"), *fx_here("wow", 1)]),
    repeat_until(or_(gt(x_pos(), 232), not_(eq(V("kind"), 1))), [
        if_else(eq(V("Scene"), 2), [hide(), say("")], [
            show(),
            change_x(1.2),
            # Waddle: hop and rock from side to side.
            set_y(add(10, mul(6, mathop("abs", sin_(mul(x_pos(), 6)))))),
            wobble(10, 0, mul(x_pos(), 6)),
            *LOOK,
            if_else(lt(distance_to("Player"), 45),
                    [say(join(NAME, " (", TIER, ") $", PRICE, " = $", RATE, "/s"))],
                    [say(join("$", PRICE))]),
            if_(and_(touching("Player"), E), [
                if_else(lt(V("Money"), PRICE),
                        tip("You need $", PRICE, " to buy this ", NAME),
                        [*find_free("My Slots"),
                         if_else(eq(V("found"), 0),
                                 tip("Your base is full! Stand on a Gobo and press X to sell it."),
                                 [change_var("Money", sub(0, PRICE)),
                                  replace("My Slots", V("found"), V("rarity")),
                                  *fx_here("kaching", 1),
                                  set_var("slot", V("found")), set_var("kind", 2),
                                  play("cash"), *tip("You bought a ", NAME, "!")])]),
            ]),
        ]),
    ]),
    if_(eq(V("kind"), 1), [delete_clone()]),
]

RAID_X = add(-165, mul(mod(sub(V("slot"), 1), 4), 110))
RAID_Y = sub(60, mul(mathop("floor", div(sub(V("slot"), 1), 4)), 100))
raid = [
    costume(V("rarity")), size(60), show(),
    if_(not_(lt(V("rarity"), RARE_FROM)), [*tip("WOW! This base has a ", TIER, " ", NAME, "!")]),
    repeat_until(not_(eq(V("kind"), 6)), [
        goto_xy(RAID_X, add(RAID_Y, BOB)),
        *LOOK,
        # Gobos shiver when the thief comes close.
        if_else(lt(distance_to("Player"), 45),
                [wobble(9, 2500, 0), say(join("Eek! ", NAME, " (", TIER, ") $", RATE, "/s"))],
                [wobble(5, 200, mul(V("slot"), 50)), say("")]),
        if_(and_(touching("Player"), E, eq(V("Scene"), 2)), [
            *find_free("My Slots"),
            if_(gt(V("found"), 0), [
                replace("My Slots", V("found"), V("rarity")),
                set_var("slot", V("found")), set_var("kind", 2),
                play("cash"), *flash("yoink"), *tip("YOINK! You stole a ", NAME, "!"),
                broadcast("raid end"),
            ]),
        ]),
    ]),
]

mine = [  # kind 2: sitting in my base, making money
    goto_xy(SLOT_X, add(MY_Y, BOB)),
    wobble(5, 200, mul(V("slot"), 50)),
    *LOOK,
    if_(not_(eq(item("My Slots", V("slot")), V("rarity"))), [delete_clone()]),
    if_else(lt(distance_to("Player"), 40),
            [say(join(NAME, " $", RATE, "/s  (X = sell)"))], [say("")]),
    # Now and then a coin pops out.
    if_(eq(rand(1, 70), 1), [set_var("kind", 7), clone_me(), set_var("kind", 2)]),
    if_(and_(touching("Player"), key("x")), [
        change_var("Money", round_(div(PRICE, 2))),
        replace("My Slots", V("slot"), 0),
        *tip("Sold ", NAME, " for $", round_(div(PRICE, 2))),
        *fx_here("sold", 2),
        delete_clone(),
    ]),
]

coin = [
    say(""), costume("coin"), size(70), point_dir(90), goto_xy(x_pos(), add(y_pos(), 18)), show(), front(),
    repeat(14, [change_y(2.5), change_effect("GHOST", 7)]),
    delete_clone(),
]

burst = [
    say(""), costume(V("fx")), clear_effects(), size(20), point_dir(rand(80, 100)), show(), front(), play("pop"),
    repeat(5, [change_size(22)]),
    repeat(3, [change_size(-6)]),
    wait(0.5),
    repeat(8, [change_effect("GHOST", 12), change_y(2)]),
    delete_clone(),
]

gobo.script([
    when_cloned(),
    set_var("orig", 0),
    if_(eq(V("kind"), 7), coin),
    if_(eq(V("kind"), 8), burst),
    if_(eq(V("kind"), 1), carpet),
    if_(eq(V("kind"), 6), raid),
    say(""), costume(V("rarity")), size(60), show(), back(),
    glide(0.5, SLOT_X, MY_Y),
    forever([if_else(eq(V("Scene"), 2), [hide(), say("")], [show(), *mine])]),
], 420, 20)

# ---------------------------------------------------------------- comic flash (full screen)

flash_sprite = Compiler("flash")
flash_sprite.script([flag(), hide(), goto_xy(0, 0)], 20, 20)
flash_sprite.script([
    when_msg("flash"),
    costume(V("Flash")), clear_effects(), size(50), goto_xy(0, 0), show(), front(),
    repeat(5, [change_size(12)]),
    wait(0.45),
    repeat(10, [change_effect("GHOST", 10), change_size(2)]),
    hide(),
], 20, 120)

# ---------------------------------------------------------------- clouds

cloud = Compiler("cloud")
cloud.script([flag(), hide()], 20, 20)
cloud.script([
    when_msg("start"),
    repeat(4, [goto_xy(rand(-230, 230), rand(140, 165)), size(rand(50, 90)), clone_me()]),
], 20, 100)
cloud.script([
    when_cloned(),
    back(),
    forever([
        if_else(eq(V("Scene"), 2), [hide()], [show()]),
        change_x(0.3),
        if_(gt(x_pos(), 235), [set_x(-235)]),
    ]),
], 20, 220)

# ---------------------------------------------------------------- title card

message = Compiler("message")
message.script([
    when_msg("title"),
    rot_style("all around"), goto_xy(0, 0), costume("title"), show(), front(),
    repeat_until(key("space"), [size(add(100, mul(2, sin_(mul(timer(), 300))))), wobble(1.5, 200, 0)]),
    size(100), point_dir(90), hide(),
], 20, 20)

# ---------------------------------------------------------------- assemble

assets = {}


def svg_costume(name, svg, cx=None, cy=None):
    data = svg.encode()
    md5 = hashlib.md5(data).hexdigest()
    assets[md5 + ".svg"] = data
    w = float(svg.split('width="', 1)[1].split('"', 1)[0])
    h = float(svg.split('height="', 1)[1].split('"', 1)[0])
    return {"name": name, "bitmapResolution": 1, "dataFormat": "svg", "assetId": md5,
            "md5ext": md5 + ".svg", "rotationCenterX": cx if cx is not None else w / 2,
            "rotationCenterY": cy if cy is not None else h / 2}


def wav_sound(name, wav):
    data, count, rate = wav
    md5 = hashlib.md5(data).hexdigest()
    assets[md5 + ".wav"] = data
    return {"name": name, "assetId": md5, "dataFormat": "wav", "format": "", "rate": rate,
            "sampleCount": count, "md5ext": md5 + ".wav"}


def sprite(comp, name, costumes, sounds, layer, x=0, y=0, visible=True, style="left-right"):
    return {"isStage": False, "name": name,
            "variables": {vid_: [v, 0] for v, vid_ in comp.local.items()},
            "lists": {}, "broadcasts": {}, "blocks": comp.blocks, "comments": {},
            "currentCostume": 0, "costumes": costumes, "sounds": sounds, "volume": 100,
            "layerOrder": layer, "visible": visible, "x": x, "y": y, "size": 100, "direction": 90,
            "draggable": False, "rotationStyle": style}


START_VALUES = {"Money": 50, "Multiplier": 1, "Rebirth Cost": 20000, "Speed": 4, "Upgrade Cost": 200,
                "Scene": 1, "Tip": "", "Flash": "sneak", "FX": "wow"}
targets = [
    {"isStage": True, "name": "Stage",
     "variables": {vid(v): [v, START_VALUES.get(v, 0)] for v in GLOBAL_VARS},
     "lists": {lid(n): [n, vals] for n, vals in LISTS.items()},
     "broadcasts": {bid(b): b for b in BROADCASTS}, "blocks": stage.blocks,
     "comments": {}, "currentCostume": 0,
     "costumes": [svg_costume("Gobo Land", backdrop(), 240, 180)]
                 + [svg_costume(f"{r[0].title()}'s Base", raid_backdrop(*r), 240, 180) for r in RAID_BASES],
     "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60, "videoTransparency": 50,
     "videoState": "on", "textToSpeechLanguage": None},
    sprite(cloud, "Cloud", [svg_costume("cloud", CLOUD)], [], 1, visible=False),
    sprite(gobo, "Gobo", [svg_costume(g[0], art) for g, art in zip(GOBOS, GOBO_ART)]
           + [svg_costume(g[0] + " blink", art) for g, art in zip(GOBOS, GOBO_BLINK)]
           + [svg_costume("coin", COIN)] + [svg_costume(n, art) for n, art in BURSTS.items()],
           [wav_sound("pop", POP), wav_sound("cash", CASH)], 2, visible=False, style="all around"),
    sprite(player, "Player", [svg_costume("idle", PLAYER_FRAMES[0]), svg_costume("walk1", PLAYER_FRAMES[1]),
                              svg_costume("walk2", PLAYER_FRAMES[2])], [wav_sound("ouch", OUCH)], 3, HOME_X, HOME_Y),
    sprite(button, "STEAL Button", [svg_costume("ready", STEAL_READY), svg_costume("wait", STEAL_WAIT)],
           [wav_sound("whoosh", WHOOSH)], 4, 0, 100, style="all around"),
    sprite(flash_sprite, "Comic Flash", [svg_costume(n, art, 240, 180) for n, art in FLASHES.items()], [], 5,
           visible=False),
    sprite(message, "Message", [svg_costume("title", TITLE_CARD, 240, 180)], [], 6, visible=False, style="all around"),
]


def monitor(name, x, y):
    return {"id": vid(name), "mode": "default", "opcode": "data_variable",
            "params": {"VARIABLE": name}, "spriteName": None, "value": 0, "width": 0, "height": 0,
            "x": x, "y": y, "visible": True, "sliderMin": 0, "sliderMax": 100, "isDiscrete": True}


project = {
    "targets": targets,
    "monitors": [monitor("Money", 5, 3), monitor("Income", 140, 3), monitor("Rebirths", 270, 3),
                 dict(monitor("Raid Time", 380, 3), visible=False)],
    "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "build_sb3.py"},
}

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("project.json", json.dumps(project))
    for fname, data in assets.items():
        z.writestr(fname, data)

if __name__ == "__main__":
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {len(assets)} assets)")
