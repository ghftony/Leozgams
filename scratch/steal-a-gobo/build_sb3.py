#!/usr/bin/env python3
"""Build "Steal a Gobo" as a Scratch 3 project file (Steal_a_Gobo.sb3).

A "Steal a Brainrot" style game with Gobos: buy Gobos from the red carpet, keep them in
your base so they make money, steal Gobos from the Rival's base, and stop the Rival from
stealing yours.

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

#        name            tier         price    $/sec  chance (out of 1000)
GOBOS = [("Gobo",         "Common",       10,      1, 550),
         ("Leaf Gobo",    "Rare",         60,      5, 250),
         ("Ice Gobo",     "Epic",        300,     20, 110),
         ("Fire Gobo",    "Legendary",  1500,     80,  50),
         ("Galaxy Gobo",  "Mythic",     7500,    350,  25),
         ("Golden Gobo",  "Gobo God",  30000,   1500,  12),
         ("Rainbow Gobo", "Secret",   150000,   7000,   3)]
CUMULATIVE = [sum(g[4] for g in GOBOS[:i + 1]) for i in range(len(GOBOS))]
assert CUMULATIVE[-1] == 1000

# ---------------------------------------------------------------- art (SVG)

SPARK = '<path d="M{x} {y} l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2 z" fill="{c}"/>'


def gobo_svg(body, edge, extra_back="", extra_front="", defs=""):
    """Gobo: a round little creature with a spiky flame-like top and big eyes."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="70" height="72" viewBox="0 0 70 72">
<defs>{defs}</defs>
{extra_back}
<ellipse cx="25" cy="66" rx="7" ry="4" fill="{edge}"/>
<ellipse cx="45" cy="66" rx="7" ry="4" fill="{edge}"/>
<path d="M35 3 L39 19 L50 7 L48 22 L60 17 L53 31 Q60 46 52 57 Q35 70 18 57 Q10 46 17 31 L9 22 L22 24 L21 9 L30 20 Z"
 fill="{body}" stroke="{edge}" stroke-width="2.5" stroke-linejoin="round"/>
