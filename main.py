#!/usr/bin/env python3
"""Draw Sunday 22 November 2026's world news as a newspaper front page.

Only the Python 3.13 standard library is used. There is no network
access, no clock and no randomness anywhere, so every run writes the
same bytes to $MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png when
that variable is unset).

The page is a broadsheet front: a masthead and date bar, one large lead
story, five more stories in a grid with small hand-drawn icons, and a
ticker of further news along the bottom edge.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024


# --------------------------------------------------------------- PNG writer
def png_chunk(kind, payload):
    """One PNG chunk: length, type, data, CRC."""
    size = struct.pack(">I", len(payload))
    crc = struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    return size + kind + payload + crc


def save_png(path, width, height, rgb):
    """Write raw RGB bytes as a PNG file.

    Every scanline is stored unfiltered (filter byte 0) and the image
    data is compressed at zlib level 9, so the output is the same on
    every run.
    """
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    rows = b"".join(
        b"\x00" + rgb[y * width * 3:(y + 1) * width * 3]
        for y in range(height)
    )
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(rows, 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(data)


# ------------------------------------------------------------ 5x7 bitmap font
# One glyph is seven rows; each row is a five-bit number, bit 4 being
# the leftmost pixel. Only capitals, digits and the punctuation the
# headlines need are included.
GLYPHS = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ";": (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "!": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    "?": (0b01110, 0b10001, 0b00001, 0b00110, 0b00100, 0, 0b00100),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "%": (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    "(": (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ")": (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    "&": (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "+": (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    "=": (0, 0, 0b11111, 0, 0b11111, 0, 0),
}

# One glyph is 5 px wide with a 1 px gap, times the scale factor.
STEP = 6


def measure(text, scale):
    """Pixel width of text drawn at the given scale."""
    return len(text) * STEP * scale - scale


def wrap(text, max_width, scale):
    """Greedy word wrap: as many whole words per line as fit."""
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if measure(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------------- surface
class Surface:
    """An RGB pixel buffer with the small drawing kit the page needs."""

    def __init__(self, width, height, background):
        self.w = width
        self.h = height
        self.buf = bytearray(background * (width * height))

    def put(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = colour

    def fill(self, x, y, w, h, colour):
        """Solid rectangle, clipped to the page."""
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:(yy * self.w + x1) * 3] = colour * (x1 - x0)

    def frame(self, x, y, w, h, colour, thick=1):
        """Rectangle outline of the given thickness."""
        self.fill(x, y, w, thick, colour)
        self.fill(x, y + h - thick, w, thick, colour)
        self.fill(x, y, thick, h, colour)
        self.fill(x + w - thick, y, thick, h, colour)

    def segment(self, x0, y0, x1, y1, colour, thick=1):
        """Bresenham line with a square brush of side `thick`."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(-(thick // 2), thick // 2 + 1):
                for b in range(-(thick // 2), thick // 2 + 1):
                    self.put(x0 + a, y0 + b, colour)
            if x0 == x1 and y0 == y1:
                return
            twice = 2 * err
            if twice >= dy:
                err += dy
                x0 += sx
            if twice <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, colour):
        """Filled circle, scanline by scanline."""
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill(cx - dx, yy, dx * 2 + 1, 1, colour)

    def ring(self, cx, cy, r, colour, thick=2):
        """Circle outline, drawn as one ring per radius step."""
        for rr in range(r - thick + 1, r + 1):
            for ang in range(360):
                x = cx + int(rr * math.cos(ang * math.pi / 180))
                y = cy + int(rr * math.sin(ang * math.pi / 180))
                self.put(x, y, colour)

    def poly(self, a, b, c, colour):
        """Filled triangle, scanline by scanline.

        The y range comes from the corners truncated to integers, while
        the edge crossings are interpolated from the original corners.
        """
        (x1, y1), (x2, y2), (x3, y3) = a, b, c
        x1, y1, x2, y2, x3, y3 = (int(v) for v in (x1, y1, x2, y2, x3, y3))
        top, bottom = min(y1, y2, y3), max(y1, y2, y3)
        for yy in range(top, bottom + 1):
            xs = []
            for (xa, ya), (xb, yb) in ((a, b), (b, c), (c, a)):
                if ya == yb:
                    continue
                if min(ya, yb) <= yy <= max(ya, yb):
                    xs.append(xa + (xb - xa) * (yy - ya) / (yb - ya))
            if len(xs) >= 2:
                self.fill(int(min(xs)), yy,
                          int(max(xs)) - int(min(xs)) + 1, 1, colour)

    def draw_text(self, x, y, text, colour, scale=2, align="left"):
        """One line of the bitmap font. Returns the x past the last glyph."""
        text = text.upper()
        if align == "center":
            x -= measure(text, scale) // 2
        elif align == "right":
            x -= measure(text, scale)
        for ch in text:
            glyph = GLYPHS.get(ch, GLYPHS["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits >> (4 - col) & 1:
                        self.fill(x + col * scale, y + row * scale,
                                  scale, scale, colour)
            x += STEP * scale
        return x

    def paragraph(self, x, y, text, colour, scale, width, leading=None):
        """Wrapped, left-aligned text; returns the y below the block."""
        if leading is None:
            leading = 9 * scale
        for line in wrap(text, width, scale):
            self.draw_text(x, y, line, colour, scale)
            y += leading
        return y

    def write(self, path):
        save_png(path, self.w, self.h, bytes(self.buf))


# ------------------------------------------------------------------- palette
PAPER = bytes((245, 239, 224))
WHITE = bytes((252, 250, 244))
INK = bytes((18, 18, 20))
GRAY = bytes((105, 105, 100))
RED = bytes((178, 34, 34))
NAVY = bytes((18, 38, 66))
GOLD = bytes((198, 142, 30))
TEAL = bytes((14, 110, 110))
GREEN = bytes((34, 120, 60))
BLUE = bytes((40, 90, 160))


# --------------------------------------------------------------------- icons
# Every icon draws inside a square of side `size` whose top-left corner
# is (x, y). Inside, positions are given in tenths of the side, so the
# same icon works at any size. px/py convert a tenth-coordinate to a
# pixel; u is one tenth of the side in pixels.
def draw_climate(page, x, y, size, ink=INK, accent=GREEN):
    """Globe with a small leaf at its lower right."""
    u = size / 10.0
    px = lambda v: int(x + v * u)
    py = lambda v: int(y + v * u)
    cx, cy, r = px(4.6), py(4.8), int(3.6 * u)
    page.ring(cx, cy, r, ink, 2)
    page.segment(cx - r, cy, cx + r, cy, ink, 1)
    page.segment(cx, cy - r, cx, cy + r, ink, 1)
    # leaf at lower right
    lx, ly = px(7.2), py(7.6)
    top = ly - int(1.6 * u)
    bot = ly + int(1.4 * u)
    page.poly((lx, top), (lx + int(1.8 * u), ly), (lx, bot), accent)
    page.poly((lx, top), (lx - int(1.4 * u), ly + int(0.4 * u)),
              (lx, bot), accent)
    page.segment(lx, bot, lx - int(1.2 * u), ly + int(2.4 * u), accent, 2)


def draw_coins(page, x, y, size, ink=INK, accent=GOLD):
    """Stack of three coins with a big percent sign above them."""
    u = size / 10.0
    px = lambda v: int(x + v * u)
    py = lambda v: int(y + v * u)
    for cy in (7.6, 5.4, 3.2):
        page.fill(px(1.2), py(cy), int(5.6 * u), int(1.8 * u), accent)
        page.frame(px(1.2), py(cy), int(5.6 * u), int(1.8 * u), ink, 1)
    page.draw_text(px(6.2), py(0.6), "%", ink, 3)


def draw_rocket(page, x, y, size, ink=INK, accent=RED):
    """Missile with its nose up, flying diagonally, flame behind it."""
    u = size / 10.0
    px = lambda v: int(x + v * u)
    py = lambda v: int(y + v * u)
    cx, cy = px(5), py(4.6)
    page.poly((cx, py(0.6)), (px(3.2), py(3.4)), (px(6.8), py(3.4)), accent)
    page.fill(px(3.2), py(3.4), int(3.6 * u), int(3.6 * u), ink)
    page.poly((px(3.2), py(7.0)), (px(1.6), py(8.6)), (px(3.2), py(5.6)), ink)
    page.poly((px(6.8), py(7.0)), (px(8.4), py(8.6)), (px(6.8), py(5.6)), ink)
    # flame and smoke puffs
    page.poly((px(4.0), py(7.0)), (px(6.0), py(7.0)), (cx, py(9.8)), GOLD)
    page.disc(px(2.2), py(9.0), max(1, int(0.5 * u)), GRAY)
    page.disc(px(8.0), py(9.2), max(1, int(0.4 * u)), GRAY)


def draw_ruins(page, x, y, size, ink=INK, accent=RED):
    """Damaged buildings with an explosion burst at the top right."""
    u = size / 10.0
    px = lambda v: int(x + v * u)
    py = lambda v: int(y + v * u)
    page.fill(px(0.6), py(5.4), int(3.0 * u), int(4.6 * u), ink)
    page.fill(px(4.2), py(6.4), int(3.0 * u), int(3.6 * u), NAVY)
    page.fill(px(7.6), py(4.6), int(1.8 * u), int(5.4 * u), ink)
    # broken top edge on the left building
    page.poly((px(0.6), py(5.4)), (px(2.0), py(4.2)), (px(3.6), py(5.4)), PAPER)
    # explosion burst top-right
    bx, by = px(7.8), py(2.0)
    page.disc(bx, by, int(1.1 * u), accent)
    for dx, dy in ((-2.2, -1.2), (2.2, -1.4), (-2.6, 0.8), (2.6, 0.6),
                   (-1.0, -2.4), (1.2, -2.2), (0, 2.6)):
        page.segment(bx, by, int(bx + dx * u), int(by + dy * u), accent, 2)


def draw_tower(page, x, y, size, ink=INK, accent=RED):
    """Skyscraper with setbacks, lit windows and an impact burst."""
    u = size / 10.0
    px = lambda v: int(x + v * u)
    py = lambda v: int(y + v * u)
    page.fill(px(3.4), py(1.2), int(3.2 * u), int(8.8 * u), NAVY)
    page.fill(px(2.6), py(4), int(4.8 * u), int(6 * u), NAVY)
    page.fill(px(1.8), py(7), int(6.4 * u), int(3 * u), ink)
    for wy in range(6):
        for wx in (3.8, 5.0, 6.2):
            page.fill(px(wx), int(y + (2.0 + wy * 1.1) * u),
                      max(1, int(0.4 * u)), max(1, int(0.4 * u)), GOLD)
    # impact burst at the top
    bx, by = px(5), py(1.0)
    page.disc(bx, by, int(0.9 * u), accent)
    for dx, dy in ((-2.4, -1.0), (2.4, -1.2), (-2.0, 1.4), (2.2, 1.2), (0, -2.4)):
        page.segment(bx, by, int(bx + dx * u), int(by + dy * u), accent, 2)


def draw_quake(page, x, y, size, ink=INK, accent=TEAL):
    """Two leaning buildings over a zigzag ground crack."""
    u = size / 10.0
    px = lambda v: int(x + v * u)
    py = lambda v: int(y + v * u)
    page.fill(px(2.0), py(2.0), int(3.4 * u), int(5.6 * u), ink)
    page.fill(px(6.0), py(3.4), int(2.6 * u), int(4.2 * u), NAVY)
    for wy in (2.8, 4.2, 5.6):
        for wx in (2.6, 3.8, 6.5, 7.5):
            page.fill(px(wx), py(wy),
                      max(1, int(0.35 * u)), max(1, int(0.35 * u)), GOLD)
    # zigzag crack across the ground
    crack = [(0.4, 8.2), (2.2, 7.4), (3.6, 8.6), (5.4, 7.6), (7.0, 8.8), (9.6, 8.0)]
    for (ax, ay), (bx, by) in zip(crack, crack[1:]):
        page.segment(px(ax), py(ay), px(bx), py(by), accent, 3)
    # shaking motion marks
    page.segment(px(1.0), py(1.2), px(1.0), py(3.0), accent, 2)
    page.segment(px(9.0), py(2.0), px(9.0), py(3.8), accent, 2)


# -------------------------------------------------------------------- panels
def news_panel(page, x, y, w, h, tag, colour, headline, summary,
               icon=None, icon_side=72, head_scale=2, sum_scale=2):
    """One white news panel: coloured tag bar, icon, headline, summary."""
    page.fill(x, y, w, h, WHITE)
    page.frame(x, y, w, h, INK, 2)
    page.fill(x, y, w, 26, colour)
    page.draw_text(x + 10, y + 6, tag, WHITE, 2)
    inner = x + 12
    content = w - 24
    cy = y + 36
    if icon is not None:
        icon(page, x + (w - icon_side) // 2, cy, icon_side)
        cy += icon_side + 8
    cy = page.paragraph(inner, cy, headline, INK, head_scale, content,
                        9 * head_scale + 4)
    page.paragraph(inner, cy + 4, summary, GRAY, sum_scale, content,
                   9 * sum_scale + 2)
    return cy


# ------------------------------------------------------------------- stories
# Each story is (tag, bar colour, headline, summary, icon). All six were
# checked against real reporting of 22 November 2026: the COP31 overtime
# deal, the EU Big Tech tax, the missile strike on Zelensky's hometown,
# fire in Gaza, Houthi strikes on Riyadh, and the Peru quake. The ticker
# carries the day's further news.
LEAD = (
    "CLIMATE - ANTALYA",
    "COP31 NEARS FINAL DEAL AFTER ALL-NIGHT TALKS",
    "AFTER TALKS RAN PAST THEIR NOV 20 DEADLINE, PRESIDENTS OF "
    "AUSTRALIA AND TURKEY PUT A NEW PACKAGE TO NEARLY 200 "
    "NATIONS. THE PLENARY RECONVENES TO APPROVE IT; 130 "
    "COUNTRIES WANT FOSSIL-FUEL PHASE-OUT WORDING BACK IN.",
)

SECOND_ROW = [
    (
        "ECONOMY - BRUSSELS", BLUE,
        "EU PROPOSES TAX ON BIG TECH",
        "BRUSSELS PUTS FORWARD A NEW LEVY ON LARGE TECHNOLOGY FIRMS.",
        draw_coins,
    ),
    (
        "WAR - UKRAINE", NAVY,
        "MISSILE ATTACK ON ZELENSKY'S HOMETOWN KILLS 2",
        "BALLISTIC MISSILE STRIKE IN CENTRAL UKRAINE WOUNDS SCORES MORE.",
        draw_rocket,
    ),
]

THIRD_ROW = [
    (
        "CONFLICT - GAZA", RED,
        "ISRAELI FIRE KILLS FOUR MORE IN GAZA",
        "FOUR MORE KILLED AS STRIKES GO ON DESPITE THE CEASEFIRE.",
        draw_ruins,
    ),
    (
        "CONFLICT - RIYADH", RED,
        "HOUTHIS LAUNCH REVENGE STRIKES ON RIYADH",
        "MISSILES FIRED AT THE SAUDI CAPITAL IN THE LATEST GULF STRIKES.",
        draw_tower,
    ),
    (
        "DISASTER - PERU", TEAL,
        "6.7-MAGNITUDE QUAKE HITS PERU",
        "STRONG TREMOR SHAKES THE COUNTRY; NO DEATHS REPORTED.",
        draw_quake,
    ),
]

TICKER = [
    "ALSO TODAY: BALTIC SHIP ABLAZE AFTER DRONE STRIKE - 24 DEAD IN NIGERIA BOAT",
    "FRANCE PROTESTS ENTER SIXTH WEEKEND - TRUMP VOWS 10% CARD RATE CAP",
]


# ------------------------------------------------------------------- compose
def build_page():
    page = Surface(PAGE_W, PAGE_H, PAPER)
    m = 28
    cw = PAGE_W - 2 * m

    # Masthead
    page.draw_text(PAGE_W // 2, 34, "THE WORLD IN ONE DAY", INK, 5,
                   align="center")
    page.fill(m, 82, cw, 3, INK)
    page.fill(m, 92, cw, 38, RED)
    page.draw_text(PAGE_W // 2, 100, "SUNDAY, 22 NOVEMBER 2026 - WORLD NEWS",
                   WHITE, 3, align="center")
    page.fill(m, 140, cw, 3, INK)

    # Lead story: icon on the left, headline and summary on the right
    lx, ly, lw, lh = m, 156, cw, 210
    page.fill(lx, ly, lw, lh, WHITE)
    page.frame(lx, ly, lw, lh, INK, 2)
    page.fill(lx, ly, lw, 26, NAVY)
    page.draw_text(lx + 10, ly + 6, LEAD[0], WHITE, 2)
    draw_climate(page, lx + 24, ly + 52, 120)
    tx = lx + 180
    tw = lw - 180 - 24
    hy = page.paragraph(tx, ly + 48, LEAD[1], INK, 3, tw, 34)
    page.paragraph(tx, hy + 10, LEAD[2], GRAY, 2, tw, 20)

    # Second row: two half-width panels
    y2, h2 = 382, 228
    w2 = (cw - 16) // 2
    for i, (tag, colour, head, summ, icon) in enumerate(SECOND_ROW):
        news_panel(page, m + i * (w2 + 16), y2, w2, h2,
                   tag, colour, head, summ,
                   icon=icon, icon_side=72, head_scale=2, sum_scale=2)

    # Third row: three third-width panels
    y3, h3 = 626, 228
    w3 = (cw - 32) // 3
    for i, (tag, colour, head, summ, icon) in enumerate(THIRD_ROW):
        news_panel(page, m + i * (w3 + 16), y3, w3, h3,
                   tag, colour, head, summ,
                   icon=icon, icon_side=64, head_scale=2, sum_scale=2)

    # Ticker: the day's further news
    ty, th = 870, 84
    page.fill(m, ty, cw, th, INK)
    page.draw_text(PAGE_W // 2, ty + 12, TICKER[0], WHITE, 2, align="center")
    page.draw_text(PAGE_W // 2, ty + 44, TICKER[1], WHITE, 2, align="center")

    # Footer
    page.draw_text(PAGE_W // 2, 972, "DRAWN FROM 22 NOVEMBER 2026 REPORTS",
                   GRAY, 2, align="center")
    return page


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    build_page().write(os.path.join(out, "entry.png"))


if __name__ == "__main__":
    main()
