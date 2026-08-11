#!/usr/bin/env python3
"""
ui.py — terminal styling for social-post-forge. Standard library only.

Forge palette: cold stock at the top of the heat, molten at the bottom.
Everything degrades cleanly: truecolor -> 256 colour -> 16 colour -> plain
text. Piping to a file or setting NO_COLOR gives you clean ASCII, so the
output stays greppable.

    from ui import c, banner, box, rule, step, score_bar, EMBER
"""

import os
import shutil
import sys

# ---------------------------------------------------------------- capability

def _color_depth():
    """0 = none, 1 = 16 colour, 2 = 256 colour, 3 = truecolor."""
    if os.environ.get("NO_COLOR") is not None:
        return 0
    force = os.environ.get("FORCE_COLOR")
    if force in ("1", "2", "3"):
        return {"1": 1, "2": 2, "3": 3}[force]
    if not sys.stdout.isatty():
        return 0
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return 0
    if os.environ.get("COLORTERM", "") in ("truecolor", "24bit"):
        return 3
    if "256" in term:
        return 2
    return 1 if term else 0


DEPTH = _color_depth()
WIDTH = min(shutil.get_terminal_size((100, 24)).columns, 100)

# ------------------------------------------------------------------ palette

EMBER = ["#ffd76a", "#ffab3d", "#ff7a1a", "#f4511e", "#cb2a2a"]

INK = "#e8edf4"
MUTED = "#8b95a5"
FAINT = "#5f6a79"
GOOD = "#58c878"
WARN = "#ffbd2e"
BAD = "#ff5f56"
COOL = "#4a9eda"

_BASIC = {  # nearest 16-colour fallback
    "#ffd76a": 93, "#ffab3d": 93, "#ff7a1a": 91, "#f4511e": 91, "#cb2a2a": 31,
    "#e8edf4": 97, "#8b95a5": 37, "#5f6a79": 90, "#58c878": 92,
    "#ffbd2e": 93, "#ff5f56": 91, "#4a9eda": 94,
}


def _rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def c(text, color=None, bold=False, dim=False, underline=False):
    """Colour some text, or hand it back untouched when colour is off."""
    if DEPTH == 0 or color is None and not (bold or dim or underline):
        return text
    codes = []
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if underline:
        codes.append("4")
    if color and DEPTH == 3:
        r, g, b = _rgb(color)
        codes.append("38;2;%d;%d;%d" % (r, g, b))
    elif color and DEPTH == 2:
        r, g, b = _rgb(color)
        # 6x6x6 cube
        idx = 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)
        codes.append("38;5;%d" % idx)
    elif color:
        codes.append(str(_BASIC.get(color, 37)))
    if not codes:
        return text
    return "\033[%sm%s\033[0m" % (";".join(codes), text)


def gradient(text, colors=None):
    """Spread a colour ramp across a string, character by character."""
    if DEPTH < 2:
        return c(text, (colors or EMBER)[0], bold=True)
    colors = colors or EMBER
    stops = [_rgb(x) for x in colors]
    n = max(len(text) - 1, 1)
    out = []
    for i, ch in enumerate(text):
        if ch == " ":
            out.append(ch)
            continue
        pos = i / n * (len(stops) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(stops) - 1)
        t = pos - lo
        r = int(stops[lo][0] + (stops[hi][0] - stops[lo][0]) * t)
        g = int(stops[lo][1] + (stops[hi][1] - stops[lo][1]) * t)
        b = int(stops[lo][2] + (stops[hi][2] - stops[lo][2]) * t)
        out.append("\033[38;2;%d;%d;%dm%s" % (r, g, b, ch))
    return "".join(out) + "\033[0m"


# ------------------------------------------------------------------- banner