<path d="M17 40 Q8 42 6 50 Q13 50 18 46 Z" fill="{body}" stroke="{edge}" stroke-width="2" stroke-linejoin="round"/>
<path d="M53 40 Q62 42 64 50 Q57 50 52 46 Z" fill="{body}" stroke="{edge}" stroke-width="2" stroke-linejoin="round"/>
<ellipse cx="28" cy="40" rx="5.5" ry="6.5" fill="#fff" stroke="#6b3a10" stroke-width="1.2"/>
<ellipse cx="42" cy="40" rx="5.5" ry="6.5" fill="#fff" stroke="#6b3a10" stroke-width="1.2"/>
<circle cx="29" cy="41" r="3.2" fill="#4a2508"/>
<circle cx="43" cy="41" r="3.2" fill="#4a2508"/>
<circle cx="30" cy="39.8" r="1" fill="#fff"/>
<circle cx="44" cy="39.8" r="1" fill="#fff"/>
<path d="M31 51 Q35 54 39 51" fill="none" stroke="#6b3a10" stroke-width="1.8" stroke-linecap="round"/>
{extra_front}
</svg>'''


GOBO_ART = [
    gobo_svg("#FFBF1F", "#E08A00"),
    gobo_svg("#7ED957", "#3B8F2B",
             extra_front='<path d="M35 4 Q46 -2 50 6 Q42 10 35 4 Z" fill="#3B8F2B"/>'),
    gobo_svg("#AEEFFF", "#2A8FC8",
             extra_front=SPARK.format(x=10, y=12, c="#fff") + SPARK.format(x=58, y=36, c="#fff")),
    gobo_svg("#FF7A2F", "#B8330A",
             extra_back='<path d="M35 0 L44 14 L56 4 L54 20 L68 18 L58 34 L12 34 L2 18 L16 20 L14 4 L26 14 Z" '
                        'fill="#FFD23F" opacity="0.85"/>'),
    gobo_svg("url(#gal)", "#3A1F80",
             defs='<radialGradient id="gal" cx="0.4" cy="0.4" r="0.7"><stop offset="0" stop-color="#B58CFF"/>'
                  '<stop offset="1" stop-color="#3B1A8C"/></radialGradient>',
             extra_front=SPARK.format(x=22, y=26, c="#fff") + SPARK.format(x=48, y=52, c="#FFE66D")
             + '<circle cx="20" cy="52" r="1.5" fill="#fff"/><circle cx="52" cy="28" r="1.5" fill="#fff"/>'),
    gobo_svg("url(#gold)", "#A87400",
             defs='<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF3A0"/>'
                  '<stop offset="1" stop-color="#FFB800"/></linearGradient>',
             extra_front='<path d="M24 12 L28 2 L32 10 L35 0 L38 10 L42 2 L46 12 Z" fill="#FFD700" '
                         'stroke="#A87400" stroke-width="1.5"/>' + SPARK.format(x=8, y=30, c="#fff")),
    gobo_svg("url(#rainbow)", "#7a3cc8",
             defs='<linearGradient id="rainbow" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF5E5E"/>'
                  '<stop offset="0.25" stop-color="#FFD23F"/><stop offset="0.5" stop-color="#6BE06B"/>'
                  '<stop offset="0.75" stop-color="#5EC8FF"/><stop offset="1" stop-color="#B36BFF"/></linearGradient>',
             extra_back='<circle cx="35" cy="38" r="34" fill="#FFF7B0" opacity="0.6"/>',
             extra_front=SPARK.format(x=8, y=14, c="#fff") + SPARK.format(x=60, y=30, c="#fff")),
]


def person_svg(shirt, stripe, hat, mask):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="52" height="66" viewBox="0 0 52 66">
<rect x="14" y="36" width="24" height="22" rx="6" fill="{shirt}"/>
<rect x="14" y="41" width="24" height="4" fill="{stripe}"/>
<rect x="14" y="49" width="24" height="4" fill="{stripe}"/>
<rect x="15" y="57" width="8" height="8" rx="3" fill="#333"/>
<rect x="29" y="57" width="8" height="8" rx="3" fill="#333"/>
<circle cx="26" cy="24" r="14" fill="#F2C29B" stroke="#b88a66" stroke-width="1.5"/>
<path d="M11 18 Q26 2 41 18 Z" fill="{hat}"/>
<rect x="9" y="16" width="34" height="4" rx="2" fill="{hat}"/>
<rect x="12" y="20" width="28" height="8" rx="4" fill="{mask}"/>
<circle cx="21" cy="24" r="2.6" fill="#fff"/>
<circle cx="31" cy="24" r="2.6" fill="#fff"/>
<circle cx="22" cy="24" r="1.3" fill="#000"/>
<circle cx="32" cy="24" r="1.3" fill="#000"/>
<path d="M21 32 Q26 35 31 32" fill="none" stroke="#7a4a2a" stroke-width="1.6" stroke-linecap="round"/>
</svg>'''


PLAYER = person_svg("#2f6fd6", "#ffffff", "#1d3f8a", "#111")
RIVAL = person_svg("#c82a2a", "#222222", "#7a1010", "#3a0000")

LASER = '''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="12" viewBox="0 0 480 12">
<rect x="0" y="2" width="480" height="8" fill="#ff3030" opacity="0.35"/>
<rect x="0" y="5" width="480" height="2" fill="#ff2020"/>
<rect x="0" y="0" width="480" height="1.5" fill="#ff6060"/>
<rect x="0" y="10.5" width="480" height="1.5" fill="#ff6060"/>
</svg>'''


def lock_svg(fill, edge, closed):
    shackle = "M11 15 V10 Q11 4 17 4 Q23 4 23 10 V15" if closed else "M11 15 V10 Q11 4 17 4 Q23 4 23 10 V8"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 34 34">
