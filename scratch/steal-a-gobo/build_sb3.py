#!/usr/bin/env python3
"""Build "Steal a Gobo" as a Scratch 3 project file (Steal_a_Gobo.sb3).

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

# ---------------------------------------------------------------- art (SVG)

def gobo_svg(body, edge, sparkle=None):
    """Gobo: a round little creature with a spiky flame-like top and big eyes."""
    extra = ""
    if sparkle:
        extra = (f'<path d="M12 14 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2 z" fill="{sparkle}"/>'
                 f'<path d="M58 40 l1.5 4 l4 1.5 l-4 1.5 l-1.5 4 l-1.5 -4 l-4 -1.5 l4 -1.5 z" fill="{sparkle}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="70" height="72" viewBox="0 0 70 72">
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
{extra}
</svg>'''


GOBO = gobo_svg("#FFBF1F", "#E08A00")
GOLD_GOBO = gobo_svg("#FFE14D", "#C79100", sparkle="#FFFFFF")
DIAMOND_GOBO = gobo_svg("#7FE7FF", "#1E88C8", sparkle="#FFFFFF")

THIEF = '''<svg xmlns="http://www.w3.org/2000/svg" width="52" height="66" viewBox="0 0 52 66">
<rect x="14" y="36" width="24" height="22" rx="6" fill="#222"/>
<rect x="14" y="41" width="24" height="4" fill="#eee"/>
<rect x="14" y="49" width="24" height="4" fill="#eee"/>
<rect x="15" y="57" width="8" height="8" rx="3" fill="#333"/>
<rect x="29" y="57" width="8" height="8" rx="3" fill="#333"/>
<path d="M40 38 Q50 42 48 54 L42 56 Q40 46 36 44 Z" fill="#8a5a2b" stroke="#5a3a1b" stroke-width="1.5"/>
<circle cx="26" cy="24" r="14" fill="#F2C29B" stroke="#b88a66" stroke-width="1.5"/>
<path d="M11 18 Q26 2 41 18 Z" fill="#222"/>
<rect x="9" y="16" width="34" height="4" rx="2" fill="#222"/>
<rect x="12" y="20" width="28" height="8" rx="4" fill="#111"/>
<circle cx="21" cy="24" r="2.6" fill="#fff"/>
<circle cx="31" cy="24" r="2.6" fill="#fff"/>
<circle cx="22" cy="24" r="1.3" fill="#000"/>
<circle cx="32" cy="24" r="1.3" fill="#000"/>
<path d="M21 32 Q26 35 31 32" fill="none" stroke="#7a4a2a" stroke-width="1.6" stroke-linecap="round"/>
</svg>'''

GUARD = '''<svg xmlns="http://www.w3.org/2000/svg" width="60" height="74" viewBox="0 0 60 74">
<rect x="14" y="40" width="32" height="26" rx="8" fill="#2855c8" stroke="#16307a" stroke-width="2"/>
<circle cx="30" cy="48" r="4" fill="#ffd23f" stroke="#b08a00" stroke-width="1"/>
<rect x="16" y="64" width="10" height="9" rx="3" fill="#16307a"/>
<rect x="34" y="64" width="10" height="9" rx="3" fill="#16307a"/>
<circle cx="30" cy="27" r="15" fill="#F2C29B" stroke="#b88a66" stroke-width="1.5"/>
<path d="M12 18 Q30 0 48 18 Z" fill="#1c3f99"/>
<rect x="10" y="16" width="40" height="5" rx="2" fill="#111"/>
<circle cx="30" cy="11" r="3" fill="#ffd23f"/>
<path d="M19 24 L27 27" stroke="#222" stroke-width="2.4" stroke-linecap="round"/>
<path d="M41 24 L33 27" stroke="#222" stroke-width="2.4" stroke-linecap="round"/>
<circle cx="24" cy="30" r="2.4" fill="#222"/>
<circle cx="36" cy="30" r="2.4" fill="#222"/>
<path d="M24 37 Q30 34 36 37" fill="none" stroke="#7a4a2a" stroke-width="2" stroke-linecap="round"/>
</svg>'''

BACKDROP = '''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect width="480" height="360" fill="#7ccf5a"/>
<g fill="#6cbf4a">
<circle cx="190" cy="80" r="5"/><circle cx="260" cy="140" r="4"/><circle cx="220" cy="260" r="5"/>
<circle cx="300" cy="300" r="4"/><circle cx="170" cy="190" r="4"/><circle cx="310" cy="70" r="5"/>
</g>
<rect x="100" y="165" width="250" height="36" fill="#d9b77a"/>
<rect x="0" y="0" width="480" height="40" fill="#2d3748" opacity="0.35"/>
<rect x="4" y="44" width="92" height="312" rx="12" fill="#bfe3ff" stroke="#2f7fd6" stroke-width="5"/>
<text x="50" y="340" font-family="Sans Serif" font-size="14" font-weight="bold" fill="#1f5fae" text-anchor="middle">YOUR BASE</text>
<rect x="346" y="44" width="130" height="312" rx="12" fill="#ffd0d0" stroke="#d63a3a" stroke-width="5" stroke-dasharray="14 8"/>
<text x="411" y="340" font-family="Sans Serif" font-size="14" font-weight="bold" fill="#b02a2a" text-anchor="middle">GOBO VAULT</text>
</svg>'''


def card(title, title_color, lines, show_gobo=True):
    rows = []
    y = 150 if show_gobo else 150
    for i, (text, size, color) in enumerate(lines):
        rows.append(f'<text x="240" y="{y}" font-family="Sans Serif" font-size="{size}" '
                    f'font-weight="bold" fill="{color}" text-anchor="middle">{text}</text>')
        y += size + 9
    gobo = ""
    if show_gobo:
        inner = GOBO.split(">", 1)[1].rsplit("</svg>", 1)[0]
        gobo = (f'<g transform="translate(40 18) scale(1.1)">{inner}</g>'
                f'<g transform="translate(362 18) scale(1.1)">{inner}</g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<rect x="20" y="16" width="440" height="328" rx="24" fill="#fffaf0" stroke="#e08a00" stroke-width="6" opacity="0.97"/>
{gobo}
<text x="240" y="90" font-family="Marker" font-size="38" fill="{title_color}" text-anchor="middle">{title}</text>
{"".join(rows)}
</svg>'''


TITLE_CARD = card("STEAL A GOBO!", "#e0600a", [
    ("Arrow keys or W A S D = move", 16, "#333"),
    ("Touch a Gobo in the red VAULT to grab it", 16, "#333"),
    ("Carry it back to YOUR BASE (blue)", 16, "#333"),
    ("Your Gobos make money every second!", 16, "#333"),
    ("Do not let the Guard catch you (3 lives)", 16, "#b02a2a"),
    ("Press U to buy more speed. Get $1000 to WIN!", 16, "#1f5fae"),
    ("Press SPACE to start", 22, "#e0600a"),
])
WIN_CARD = card("YOU WIN!", "#1f9e3a", [
    ("You have $1000!", 22, "#333"),
    ("You are the best Gobo thief ever!", 18, "#333"),
    ("", 18, "#333"),
    ("Click the green flag to play again", 18, "#1f5fae"),
])
LOSE_CARD = card("GAME OVER", "#b02a2a", [
    ("The Guard caught you 3 times.", 20, "#333"),
    ("Your Gobos went back to the Vault...", 18, "#333"),
    ("", 18, "#333"),
    ("Click the green flag to try again", 18, "#1f5fae"),
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
    ("motion_pointtowards", "TOWARDS"): ("motion_pointtowards_menu", "TOWARDS"),
    ("sensing_of", "OBJECT"): ("sensing_of_object_menu", "OBJECT"),
    ("looks_switchcostumeto", "COSTUME"): ("looks_costume", "COSTUME"),
    ("control_create_clone_of", "CLONE_OPTION"): ("control_create_clone_of_menu", "CLONE_OPTION"),
    ("sound_play", "SOUND_MENU"): ("sound_sounds_menu", "SOUND_MENU"),
}
TEXT_INPUTS = {"OPERAND1", "OPERAND2", "STRING1", "STRING2", "MESSAGE"}
STOP_MUTATION = {"tagName": "mutation", "children": [], "hasnext": "false"}

GLOBAL_VARS = ["Money", "Income", "Lives", "Gobos Stolen", "Carrying", "Speed", "Waiting",
               "Upgrade Cost", "Guard Speed"]
BROADCASTS = ["title", "start", "caught", "you win", "game over"]


def vid(name):
    return "var-" + name.lower().replace(" ", "-")


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
            elif name == "BROADCAST_OPTION":
                blk["fields"][name] = [val, bid(val)]
            else:
                blk["fields"][name] = [val, None]
        if node.mutation:
            blk["mutation"] = node.mutation
        return i

    def input(self, op, name, val, pid):
        shadow_type = 10 if name in TEXT_INPUTS else 4
        if (op, name) in MENUS:
            sop, field = MENUS[(op, name)]
            sid = self.new_id()
            self.blocks[sid] = {"opcode": sop, "next": None, "parent": pid, "inputs": {},
                                "fields": {field: [val, None]}, "shadow": True, "topLevel": False}
            return [1, sid]
        if isinstance(val, list):
            return [2, self.stack(val, pid)]
        if isinstance(val, V):
            return [3, [12, val.name, self.var_id(val.name)], [shadow_type, ""]]
        if isinstance(val, BC):
            return [1, [11, val.name, bid(val.name)]]
        if isinstance(val, B):
            cid = self.emit(val, pid)
            if name == "CONDITION" or op in ("operator_and", "operator_or", "operator_not"):
                return [2, cid]
            return [3, cid, [shadow_type, ""]]
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return [1, [shadow_type, str(val)]]

    def stack(self, nodes, parent):
        first = prev = None
        for node in nodes:
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


# Handy shortcuts ---------------------------------------------------------------
def flag():                 return B("event_whenflagclicked")
def when_msg(m):            return B("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": m})
def when_key(k):            return B("event_whenkeypressed", fields={"KEY_OPTION": k})
def broadcast(m):           return B("event_broadcast", BROADCAST_INPUT=BC(m))
def broadcast_wait(m):      return B("event_broadcastandwait", BROADCAST_INPUT=BC(m))
def set_var(n, v):          return B("data_setvariableto", fields={"VARIABLE": n}, VALUE=v)
def change_var(n, v):       return B("data_changevariableby", fields={"VARIABLE": n}, VALUE=v)
def forever(body):          return B("control_forever", SUBSTACK=body)
def repeat_until(c, body):  return B("control_repeat_until", CONDITION=c, SUBSTACK=body)
def wait_until(c):          return B("control_wait_until", CONDITION=c)
def wait(s):                return B("control_wait", DURATION=s)
def if_(c, body):           return B("control_if", CONDITION=c, SUBSTACK=body)
def if_else(c, a, b):       return B("control_if_else", CONDITION=c, SUBSTACK=a, SUBSTACK2=b)
def eq(a, b):               return B("operator_equals", OPERAND1=a, OPERAND2=b)
def lt(a, b):               return B("operator_lt", OPERAND1=a, OPERAND2=b)
def gt(a, b):               return B("operator_gt", OPERAND1=a, OPERAND2=b)
def and_(a, b):             return B("operator_and", OPERAND1=a, OPERAND2=b)
def or_(a, b):              return B("operator_or", OPERAND1=a, OPERAND2=b)
def not_(a):                return B("operator_not", OPERAND=a)
def add(a, b):              return B("operator_add", NUM1=a, NUM2=b)
def sub(a, b):              return B("operator_subtract", NUM1=a, NUM2=b)
def mul(a, b):              return B("operator_multiply", NUM1=a, NUM2=b)
def div(a, b):              return B("operator_divide", NUM1=a, NUM2=b)
def mod(a, b):              return B("operator_mod", NUM1=a, NUM2=b)
def floor(a):               return B("operator_mathop", fields={"OPERATOR": "floor"}, NUM=a)
def rand(a, b):             return B("operator_random", FROM=a, TO=b)
def join(a, b):             return B("operator_join", STRING1=a, STRING2=b)
def key(k):                 return B("sensing_keypressed", KEY_OPTION=k)
def touching(s):            return B("sensing_touchingobject", TOUCHINGOBJECTMENU=s)
def prop_of(p, s):          return B("sensing_of", fields={"PROPERTY": p}, OBJECT=s)
def goto_xy(x, y):          return B("motion_gotoxy", X=x, Y=y)
def set_x(x):               return B("motion_setx", X=x)
def set_y(y):               return B("motion_sety", Y=y)
def change_x(d):            return B("motion_changexby", DX=d)
def change_y(d):            return B("motion_changeyby", DY=d)
def x_pos():                return B("motion_xposition")
def y_pos():                return B("motion_yposition")
def point_dir(d):           return B("motion_pointindirection", DIRECTION=d)
def point_towards(s):       return B("motion_pointtowards", TOWARDS=s)
def move(n):                return B("motion_movesteps", STEPS=n)
def bounce():               return B("motion_ifonedgebounce")
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
def stop_all():             return B("control_stop", fields={"STOP_OPTION": "all"}, mutation=STOP_MUTATION)

HOME_X = -190          # where the thief starts (inside YOUR BASE)
BASE_EDGE = -150       # a carried Gobo counts as stolen once the thief is left of this
GUARD_WALL = -125      # the guard never walks further left than this
GOAL = 1000

# ---------------------------------------------------------------- scripts

stage = Compiler("stage")
stage.script([
    flag(),
    set_var("Money", 0), set_var("Income", 0), set_var("Lives", 3), set_var("Gobos Stolen", 0),
    set_var("Carrying", 0), set_var("Speed", 4), set_var("Waiting", 0), set_var("Upgrade Cost", 50),
    set_var("Guard Speed", 2.6),
    broadcast_wait("title"),
    broadcast("start"),
    forever([
        wait(1),
        change_var("Money", V("Income")),
        if_(not_(lt(V("Money"), GOAL)), [broadcast("you win")]),
    ]),
], 20, 20)

thief = Compiler("thief")
thief.script([
    flag(), rot_style("left-right"), point_dir(90), goto_xy(HOME_X, 0), size(100), show(), front(),
], 20, 20)
thief.script([
    when_msg("start"),
    forever([
        if_(or_(key("right arrow"), key("d")), [point_dir(90), change_x(V("Speed"))]),
        if_(or_(key("left arrow"), key("a")), [point_dir(-90), change_x(sub(0, V("Speed")))]),
        if_(or_(key("up arrow"), key("w")), [change_y(V("Speed"))]),
        if_(or_(key("down arrow"), key("s")), [change_y(sub(0, V("Speed")))]),
        if_(gt(y_pos(), 130), [set_y(130)]),
        if_(lt(y_pos(), -150), [set_y(-150)]),
    ]),
], 20, 220)
thief.script([
    when_msg("caught"),
    play("ouch"),
    goto_xy(HOME_X, 0),
    say_for("Oh no! The Guard got me!", 1.5),
], 450, 20)
thief.script([
    when_key("u"),
    if_else(lt(V("Money"), V("Upgrade Cost")),
            [say_for(join("You need $", V("Upgrade Cost")), 1)],
            [change_var("Money", sub(0, V("Upgrade Cost"))),
             change_var("Speed", 1),
             set_var("Upgrade Cost", mul(V("Upgrade Cost"), 2)),
             say_for(join("Zoom! Speed is now ", V("Speed")), 1)]),
], 450, 220)

guard = Compiler("guard")
guard.script([
    flag(), rot_style("left-right"), point_dir(-90), goto_xy(170, 0), show(), say(""),
], 20, 20)
guard.script([
    when_msg("start"),
    forever([
        # Patrol the vault while nobody is carrying a Gobo.
        repeat_until(eq(V("Carrying"), 1), [
            move(2),
            bounce(),
            if_(eq(rand(1, 40), 1), [point_dir(rand(-180, 180))]),
            if_(lt(x_pos(), 90), [point_dir(90)]),
            if_(gt(y_pos(), 125), [point_dir(180)]),
        ]),
        # Somebody grabbed a Gobo: sound the alarm and chase!
        say("Hey! Stop, thief!"),
        play("alarm"),
        set_var("Guard Speed", add(2.6, div(V("Gobos Stolen"), 4))),
        if_(gt(V("Guard Speed"), 5.5), [set_var("Guard Speed", 5.5)]),
        wait(0.4),
        repeat_until(eq(V("Carrying"), 0), [
            point_towards("Thief"),
            move(V("Guard Speed")),
            if_(lt(x_pos(), GUARD_WALL), [set_x(GUARD_WALL)]),
            if_(touching("Thief"), [
                set_var("Carrying", 0),
                change_var("Lives", -1),
                broadcast("caught"),
                say_for("Got you!", 1),
            ]),
        ]),
        say(""),
        if_(lt(V("Lives"), 1), [broadcast("game over")]),
        point_dir(90),
    ]),
], 20, 200)

slot = V("slot")
gobo = Compiler("gobo", local_vars=["state", "value", "rarity", "slot"])
gobo.script([
    flag(), hide(), set_var("state", 0),
], 20, 20)
gobo.script([
    when_msg("start"),
    forever([
        if_(lt(V("Waiting"), 3), [
            change_var("Waiting", 1),
            goto_xy(rand(125, 215), rand(-135, 105)),
            clone_me(),
            wait(1.5),
        ]),
        wait(0.1),
    ]),
], 20, 160)
gobo.script([
    when_cloned(),
    set_var("rarity", rand(1, 100)),
    if_else(lt(V("rarity"), 71),
            [costume("Gobo"), set_var("value", 2)],
            [if_else(lt(V("rarity"), 95),
                     [costume("Gold Gobo"), set_var("value", 10)],
                     [costume("Diamond Gobo"), set_var("value", 50)])]),
    size(100), set_var("state", 0), show(),
    say(join("$", join(V("value"), "/s"))),
    wait_until(and_(touching("Thief"), eq(V("Carrying"), 0))),
    # Grabbed!
    set_var("Carrying", 1), set_var("state", 1), change_var("Waiting", -1),
    say(""), play("pop"), front(),
    repeat_until(lt(prop_of("x position", "Thief"), BASE_EDGE), [
        goto_xy(prop_of("x position", "Thief"), add(prop_of("y position", "Thief"), 32)),
    ]),
    if_(eq(V("Carrying"), 0), [delete_clone()]),
    # Safe in YOUR BASE: it now earns money every second.
    set_var("state", 2), set_var("Carrying", 0),
    change_var("Gobos Stolen", 1), change_var("Income", V("value")),
    play("cash"),
    set_var("slot", mod(sub(V("Gobos Stolen"), 1), 15)),
    goto_xy(add(-222, mul(mod(slot, 3), 32)), sub(110, mul(floor(div(slot, 3)), 50))),
    size(70), back(),
    forever([change_y(3), wait(0.3), change_y(-3), wait(0.3)]),
], 350, 20)
gobo.script([
    when_msg("caught"),
    if_(eq(V("state"), 1), [delete_clone()]),
], 350, 700)

message = Compiler("message")
message.script([
    when_msg("title"),
    goto_xy(0, 0), costume("title"), show(), front(),
    wait_until(key("space")),
    hide(),
], 20, 20)
message.script([when_msg("you win"), costume("win"), show(), front(), stop_all()], 20, 250)
message.script([when_msg("game over"), costume("game over"), show(), front(), stop_all()], 20, 400)

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


def sprite(comp, name, costumes, sounds, layer, x=0, y=0, visible=True, local_vars=()):
    return {"isStage": False, "name": name,
            "variables": {comp.var_id(v): [v, 0] for v in local_vars},
            "lists": {}, "broadcasts": {}, "blocks": comp.blocks, "comments": {},
            "currentCostume": 0, "costumes": costumes, "sounds": sounds, "volume": 100,
            "layerOrder": layer, "visible": visible, "x": x, "y": y, "size": 100, "direction": 90,
            "draggable": False, "rotationStyle": "left-right"}


START_VALUES = {"Lives": 3, "Speed": 4, "Upgrade Cost": 50, "Guard Speed": 2.6}
targets = [
    {"isStage": True, "name": "Stage",
     "variables": {vid(v): [v, START_VALUES.get(v, 0)] for v in GLOBAL_VARS},
     "lists": {}, "broadcasts": {bid(b): b for b in BROADCASTS}, "blocks": stage.blocks,
     "comments": {}, "currentCostume": 0,
     "costumes": [svg_costume("Gobo Land", BACKDROP, 240, 180)],
     "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60, "videoTransparency": 50,
     "videoState": "on", "textToSpeechLanguage": None},
    sprite(gobo, "Gobo", [svg_costume("Gobo", GOBO), svg_costume("Gold Gobo", GOLD_GOBO),
                          svg_costume("Diamond Gobo", DIAMOND_GOBO)],
           [wav_sound("pop", POP), wav_sound("cash", CASH)], 1, 170, 0, visible=False,
           local_vars=["state", "value", "rarity", "slot"]),
    sprite(guard, "Guard", [svg_costume("Guard", GUARD)], [wav_sound("alarm", ALARM)], 2, 170, 0),
    sprite(thief, "Thief", [svg_costume("Thief", THIEF)], [wav_sound("ouch", OUCH)], 3, HOME_X, 0),
    sprite(message, "Message", [svg_costume("title", TITLE_CARD, 240, 180),
                                svg_costume("win", WIN_CARD, 240, 180),
                                svg_costume("game over", LOSE_CARD, 240, 180)], [], 4, visible=False),
]


def monitor(name, x, y):
    return {"id": vid(name), "mode": "default", "opcode": "data_variable",
            "params": {"VARIABLE": name}, "spriteName": None, "value": 0, "width": 0, "height": 0,
            "x": x, "y": y, "visible": True, "sliderMin": 0, "sliderMax": 100, "isDiscrete": True}


project = {
    "targets": targets,
    "monitors": [monitor("Money", 5, 5), monitor("Income", 120, 5), monitor("Gobos Stolen", 235, 5),
                 monitor("Lives", 385, 5)],
    "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "build_sb3.py"},
}

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("project.json", json.dumps(project))
    for fname, data in assets.items():
        z.writestr(fname, data)

if __name__ == "__main__":
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {len(assets)} assets)")