_GLYPHS = {
    "F": ["█████", "█    ", "████ ", "█    ", "█    "],
    "O": [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "G": [" ████", "█    ", "█  ██", "█   █", " ███ "],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
}


def banner(subtitle="source in, posts out"):
    """The forge wordmark, heat-mapped top to bottom."""
    word = "FORGE"
    rows = []
    for r in range(5):
        rows.append("  ".join(_GLYPHS[ch][r] for ch in word))

    out = []
    if DEPTH == 0:
        out.append("social-post-forge")
        out.append(subtitle)
        out.append("")
        return "\n".join(out)

    out.append("")
    out.append("  " + c("social-post-", MUTED) + c("forge", EMBER[2], bold=True))
    out.append("")
    # rows run cool at the top to molten at the bottom, like heated stock
    for i, row in enumerate(rows):
        out.append("  " + c(row, EMBER[i], bold=True))
    out.append("")
    out.append("  " + c(subtitle, FAINT))
    out.append("")
    return "\n".join(out)


# -------------------------------------------------------------------- rules

def rule(label=None, color=None):
    color = color or EMBER[3]
    if not label:
        return c("─" * WIDTH, FAINT)
    head = "── %s " % label
    return c("──", color) + " " + c(label, INK, bold=True) + " " + \
        c("─" * max(0, WIDTH - len(head) - 2), FAINT)


def heatbar(width=None):
    """A thin ember gradient bar."""
    width = width or WIDTH
    return gradient("━" * width)


# --------------------------------------------------------------------- boxes

def box(title, lines, color=None, width=None):
    color = color or EMBER[2]
    width = width or WIDTH
    inner = width - 2
    out = []
    t = " %s " % title
    out.append(c("┌", color) + c("─", color) + c(t, INK, bold=True) +
               c("─" * max(0, inner - len(t) - 1), color) + c("┐", color))
    for line in lines:
        visible = _strip(line)
        pad = max(0, inner - len(visible) - 1)
        out.append(c("│", color) + " " + line + " " * pad + c("│", color))
    out.append(c("└", color) + c("─" * inner, color) + c("┘", color))
    return "\n".join(out)


def _strip(s):
    """Length of a string ignoring ANSI escapes."""
    out, i = [], 0
    while i < len(s):
        if s[i] == "\033":
            while i < len(s) and s[i] != "m":
                i += 1
            i += 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


# --------------------------------------------------------------------- steps

_MARKS = {
    "run": ("◆", EMBER[2]),
    "ok": ("✓", GOOD),
    "warn": ("▲", WARN),
    "fail": ("✗", BAD),
    "skip": ("·", FAINT),
}

# Plain output can land in a log file or a terminal with no unicode support,
# so drop to ASCII whenever colour is off.
_MARKS_ASCII = {
    "run": (">", None), "ok": ("+", None), "warn": ("!", None),
    "fail": ("x", None), "skip": ("-", None),
}


def step(n, total, title, state="run", detail=""):
    marks = _MARKS if DEPTH else _MARKS_ASCII
    mark, col = marks.get(state, marks["run"])
    head = c("%s" % mark, col, bold=True)
    counter = c("%d/%d" % (n, total), FAINT)
    line = "%s %s %s" % (head, counter, c(title, INK, bold=(state == "run")))
    if detail:
        line += "  " + c(detail, MUTED)
    return line


def score_bar(label, value, out_of=5, threshold=4):
    """A filled bar that turns molten when it fails the threshold."""
    filled = int(round(value / out_of * 10))
    col = GOOD if value >= threshold else (WARN if value >= threshold - 1 else BAD)
    bar = c("█" * filled, col) + c("░" * (10 - filled), FAINT)
    flag = "" if value >= threshold else c("  below threshold", BAD)
    return "  %s %s %s%s" % (
        c(label.ljust(14), MUTED), bar, c("%d/%d" % (value, out_of), col, bold=True), flag)


def kv(key, value, color=None):
    return "  %s %s" % (c((key + ":").ljust(16), FAINT), c(str(value), color or INK))


def verdict(text, ok=True):
    col = GOOD if ok else BAD
    mark = "✓" if ok else "✗"
    return "%s %s" % (c(mark, col, bold=True), c(text, col, bold=True))