<circle cx="17" cy="17" r="16" fill="{fill}" stroke="{edge}" stroke-width="2"/>
<path d="{shackle}" fill="none" stroke="#fff" stroke-width="3"/>
<rect x="8" y="15" width="18" height="13" rx="3" fill="#fff"/>
<circle cx="17" cy="21" r="2" fill="{edge}"/>
</svg>'''


LOCK_OPEN = lock_svg("#2fb84a", "#1a7a2e", closed=False)
LOCK_CLOSED = lock_svg("#e03a3a", "#8a1a1a", closed=True)


def slot_x(i):
    """Stage x of base slot i (1..8)."""
    return -230 + i * 55


MY_Y, RIVAL_Y = -118, 108


def backdrop():
    pads = []
    for i in range(1, 9):
        cx = 240 + slot_x(i)
        pads.append(f'<ellipse cx="{cx}" cy="{180 - MY_Y + 22}" rx="24" ry="7" fill="#8fb6e8" stroke="#2f7fd6" stroke-width="2"/>')
        pads.append(f'<ellipse cx="{cx}" cy="{180 - RIVAL_Y + 22}" rx="24" ry="7" fill="#e8a0a0" stroke="#d63a3a" stroke-width="2"/>')
    studs = "".join(f'<circle cx="{x}" cy="{y}" r="2.2" fill="#ffd23f"/>'
                    for x in range(20, 480, 30) for y in (144, 196))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect width="480" height="360" fill="#7ccf5a"/>
<rect x="0" y="0" width="480" height="30" fill="#2d3748" opacity="0.35"/>
<rect x="3" y="32" width="474" height="94" rx="10" fill="#ffd6d6" stroke="#d63a3a" stroke-width="4"/>
<text x="470" y="48" font-family="Sans Serif" font-size="12" font-weight="bold" fill="#b02a2a" text-anchor="end">RIVAL BASE</text>
<rect x="0" y="140" width="480" height="60" fill="#c8202a"/>
<rect x="0" y="140" width="480" height="4" fill="#ffd23f"/>
<rect x="0" y="196" width="480" height="4" fill="#ffd23f"/>
{studs}
<path d="M0 132 Q30 120 48 150 L48 200 L0 200 Z" fill="#5a4a3a"/>
<path d="M4 150 Q22 138 36 158 L36 200 L4 200 Z" fill="#1a1410"/>
<text x="240" y="176" font-family="Sans Serif" font-size="13" font-weight="bold" fill="#ffd23f" text-anchor="middle" opacity="0.8">GOBO CARPET</text>
<rect x="3" y="258" width="474" height="99" rx="10" fill="#d6ecff" stroke="#2f7fd6" stroke-width="4"/>
<text x="470" y="352" font-family="Sans Serif" font-size="12" font-weight="bold" fill="#1f5fae" text-anchor="end">YOUR BASE</text>
{"".join(pads)}
</svg>'''


def card(title, title_color, lines):
    rows, y = [], 128
    for text, size, color in lines:
        rows.append(f'<text x="240" y="{y}" font-family="Sans Serif" font-size="{size}" '
                    f'font-weight="bold" fill="{color}" text-anchor="middle">{text}</text>')
        y += size + 8
    left = GOBO_ART[0].split(">", 1)[1].rsplit("</svg>", 1)[0]
    right = GOBO_ART[6].split(">", 1)[1].rsplit("</svg>", 1)[0].replace('id="rainbow"', 'id="rb2"').replace("#rainbow", "#rb2")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect x="16" y="12" width="448" height="336" rx="24" fill="#fffaf0" stroke="#e08a00" stroke-width="6" opacity="0.97"/>
<g transform="translate(30 16)">{left}</g>
<g transform="translate(380 16)">{right}</g>
<text x="240" y="72" font-family="Marker" font-size="38" fill="{title_color}" text-anchor="middle">{title}</text>
<text x="240" y="98" font-family="Sans Serif" font-size="13" fill="#888" text-anchor="middle">Gobo, Leaf, Ice, Fire, Galaxy, Golden and the SECRET Rainbow Gobo!</text>
{"".join(rows)}
</svg>'''


TITLE_CARD = card("STEAL A GOBO!", "#e0600a", [
    ("Walk: Arrow keys or W A S D", 15, "#333"),
    ("Buy a Gobo on the red carpet: touch it + press E", 15, "#333"),
    ("Gobos in YOUR BASE make money every second", 15, "#333"),
    ("Steal from the RIVAL BASE: press E, then run home!", 15, "#b02a2a"),
    ("The Rival steals too! Touch him to get it back", 15, "#b02a2a"),
    ("Step on the LOCK button to lock your base", 15, "#1f5fae"),
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
ALARM = tone_wav([(700, 500, 0.18, "square"), (700, 500, 0.18, "square")])
OUCH = tone_wav([(500, 150, 0.45, "square")])
LOCK = tone_wav([(300, 300, 0.08, "square"), (600, 600, 0.15, "square")])

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
               "Carrying", "Rival Carry", "Rival Result", "Rival New Slot", "My Lock", "Rival Lock",
               "Steal Timer", "Rival Lock Timer", "Tip"]
LISTS = {"My Slots": [0] * 8, "Rival Slots": [0] * 8,
         "Names": [g[0] for g in GOBOS], "Tiers": [g[1] for g in GOBOS],
         "Prices": [g[2] for g in GOBOS], "Rates": [g[3] for g in GOBOS], "Chances": CUMULATIVE}
BROADCASTS = ["title", "start", "caught", "tip"]


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
def change_x(d):            return B("motion_changexby", DX=d)
def change_y(d):            return B("motion_changeyby", DY=d)
def x_pos():                return B("motion_xposition")
def y_pos():                return B("motion_yposition")
def point_dir(d):           return B("motion_pointindirection", DIRECTION=d)
def rot_style(s):           return B("motion_setrotationstyle", fields={"STYLE": s})
def say(m):                 return B("looks_say", MESSAGE=m)
def say_for(m, s):          return B("looks_sayforsecs", MESSAGE=m, SECS=s)
def costume(c):             return B("looks_switchcostumeto", COSTUME=c)
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
RIVAL_HOME = (0, 146)

# ---------------------------------------------------------------- Stage

stage = Compiler("stage")
init = [set_var("Money", 50), set_var("Income", 0), set_var("Rebirths", 0), set_var("Multiplier", 1),
        set_var("Rebirth Cost", 20000), set_var("Speed", 4), set_var("Upgrade Cost", 200),
        set_var("Carrying", 0), set_var("Rival Carry", 0), set_var("Rival Result", 0),
        set_var("Rival New Slot", 0), set_var("My Lock", 0), set_var("Rival Lock", 0),
        set_var("Steal Timer", 40), set_var("Rival Lock Timer", 45), set_var("Tip", ""),
        clear_list("My Slots"), clear_list("Rival Slots")]
init += [add_to("My Slots", 0) for _ in range(8)] + [add_to("Rival Slots", 0) for _ in range(8)]
income = [set_var("Income", 0)] + [
    if_(gt(item("My Slots", i), 0), [change_var("Income", item("Rates", item("My Slots", i)))])
    for i in range(1, 9)] + [set_var("Income", mul(V("Income"), V("Multiplier")))]
stage.script([
    flag(), *init,
    broadcast_wait("title"),
    broadcast("start"),
    forever([
        wait(1),
        *income,
        change_var("Money", V("Income")),
        if_(gt(V("My Lock"), 0), [change_var("My Lock", -1)]),
        if_(gt(V("Rival Lock"), 0), [change_var("Rival Lock", -1)]),
        if_(gt(V("Steal Timer"), 0), [change_var("Steal Timer", -1)]),
        change_var("Rival Lock Timer", -1),
        if_(lt(V("Rival Lock Timer"), 1), [set_var("Rival Lock", 12), set_var("Rival Lock Timer", rand(40, 70))]),
    ]),
], 20, 20)

# ---------------------------------------------------------------- Player

player = Compiler("player", local_vars=["step"])
player.script([
    flag(), rot_style("left-right"), point_dir(90), goto_xy(HOME_X, HOME_Y), size(100), show(), front(), say(""),
], 20, 20)
player.script([
    when_msg("start"),
    forever([
        if_else(gt(V("Carrying"), 0), [set_var("step", mul(V("Speed"), 0.75))], [set_var("step", V("Speed"))]),
        if_(any_key("right arrow", "d"), [point_dir(90), change_x(V("step"))]),
        if_(any_key("left arrow", "a"), [point_dir(-90), change_x(sub(0, V("step")))]),
        if_(any_key("up arrow", "w"), [change_y(V("step"))]),
        if_(any_key("down arrow", "s"), [change_y(sub(0, V("step")))]),
        # The Rival's lasers push you out while his base is locked.
        if_else(gt(V("Rival Lock"), 0),
                [if_(gt(y_pos(), 50), [set_y(50)])],
                [if_(gt(y_pos(), 148), [set_y(148)])]),
        if_(lt(y_pos(), -160), [set_y(-160)]),
    ]),
], 20, 200)
player.script([when_msg("tip"), say_for(V("Tip"), 2)], 480, 20)
player.script([
    when_msg("caught"),
    play("ouch"),
    goto_xy(HOME_X, HOME_Y),
    say_for("Caught! The Rival took his Gobo back.", 2),
], 480, 120)
player.script([
    when_key("u"),
    if_else(lt(V("Money"), V("Upgrade Cost")),
            tip("Faster shoes cost $", V("Upgrade Cost")),
            [change_var("Money", sub(0, V("Upgrade Cost"))),
             change_var("Speed", 0.5),
             set_var("Upgrade Cost", mul(V("Upgrade Cost"), 3)),
             *tip("Zoom! Your speed is now ", V("Speed"))]),
], 480, 260)
player.script([
    when_key("r"),
    if_else(or_(lt(V("Money"), V("Rebirth Cost")), gt(V("Carrying"), 0)),
            tip("Rebirth costs $", V("Rebirth Cost"), ". It resets your Gobos but you earn more!"),
            [set_var("Money", 0),
             *[replace("My Slots", i, 0) for i in range(1, 9)],
             change_var("Rebirths", 1),
             set_var("Multiplier", add(1, mul(V("Rebirths"), 0.5))),
             set_var("Rebirth Cost", mul(20000, mul(add(V("Rebirths"), 1), add(V("Rebirths"), 1)))),
             *tip("REBIRTH! Now your Gobos make x", V("Multiplier"), " money!")]),
], 480, 480)

# ---------------------------------------------------------------- Gobo (all Gobos are clones)
# kind: 1 = on the carpet, 2 = in my base, 3 = in the Rival's base,
#       4 = carried by me, 5 = carried by the Rival

pick_rarity = [set_var("r", rand(1, 1000)), set_var("rarity", 1)] + [
    if_(gt(V("r"), item("Chances", k)), [set_var("rarity", k + 1)]) for k in range(1, 7)]
E = any_key("e", "space")

gobo = Compiler("gobo", local_vars=["kind", "rarity", "slot", "found", "r", "rolled"])
gobo.script([flag(), hide(), set_var("kind", 0)], 20, 20)
gobo.script([
    when_msg("start"),
    # The Rival starts with a few Gobos.
    set_var("kind", 3),
    *[[set_var("slot", i), set_var("rarity", r), replace("Rival Slots", i, r), clone_me()]
      for i, r in ((2, 1), (4, 2), (6, 1), (7, 3))],
    forever([set_var("kind", 1), clone_me(), wait(rand(1.5, 3))]),
], 20, 140)

carpet = [
    *pick_rarity,
    costume(V("rarity")), size(60), goto_xy(-225, 12), back(), show(),
    if_(gt(V("rarity"), 4), [*tip("WOW! A ", TIER, " ", NAME, " is on the carpet!"), play("alarm")]),
    set_var("rolled", 0),
    repeat_until(or_(gt(x_pos(), 232), not_(eq(V("kind"), 1))), [
        change_x(1.2),
        set_y(add(12, BOB)),
        if_else(lt(distance_to("Player"), 45),
                [say(join(NAME, " (", TIER, ") $", PRICE, " = $", RATE, "/s"))],
                [say(join("$", PRICE))]),
        if_(and_(touching("Player"), E, eq(V("Carrying"), 0)), [
            if_else(lt(V("Money"), PRICE),
                    tip("You need $", PRICE, " to buy this ", NAME),
                    [*find_free("My Slots"),
                     if_else(eq(V("found"), 0),
                             tip("Your base is full! Stand on a Gobo and press X to sell it."),
                             [change_var("Money", sub(0, PRICE)),
                              replace("My Slots", V("found"), V("rarity")),
                              set_var("slot", V("found")), set_var("kind", 2),
                              play("cash"), *tip("You bought a ", NAME, "!")])]),
        ]),
        # Near the end of the carpet the Rival may buy it.
        if_(and_(eq(V("rolled"), 0), gt(x_pos(), 150), eq(V("kind"), 1)), [
            set_var("rolled", 1),
            # He keeps one slot free so he can still steal from you.
            set_var("r", 0),
            *[if_(eq(item("Rival Slots", i), 0), [change_var("r", 1)]) for i in range(1, 9)],
            if_(and_(gt(V("r"), 1), or_(gt(V("rarity"), 2), lt(rand(1, 10), 3))), [
                *find_free("Rival Slots"),
                if_(gt(V("found"), 0), [
                    replace("Rival Slots", V("found"), V("rarity")),
                    set_var("slot", V("found")), set_var("kind", 3),
                ]),
            ]),
        ]),
    ]),
    if_(eq(V("kind"), 1), [delete_clone()]),
]

mine = [  # kind 2: sitting in my base, making money
    goto_xy(SLOT_X, add(MY_Y, BOB)),
    if_(not_(eq(item("My Slots", V("slot")), V("rarity"))), [delete_clone()]),
    if_else(lt(distance_to("Player"), 40),
            [say(join(NAME, " $", RATE, "/s  (X = sell)"))], [say("")]),
    if_(and_(touching("Player"), key("x"), eq(V("Carrying"), 0)), [
        change_var("Money", round_(div(PRICE, 2))),
        replace("My Slots", V("slot"), 0),
        *tip("Sold ", NAME, " for $", round_(div(PRICE, 2))),
        delete_clone(),
    ]),
    if_(eq(V("Rival Carry"), V("slot")), [set_var("kind", 5), say(""), front()]),
]

rivals = [  # kind 3: sitting in the Rival's base
    goto_xy(SLOT_X, add(RIVAL_Y, BOB)),
    if_(not_(eq(item("Rival Slots", V("slot")), V("rarity"))), [delete_clone()]),
    if_else(lt(distance_to("Player"), 40),
            [say(join(NAME, " $", RATE, "/s  (E = steal)"))], [say("")]),
    if_(and_(touching("Player"), E, eq(V("Carrying"), 0)), [
        if_else(gt(V("Rival Lock"), 0),
                tip("The Rival Base is locked! Wait for the lasers to go away."),
                [*find_free("My Slots"),
                 if_else(eq(V("found"), 0),
                         tip("Your base is full! Sell a Gobo first (X)."),
                         [set_var("Carrying", V("rarity")), set_var("kind", 4),
                          say(""), play("pop"), front()])]),
    ]),
]

carried = [  # kind 4: I am running home with it
    goto_xy(prop_of("x position", "Player"), add(prop_of("y position", "Player"), 34)),
    if_else(eq(V("Carrying"), 0),
            [set_var("kind", 3), back()],  # caught: it goes back
            [if_(lt(prop_of("y position", "Player"), SAFE_Y), [
                *find_free("My Slots"),
                if_(gt(V("found"), 0), [
                    replace("My Slots", V("found"), V("rarity")),
                    replace("Rival Slots", V("slot"), 0),
                    set_var("slot", V("found")), set_var("kind", 2), set_var("Carrying", 0),
                    back(), play("cash"), *tip("You stole a ", NAME, "!"),
                ]),
            ])]),
]

rival_carried = [  # kind 5: the Rival is running away with it
    if_else(eq(V("Rival Carry"), V("slot")),
            [goto_xy(prop_of("x position", "Rival"), add(prop_of("y position", "Rival"), 34))],
            [back(),
             if_else(eq(V("Rival Result"), 1),
                     [set_var("slot", V("Rival New Slot")), set_var("kind", 3)],
                     [set_var("kind", 2)])]),
]

gobo.script([
    when_cloned(),
    if_(eq(V("kind"), 1), carpet),
    say(""), costume(V("rarity")), size(60), show(),
    if_else(eq(V("kind"), 2), [glide(0.5, SLOT_X, MY_Y)], [glide(0.5, SLOT_X, RIVAL_Y)]),
    forever([
        if_(eq(V("kind"), 2), mine),
        if_(eq(V("kind"), 3), rivals),
        if_(eq(V("kind"), 4), carried),
        if_(eq(V("kind"), 5), rival_carried),
    ]),
], 380, 20)

# ---------------------------------------------------------------- Rival
# mode: 0 = at home (guards, chases thieves), 1 = walking to steal, 2 = running away with
#       my Gobo, 3 = walking home

rival = Compiler("rival", local_vars=["mode", "tx", "ty", "dx", "dy", "dist", "spd", "patrol", "target",
                                      "best", "found", "alerted"])
walk = [  # walk toward (tx, ty) at speed spd
    set_var("dx", sub(V("tx"), x_pos())),
    set_var("dy", sub(V("ty"), y_pos())),
    set_var("dist", mathop("sqrt", add(mul(V("dx"), V("dx")), mul(V("dy"), V("dy"))))),
    if_else(gt(V("dist"), V("spd")),
            [change_x(div(mul(V("dx"), V("spd")), V("dist"))),
             change_y(div(mul(V("dy"), V("spd")), V("dist")))],
            [goto_xy(V("tx"), V("ty"))]),
    if_(gt(V("dx"), 0.5), [point_dir(90)]),
    if_(lt(V("dx"), -0.5), [point_dir(-90)]),
]
pick_target = [set_var("best", 0), set_var("target", 0)] + [
    if_(gt(item("My Slots", i), V("best")), [set_var("best", item("My Slots", i)), set_var("target", i)])
    for i in range(1, 9)]
go_home = lambda *extra: [set_var("mode", 3), set_var("alerted", 0), *extra]

rival.script([
    flag(), rot_style("left-right"), point_dir(-90), goto_xy(*RIVAL_HOME), show(), say(""),
    set_var("mode", 0), set_var("patrol", 0), set_var("alerted", 0),
], 20, 20)
rival.script([
    when_msg("start"),
    forever([
        if_(eq(V("mode"), 0), [
            if_else(and_(gt(V("Carrying"), 0), gt(prop_of("y position", "Player"), SAFE_Y)),
                    [if_(eq(V("alerted"), 0), [
                        say("HEY! That's MY Gobo!"), play("alarm"), set_var("alerted", 1), wait(0.5)]),
                     set_var("tx", prop_of("x position", "Player")),
                     set_var("ty", prop_of("y position", "Player")),
                     set_var("spd", 3.6)],
                    [if_(eq(V("alerted"), 1), [set_var("alerted", 0), say("")]),
                     set_var("tx", V("patrol")), set_var("ty", RIVAL_HOME[1]), set_var("spd", 1.3),
                     if_(lt(mathop("abs", sub(x_pos(), V("patrol"))), 4), [set_var("patrol", rand(-200, 200))]),
                     if_(and_(lt(V("Steal Timer"), 1), eq(V("Carrying"), 0), eq(V("My Lock"), 0)), [
                         *pick_target, *find_free("Rival Slots"),
                         if_else(and_(gt(V("target"), 0), gt(V("found"), 0)),
                                 [set_var("mode", 1), say("I'm going to steal your Gobo!")],
                                 [set_var("Steal Timer", 10)]),
                     ])]),
            *walk,
            if_(and_(gt(V("Carrying"), 0), touching("Player")), [
                set_var("Carrying", 0), say("Got you!"), broadcast("caught"), *go_home(),
            ]),
        ]),
        if_(eq(V("mode"), 1), [
            set_var("tx", add(-230, mul(V("target"), 55))), set_var("ty", -96), set_var("spd", 2.4),
            *walk,
            if_(and_(gt(V("My Lock"), 0), lt(y_pos(), -55)),
                go_home(say("Your base is locked! Grrr!"), set_var("Steal Timer", rand(20, 35)))),
            if_(eq(item("My Slots", V("target")), 0), go_home(say(""), set_var("Steal Timer", 15))),
            if_(touching("Player"),
                go_home(say("Eek! You caught me!"), set_var("Steal Timer", rand(25, 40)))),
            if_(and_(eq(V("mode"), 1), lt(V("dist"), 4)), [
                set_var("best", item("My Slots", V("target"))),
                set_var("Rival Result", 0), set_var("Rival Carry", V("target")),
                set_var("mode", 2), say("Hehe! Got one!"), play("alarm"),
                *tip("The Rival is stealing your ", item("Names", V("best")), "! Touch him!"),
            ]),
        ]),
        if_(eq(V("mode"), 2), [
            set_var("tx", RIVAL_HOME[0]), set_var("ty", RIVAL_HOME[1]), set_var("spd", 2),
            *walk,
            if_else(touching("Player"),
                    [set_var("Rival Result", 2), set_var("Rival Carry", 0), play("ouch"),
                     *go_home(say("Nooo!"), set_var("Steal Timer", rand(25, 45))),
                     *tip("You saved your Gobo!")],
                    [if_(lt(V("dist"), 4), [
                        *find_free("Rival Slots"),
                        if_else(and_(gt(V("found"), 0), eq(item("My Slots", V("target")), V("best"))),
                                [set_var("Rival New Slot", V("found")),
                                 replace("Rival Slots", V("found"), V("best")),
                                 replace("My Slots", V("target"), 0),
                                 set_var("Rival Result", 1),
                                 *tip("Oh no! The Rival stole your ", item("Names", V("best")), "!")],
                                [set_var("Rival Result", 2)]),
                        set_var("Rival Carry", 0),
                        set_var("mode", 0), say(""), set_var("Steal Timer", rand(30, 50)),
                    ])]),
        ]),
        if_(eq(V("mode"), 3), [
            set_var("tx", RIVAL_HOME[0]), set_var("ty", RIVAL_HOME[1]), set_var("spd", 3),
            *walk,
            if_(lt(V("dist"), 4), [set_var("mode", 0), say("")]),
        ]),
    ]),
], 20, 200)
rival.script([when_msg("caught"), wait(1.5), say("")], 700, 20)

# ---------------------------------------------------------------- Lock button and lasers

lock = Compiler("lock")
lock.script([flag(), goto_xy(-218, -100), costume("unlocked"), show(), say("")], 20, 20)
lock.script([
    when_msg("start"),
    forever([
        if_(and_(touching("Player"), eq(V("My Lock"), 0)), [
            set_var("My Lock", 25), play("lock"), *tip("Your base is locked for 25 seconds!"),
        ]),
        if_else(gt(V("My Lock"), 0),
                [costume("locked"), say(join(V("My Lock"), "s"))],
                [costume("unlocked"), say("LOCK")]),
    ]),
], 20, 160)

my_laser = Compiler("mylaser")
my_laser.script([flag(), goto_xy(0, -71), hide()], 20, 20)
my_laser.script([when_msg("start"), forever([
    if_else(gt(V("My Lock"), 0), [show(), front()], [hide()])])], 20, 140)

rival_laser = Compiler("rivallaser")
rival_laser.script([flag(), goto_xy(0, 56), hide()], 20, 20)
rival_laser.script([when_msg("start"), forever([
    if_else(gt(V("Rival Lock"), 0), [show(), front()], [hide()])])], 20, 140)

# ---------------------------------------------------------------- title card

message = Compiler("message")
message.script([
    when_msg("title"),
    goto_xy(0, 0), costume("title"), show(), front(),
    wait_until(key("space")),
    hide(),
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


def sprite(comp, name, costumes, sounds, layer, x=0, y=0, visible=True):
    return {"isStage": False, "name": name,
            "variables": {vid_: [v, 0] for v, vid_ in comp.local.items()},
            "lists": {}, "broadcasts": {}, "blocks": comp.blocks, "comments": {},
            "currentCostume": 0, "costumes": costumes, "sounds": sounds, "volume": 100,
            "layerOrder": layer, "visible": visible, "x": x, "y": y, "size": 100, "direction": 90,
            "draggable": False, "rotationStyle": "left-right"}


START_VALUES = {"Money": 50, "Multiplier": 1, "Rebirth Cost": 20000, "Speed": 4, "Upgrade Cost": 200,
                "Steal Timer": 40, "Rival Lock Timer": 45, "Tip": ""}
targets = [
    {"isStage": True, "name": "Stage",
     "variables": {vid(v): [v, START_VALUES.get(v, 0)] for v in GLOBAL_VARS},
     "lists": {lid(n): [n, vals] for n, vals in LISTS.items()},
     "broadcasts": {bid(b): b for b in BROADCASTS}, "blocks": stage.blocks,
     "comments": {}, "currentCostume": 0,
     "costumes": [svg_costume("Gobo Land", backdrop(), 240, 180)],
     "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60, "videoTransparency": 50,
     "videoState": "on", "textToSpeechLanguage": None},
    sprite(gobo, "Gobo", [svg_costume(g[0], art) for g, art in zip(GOBOS, GOBO_ART)],
           [wav_sound("pop", POP), wav_sound("cash", CASH), wav_sound("alarm", ALARM)], 1, visible=False),
    sprite(lock, "Lock Button", [svg_costume("unlocked", LOCK_OPEN), svg_costume("locked", LOCK_CLOSED)],
           [wav_sound("lock", LOCK)], 2, -218, -100),
    sprite(my_laser, "My Lasers", [svg_costume("laser", LASER)], [], 3, 0, -71, visible=False),
    sprite(rival_laser, "Rival Lasers", [svg_costume("laser", LASER)], [], 4, 0, 56, visible=False),
    sprite(rival, "Rival", [svg_costume("Rival", RIVAL)], [wav_sound("alarm", ALARM), wav_sound("ouch", OUCH)],
           5, *RIVAL_HOME),
    sprite(player, "Player", [svg_costume("Player", PLAYER)], [wav_sound("ouch", OUCH)], 6, HOME_X, HOME_Y),
    sprite(message, "Message", [svg_costume("title", TITLE_CARD, 240, 180)], [], 7, visible=False),
]


def monitor(name, x, y):
    return {"id": vid(name), "mode": "default", "opcode": "data_variable",
            "params": {"VARIABLE": name}, "spriteName": None, "value": 0, "width": 0, "height": 0,
            "x": x, "y": y, "visible": True, "sliderMin": 0, "sliderMax": 100, "isDiscrete": True}


project = {
    "targets": targets,
    "monitors": [monitor("Money", 5, 3), monitor("Income", 140, 3), monitor("Rebirths", 270, 3)],
    "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "build_sb3.py"},
}

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("project.json", json.dumps(project))
    for fname, data in assets.items():
        z.writestr(fname, data)

if __name__ == "__main__":
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {len(assets)} assets)")
