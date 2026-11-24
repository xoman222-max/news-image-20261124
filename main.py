#!/usr/bin/env python3
"""news-image-20261124: draw one image summing up the world news of
Tuesday 24 November 2026. Pure Python 3 stdlib (no PIL in the reviewer
container): own 5x7 bitmap font, own PNG encoder, flat vector drawing.
Run: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png (1600x2100) to $MAKEFUN_OUTPUT_DIR or ./out.
Deterministic: no clock, no randomness, no network.
"""
import os
import struct
import zlib

# ---------------------------------------------------------------- PNG output
def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

def write_png(path, w, h, rgb):
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + _chunk(b"IDAT", zlib.compress(raw, 6))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)

# ------------------------------------------------------------------ palette
PAPER   = (247, 243, 232)
INK     = (20, 20, 20)
RED     = (176, 30, 30)
BLUE    = (31, 78, 121)
GOLD    = (176, 138, 28)
TEAL    = (18, 110, 105)
GREEN   = (46, 110, 52)
PURPLE  = (98, 58, 130)
ORANGE  = (196, 96, 20)
GREY    = (110, 108, 100)
LIGHT   = (232, 226, 210)
WHITE   = (255, 255, 255)
BROWN   = (122, 84, 40)
REGION_COLORS = {
    "NORTH AMERICA": BLUE, "SOUTH AMERICA": GREEN, "EUROPE": PURPLE,
    "MIDDLE EAST": ORANGE, "AFRICA": BROWN, "ASIA": RED,
    "OCEANIA": TEAL, "GLOBAL": INK,
}

# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg=PAPER):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = yy * self.w * 3
            for xx in range(x0, x1):
                i = base + xx * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= (r + t) ** 2:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = x0 + dx * i // steps
            y = y0 + dy * i // steps
            self.rect(x - t // 2, y - t // 2, t, t, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.set(x, y, c)

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.px[i], self.px[i + 1], self.px[i + 2])

    def save(self, path):
        write_png(path, self.w, self.h, bytes(self.px))

def blit_scaled(cv, src, x, y, w, h):
    # nearest-neighbour downscale of src canvas into cv at (x, y, w, h)
    for dy in range(h):
        sy = dy * src.h // h
        for dx in range(w):
            sx = dx * src.w // w
            cv.set(x + dx, y + dy, src.get(sx, sy))

# ------------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 bits, '1' = ink. Uppercase, digits, punctuation only.
FONT = {}
def _g(ch, rows):
    FONT[ch] = rows

_g("A", ["01110", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("B", ["11110", "10001", "10001", "11110", "10001", "10001", "11110"])
_g("C", ["01110", "10001", "10000", "10000", "10000", "10001", "01110"])
_g("D", ["11110", "10001", "10001", "10001", "10001", "10001", "11110"])
_g("E", ["11111", "10000", "10000", "11110", "10000", "10000", "11111"])
_g("F", ["11111", "10000", "10000", "11110", "10000", "10000", "10000"])
_g("G", ["01110", "10001", "10000", "10111", "10001", "10001", "01111"])
_g("H", ["10001", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("I", ["01110", "00100", "00100", "00100", "00100", "00100", "01110"])
_g("J", ["00111", "00010", "00010", "00010", "00010", "10010", "01100"])
_g("K", ["10001", "10010", "10100", "11000", "10100", "10010", "10001"])
_g("L", ["10000", "10000", "10000", "10000", "10000", "10000", "11111"])
_g("M", ["10001", "11011", "10101", "10101", "10001", "10001", "10001"])
_g("N", ["10001", "11001", "10101", "10011", "10001", "10001", "10001"])
_g("O", ["01110", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("P", ["11110", "10001", "10001", "11110", "10000", "10000", "10000"])
_g("Q", ["01110", "10001", "10001", "10001", "10101", "10010", "01101"])
_g("R", ["11110", "10001", "10001", "11110", "10100", "10010", "10001"])
_g("S", ["01111", "10000", "10000", "01110", "00001", "00001", "11110"])
_g("T", ["11111", "00100", "00100", "00100", "00100", "00100", "00100"])
_g("U", ["10001", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("V", ["10001", "10001", "10001", "10001", "10001", "01010", "00100"])
_g("W", ["10001", "10001", "10001", "10101", "10101", "11011", "10001"])
_g("X", ["10001", "10001", "01010", "00100", "01010", "10001", "10001"])
_g("Y", ["10001", "10001", "01010", "00100", "00100", "00100", "00100"])
_g("Z", ["11111", "00001", "00010", "00100", "01000", "10000", "11111"])
_g("0", ["01110", "10001", "10011", "10101", "11001", "10001", "01110"])
_g("1", ["00100", "01100", "00100", "00100", "00100", "00100", "01110"])
_g("2", ["01110", "10001", "00001", "00110", "01000", "10000", "11111"])
_g("3", ["11111", "00010", "00100", "00010", "00001", "10001", "01110"])
_g("4", ["00010", "00110", "01010", "10010", "11111", "00010", "00010"])
_g("5", ["11111", "10000", "11110", "00001", "00001", "10001", "01110"])
_g("6", ["00110", "01000", "10000", "11110", "10001", "10001", "01110"])
_g("7", ["11111", "00001", "00010", "00100", "01000", "01000", "01000"])
_g("8", ["01110", "10001", "10001", "01110", "10001", "10001", "01110"])
_g("9", ["01110", "10001", "10001", "01111", "00001", "00010", "01100"])
_g(" ", ["00000", "00000", "00000", "00000", "00000", "00000", "00000"])
_g(".", ["00000", "00000", "00000", "00000", "00000", "01100", "01100"])
_g(",", ["00000", "00000", "00000", "00000", "01100", "00100", "01000"])
_g(":", ["00000", "01100", "01100", "00000", "01100", "01100", "00000"])
_g(";", ["00000", "01100", "01100", "00000", "01100", "00100", "01000"])
_g("!", ["00100", "00100", "00100", "00100", "00100", "00000", "00100"])
_g("?", ["01110", "10001", "00001", "00110", "00100", "00000", "00100"])
_g("'", ["00100", "00100", "01000", "00000", "00000", "00000", "00000"])
_g('"', ["01010", "01010", "00000", "00000", "00000", "00000", "00000"])
_g("-", ["00000", "00000", "00000", "01110", "00000", "00000", "00000"])
_g("(", ["00010", "00100", "01000", "01000", "01000", "00100", "00010"])
_g(")", ["01000", "00100", "00010", "00010", "00010", "00100", "01000"])
_g("/", ["00001", "00010", "00010", "00100", "01000", "01000", "10000"])
_g("%", ["11001", "11010", "00010", "00100", "01000", "01011", "10011"])
_g("+", ["00000", "00100", "00100", "11111", "00100", "00100", "00000"])
_g("=", ["00000", "00000", "11111", "00000", "11111", "00000", "00000"])
_g("&", ["01100", "10010", "10100", "01000", "10101", "10010", "01101"])
_g("$", ["00100", "01111", "10100", "01110", "00101", "11110", "00100"])
_g("#", ["01010", "01010", "11111", "01010", "11111", "01010", "01010"])
_g("@", ["01110", "10001", "10111", "10101", "10110", "10000", "01110"])
_g("*", ["00000", "10101", "01110", "11111", "01110", "10101", "00000"])
_g("_", ["00000", "00000", "00000", "00000", "00000", "00000", "11111"])
_g("|", ["00100", "00100", "00100", "00100", "00100", "00100", "00100"])
_g("<", ["00010", "00100", "01000", "10000", "01000", "00100", "00010"])
_g(">", ["01000", "00100", "00010", "00001", "00010", "00100", "01000"])

def text_w(s, scale):
    return len(s) * 6 * scale - scale

def draw_text(cv, x, y, s, scale, color):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT["?"])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "1":
                    cv.rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx

def draw_text_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s.upper(), scale) // 2, y, s, scale, color)

def wrap_text(s, max_w, scale):
    words = s.upper().split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_para(cv, x, y, s, max_w, scale, color, lh=None):
    lh = lh or (7 * scale + 4)
    for ln in wrap_text(s, max_w, scale):
        draw_text(cv, x, y, ln, scale, color)
        y += lh
    return y

# ------------------------------------------------------------- flat pictograms
# Each paints a simple flat-vector illustration inside (x, y, w, h).
def _bg(cv, x, y, w, h, c):
    cv.rect(x, y, w, h, c)

def icon_chip(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (24, 38, 54))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 34, cy - 34, 68, 68, (0, 190, 150))
    cv.rect(cx - 22, cy - 22, 44, 44, (24, 38, 54))
    cv.rect(cx - 12, cy - 12, 24, 24, (0, 190, 150))
    for i in range(5):
        px = cx - 28 + i * 14
        cv.rect(px, cy - 46, 5, 12, (0, 190, 150))
        cv.rect(px, cy + 34, 5, 12, (0, 190, 150))
        cv.rect(cx - 46, cy - 28 + i * 14, 12, 5, (0, 190, 150))
        cv.rect(cx + 34, cy - 28 + i * 14, 12, 5, (0, 190, 150))

def icon_blast(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (64, 40, 32))
    cx, cy = x + w // 2, y + h // 2 + 8
    cv.rect(x + 14, y + h - 46, 52, 46, (120, 118, 110))
    cv.rect(x + 74, y + h - 66, 46, 66, (96, 94, 88))
    cv.rect(x + 128, y + h - 38, 56, 38, (120, 118, 110))
    cv.rect(x + 22, y + h - 38, 10, 10, (247, 243, 232))
    cv.rect(x + 84, y + h - 56, 10, 10, (247, 243, 232))
    cv.rect(x + 140, y + h - 30, 10, 10, (247, 243, 232))
    for dx, dy, r in [(-52, -42, 16), (-20, -58, 20), (14, -52, 24),
                      (48, -34, 16), (58, -58, 12), (-58, -18, 10)]:
        cv.circle(cx + dx, cy + dy, r, (255, 176, 32))
    cv.circle(cx + 14, cy - 52, 12, (255, 220, 120))
    cv.line(cx - 30, cy - 20, cx + 44, cy - 20, (255, 120, 40), 6)

def icon_capitol(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (238, 232, 214))
    cx = x + w // 2
    base = y + h - 14
    cv.rect(cx - 70, base - 12, 140, 12, INK)
    for i in range(5):
        px = cx - 62 + i * 28
        cv.rect(px, base - 62, 12, 50, INK)
    cv.rect(cx - 78, base - 72, 156, 10, INK)
    cv.rect(cx - 34, base - 104, 68, 32, INK)
    cv.circle(cx, base - 104, 22, INK)
    cv.rect(cx - 2, base - 136, 4, 12, INK)
    cv.circle(cx, base - 138, 5, RED)

def icon_phone(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (32, 32, 40))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 34, cy - 52, 68, 104, (240, 240, 240))
    cv.rect(cx - 27, cy - 44, 54, 76, (31, 78, 121))
    cv.rect(cx - 27, cy - 44, 54, 14, RED)
    cv.rect(cx - 20, cy - 18, 40, 5, WHITE)
    cv.rect(cx - 20, cy - 8, 28, 5, WHITE)
    cv.rect(cx - 20, cy + 2, 34, 5, WHITE)
    cv.rect(cx - 12, cy + 34, 24, 6, INK)
    cv.circle(cx + 52, cy - 44, 16, RED)
    draw_text(cv, cx + 47, cy - 51, "!", 2, WHITE)

def icon_card(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (24, 54, 40))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 74, cy - 42, 148, 84, (247, 243, 232))
    cv.rect(cx - 74, cy - 42, 148, 20, RED)
    cv.rect(cx - 62, cy - 6, 26, 20, GOLD)
    cv.rect(cx - 62, cy + 24, 90, 6, INK)
    draw_text(cv, cx - 62, cy - 36, "10%", 3, WHITE)

def icon_ship(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (16, 60, 88))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 70, cy - 34, 30, 26, (196, 96, 20))
    cv.rect(cx - 36, cy - 34, 30, 26, (247, 243, 232))
    cv.rect(cx - 70, cy - 8, 64, 26, (176, 138, 28))
    cv.rect(cx - 6, cy - 34, 30, 26, (196, 96, 20))
    cv.rect(cx + 28, cy - 34, 30, 26, (247, 243, 232))
    cv.rect(cx - 78, cy + 18, 164, 22, (120, 40, 30))
    cv.rect(cx - 78, cy + 40, 164, 6, (247, 243, 232))
    for i in range(4):
        cv.line(x + 12 + i * 44, y + h - 14, x + 34 + i * 44, y + h - 14,
                (255, 255, 255), 3)

def icon_flag(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (238, 232, 214))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 4, cy - 56, 8, 116, INK)
    cv.rect(cx + 4, cy - 56, 74, 30, RED)
    cv.rect(cx + 4, cy - 26, 74, 30, GOLD)
    cv.rect(cx + 4, cy + 4, 74, 30, GREEN)
    cv.circle(cx + 41, cy - 11, 9, INK)
    cv.rect(cx - 66, cy + 44, 48, 16, BLUE)
    cv.rect(cx - 18, cy + 44, 48, 16, (0, 120, 90))
    cv.rect(cx + 30, cy + 44, 48, 16, GOLD)

def icon_leaf(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (40, 70, 44))
    cx, cy = x + w // 2, y + h // 2
    cv.circle(cx, cy + 6, 40, (120, 170, 90))
    cv.circle(cx, cy - 26, 26, (120, 170, 90))
    cv.line(cx, cy - 52, cx, cy + 44, (40, 70, 44), 4)
    cv.circle(cx - 52, cy + 34, 14, GOLD)
    draw_text(cv, cx - 57, cy + 27, "!", 2, INK)

def icon_drone(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (52, 58, 66))
    cx, cy = x + w // 2, y + h // 2
    cv.line(cx - 44, cy - 30, cx + 44, cy + 30, (200, 200, 200), 6)
    cv.line(cx + 44, cy - 30, cx - 44, cy + 30, (200, 200, 200), 6)
    cv.rect(cx - 20, cy - 14, 40, 28, INK)
    cv.circle(cx, cy, 8, RED)
    for px, py in [(cx - 52, cy - 38), (cx + 52, cy - 38),
                   (cx - 52, cy + 38), (cx + 52, cy + 38)]:
        cv.circle(px, py, 12, (200, 200, 200))
        cv.line(px - 18, py, px + 18, py, (240, 240, 240), 3)

def icon_quake(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (238, 232, 214))
    cx, cy = x + w // 2, y + h // 2
    pts = [(-84, 10), (-60, 10), (-48, -34), (-30, 30), (-14, -44),
           (2, 22), (16, -18), (30, 8), (44, 8), (60, -26), (84, 6)]
    for i in range(len(pts) - 1):
        cv.line(cx + pts[i][0], cy + pts[i][1],
                cx + pts[i + 1][0], cy + pts[i + 1][1], RED, 5)
    cv.rect(x + 12, y + h - 58, 30, 58, GREY)
    cv.rect(x + 50, y + h - 40, 30, 40, GREY)
    cv.rect(x + 88, y + h - 66, 30, 66, GREY)
    cv.line(x + 12, y + h - 58, x + 118, y + h - 58, INK, 3)

def icon_crowd(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (238, 232, 214))
    cx, cy = x + w // 2, y + h // 2
    for dx, col in [(-52, BLUE), (0, RED), (52, GREEN)]:
        cv.circle(cx + dx, cy - 22, 22, col)
        cv.rect(cx + dx - 28, cy + 4, 56, 44, col)
    cv.rect(cx - 78, cy - 58, 14, 34, INK)
    cv.rect(cx + 64, cy - 58, 14, 34, INK)

def icon_ai(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (24, 38, 54))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 44, cy - 36, 88, 72, (0, 190, 150))
    cv.rect(cx - 30, cy - 20, 20, 14, (24, 38, 54))
    cv.rect(cx + 10, cy - 20, 20, 14, (24, 38, 54))
    cv.rect(cx - 30, cy + 8, 60, 6, (24, 38, 54))
    cv.line(cx - 44, cy - 36, cx - 62, cy - 54, (0, 190, 150), 4)
    cv.line(cx + 44, cy - 36, cx + 62, cy - 54, (0, 190, 150), 4)
    cv.circle(cx - 62, cy - 54, 6, GOLD)
    cv.circle(cx + 62, cy - 54, 6, GOLD)

def icon_shield(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (238, 232, 214))
    cx, cy = x + w // 2, y + h // 2
    pts = [(cx, cy + 52), (cx - 46, cy + 22), (cx - 46, cy - 34),
           (cx, cy - 52), (cx + 46, cy - 34), (cx + 46, cy + 22)]
    cv.poly(pts, BLUE)
    cv.circle(cx, cy - 8, 20, WHITE)
    draw_text(cv, cx - 7, cy - 15, "*", 2, RED)

def icon_germ(cv, x, y, w, h):
    _bg(cv, x, y, w, h, (40, 70, 44))
    cx, cy = x + w // 2, y + h // 2
    for dx, dy in [(-34, -30), (34, -30), (-44, 8), (44, 8),
                   (-26, 34), (26, 34), (0, -44), (0, 44)]:
        cv.line(cx, cy, cx + dx, cy + dy, (120, 170, 90), 5)
        cv.circle(cx + dx, cy + dy, 7, (120, 170, 90))
    cv.circle(cx, cy, 30, (160, 60, 60))
    cv.circle(cx - 10, cy - 8, 7, WHITE)
    cv.circle(cx + 10, cy - 8, 7, WHITE)
    cv.circle(cx, cy + 10, 7, WHITE)

ICONS = {"chip": icon_chip, "blast": icon_blast, "capitol": icon_capitol,
         "phone": icon_phone, "card": icon_card, "ship": icon_ship,
         "flag": icon_flag, "leaf": icon_leaf, "drone": icon_drone,
         "quake": icon_quake, "crowd": icon_crowd, "ai": icon_ai,
         "shield": icon_shield, "germ": icon_germ}

# ------------------------------------------------------------------ story data
# (number, headline, summary, region, source, icon, lon, lat)
FEATURED = [
    (1, "NVIDIA BRINGS HUANG BACK; SHARES SOAR 33%",
     "Nvidia reinstates co-founder Jensen Huang as chief executive, president "
     "and director, 11 days after he quit. The Nasdaq jumps 6.5% and the "
     "S&P 500 4.8% in the biggest market rally in months.",
     "NORTH AMERICA", "AP, REUTERS, CNBC", "chip", -122.0, 37.4),
    (2, "KYIV REGION STRIKE TOLL RISES TO 14",
     "A Russian strike flattens an apartment block in Dymer, north of Kyiv. "
     "Rescuers pull a boy out alive after 14 hours under the rubble, and an "
     "elderly woman after 22 hours.",
     "EUROPE", "AP", "blast", 30.3, 50.8),
    (3, "GOMEZ TO QUIT CONGRESS AFTER ETHICS FINDING",
     "Rep. Jimmy Gomez of California will resign on Dec. 1 after the House "
     "Ethics Committee finds evidence of sexual misconduct toward a staffer.",
     "NORTH AMERICA", "AP", "capitol", -77.0, 38.9),
    (4, "STATES SUE MUSK FIRMS OVER GROK IMAGES",
     "Oregon and Virginia sue Musk's companies, saying the Grok chatbot made "
     "sexualized images of real people. The states call it a flood of abuse.",
     "NORTH AMERICA", "AP, CBS", "phone", -122.7, 44.0),
    (5, "TRUMP FLOATS 10% CAP ON CREDIT-CARD RATES",
     "President Trump says he will work with Democrats to cap credit-card "
     "interest at 10%, a populist pitch days before Thanksgiving.",
     "NORTH AMERICA", "AP", "card", -77.0, 38.9),
    (6, "IRAN VOWS TO DEFY US BLOCKADE; HORMUZ STALLS",
     "Iran says it will use all means against the US naval blockade. "
     "Trump says strikes could resume after the new year if no deal "
     "is reached.",
     "MIDDLE EAST", "REUTERS, CBS", "ship", 56.2, 26.5),
    (7, "GERMAN PRESIDENT OPENS AFRICA BUSINESS SUMMIT",
     "Frank-Walter Steinmeier meets Ghana's President Mahama in Accra and "
     "opens the German-African Business Summit on a five-day Africa tour.",
     "AFRICA", "GERMAN PRESIDENCY", "flag", -0.2, 5.6),
    (8, "GAZA'S AIR, SOIL AND WATER POISONED FOR DECADES",
     "A report by Oxfam and CEOBS finds Israel's bombardment left toxic "
     "contamination across almost all of Gaza, a danger for generations.",
     "MIDDLE EAST", "OXFAM, CEOBS", "leaf", 34.5, 31.5),
    (9, "DRONES HIT HOMES AND UN BUILDING IN KHARTOUM",
     "Drone strikes hit homes and a UN building in Sudan's capital as the "
     "war grinds on, the latest attacks on civilians in the city.",
     "AFRICA", "AP", "drone", 32.5, 15.6),
    (10, "6.7 QUAKE HITS PERU; NO DEATHS REPORTED",
     "A magnitude 6.7 earthquake shakes Peru. Officials report no deaths, "
     "and no tsunami warning follows the tremor.",
     "SOUTH AMERICA", "AP", "quake", -75.0, -10.0),
    (11, "THOUSANDS MARCH IN LISBON OVER LIVING COSTS",
     "Thousands take to the streets of Lisbon to protest rising living "
     "costs, part of a wave of cost-of-living anger across Europe.",
     "EUROPE", "AP", "crowd", -9.1, 38.7),
    (12, "MODI OPENS AI CENTRE AT IIT PATNA",
     "Prime Minister Narendra Modi opens an artificial intelligence centre "
     "at IIT Patna and launches a 400-crore-rupee research park.",
     "ASIA", "PTI", "ai", 85.1, 25.6),
    (13, "PENTAGON TO CURB US-CANADA DEFENCE TIES",
     "The Pentagon moves to restrict US-Canada defence cooperation, the "
     "latest strain in the allies' relationship.",
     "NORTH AMERICA", "AP", "shield", -75.7, 45.4),
    (14, "FIGHTING TRAPS EBOLA TEAMS IN DR CONGO",
     "Heavy fighting near a hospital in Ituri traps Ebola responders, the "
     "WHO says, as its chief pleads for peace in the outbreak zone.",
     "AFRICA", "WHO", "germ", 30.2, 1.6),
]

ALSO = [
    (15, "TRUMP ORDERS CONTRACTORS TO CLEAR CONGRESS REPLIES WITH WHITE HOUSE"),
    (16, "TAIWAN WARNS CANADA'S CARNEY OVER DEEPER CHINA TIES"),
    (17, "ROHINGYAS HAIL GENOCIDE VERDICT AGAINST MYANMAR"),
    (18, "KIM VISITS FACTORIES AFTER \"TRUMP SNUB\"; WSJ SAYS OUTREACH IGNORED"),
    (19, "CONCORDIA SURVIVORS ANGRY AT CAPTAIN'S EARLY RELEASE"),
    (20, "MYANMAR GOVERNMENT CALLS ASEAN DECISION UNFAIR"),
    (21, "NIGERIA'S TINUBU ADMITS VILLA HIT BY POWER AND WATER CUTS"),
    (22, "STORMS AND AIRLINE GLITCHES THREATEN MESSY THANKSGIVING TRAVEL"),
    (23, "KING TIDES AND STORM SURGE THREATEN BAY AREA FLOODING"),
    (24, "MODI AND NEPAL'S SHAH FLAG OFF SARYU-KAMALA EXPRESS"),
    (25, "INDIA AND CHINA HOLD MILITARY TALKS IN ARUNACHAL"),
    (26, "PILOTS URGE ACTION AS SPICEJET CRISIS DEEPENS"),
    (27, "FERRARI UNVEILS TWO NEW 296 MODELS IN SPAIN"),
    (28, "INDIA V NEW ZEALAND FIRST TEST ENDS IN A DRAW AT WELLINGTON"),
    (29, "GUKESH DEFENDS WORLD CHESS CROWN AGAINST SINDAROV IN GENEVA"),
    (30, "CROWDSTRIKE BUYS ZSCALER IN $44 BILLION CYBER DEAL"),
    (31, "MARKETS ROAR BACK: S&P +4.8%, NASDAQ +6.5%, NIKKEI -5.1%"),
    (32, "PHILIPPINES: P241-BILLION AID BUDGET QUESTIONED IN SENATE"),
    (33, "MANILA OMBUDSMAN BACKS PLUNDER CASE AGAINST MARCOLETA"),
    (34, "PHILIPPINE POLICE BRACE FOR VP SARA IMPEACHMENT TRIAL"),
    (35, "MADLANGA COMMISSION HEARS WITNESS C IN SOUTH AFRICA"),
    (36, "ANC TO FINALISE COALITION CALLS AFTER NEC MEETING"),
    (37, "GAMBIA INTERCEPTS 491 WOULD-BE MIGRANTS"),
    (38, "LIBYA'S NATIONAL FINE ARTS EXHIBITION OPENS IN TRIPOLI"),
    (39, "GHANA BEAT MOROCCO 1-0 TO WIN AMPUTEE FOOTBALL WORLD CUP"),
    (40, "ONE MILLION CHILDREN IN AFGHANISTAN FACE DEADLY MALNUTRITION"),
    (41, "THOUSANDS PROTEST CLOSURE OF TURKEY MEDIA OUTLETS"),
    (42, "MACRON EYES CONSTITUTIONAL CHANGE TO CURB SPENDING"),
    (43, "LEGO PICKS PORTUGAL FOR ITS 8TH FACTORY"),
    (44, "TRUMP POSTS HUANG MEME AND CLAIMS ROLE IN COMEBACK"),
    (45, "GREEN-CARD ROUTE PROPOSED FOR LONG-TERM IMMIGRANTS"),
]

TIMELINE = [
    ("OVERNIGHT", "RUSSIAN STRIKES HIT KYIV; TOLL NOW 14"),
    ("MORNING", "STEINMEIER IN ACCRA; OPENS SUMMIT"),
    ("MIDDAY", "NVIDIA: HUANG RETURNS; SHARES +33%"),
    ("AFTERNOON", "STATES SUE MUSK; GOMEZ RESIGNS"),
    ("EVENING", "TRUMP: 10% CARD CAP; STORM TRAVEL"),
]

DATE_CHECK = [
    "COP31 ENDED SUNDAY WITHOUT A DEAL - NOT TUESDAY'S NEWS",
    "RUSSIAN CORVETTE SUNK OFF LIBYA ON SUNDAY; CLAIMED MONDAY",
    "INDONESIA FACTORY FIRE: BLAZE SATURDAY, 24 DEAD CONFIRMED MONDAY",
    "BEPICOLOMBO ENTERED MERCURY ORBIT ON SATURDAY",
    "VERSTAPPEN WON THE LAS VEGAS GRAND PRIX ON SATURDAY",
    "ALCARAZ WON THE ATP FINALS ON SUNDAY",
    "HORMUZ TANKER STRIKES WERE 16 AND 21 NOVEMBER, NOT TODAY",
    "HUANG STEPPED DOWN ON 12 NOVEMBER; ONLY HIS RETURN IS TODAY",
    "DEMOCRATS' 258 HOUSE SEATS WERE CLINCHED ON MONDAY",
]

SOURCES = ("AP, REUTERS, AFP, BBC, AL JAZEERA, CBS, CNBC, WHO, UN NEWS, "
           "PTI, SCMP, XINHUA, THE HINDU")

# ------------------------------------------------------- simplified world map
# Rough continent outlines in (lon, lat); drawn flat, labelled, with pins.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-80, 73), (-65, 62), (-55, 52), (-60, 47), (-70, 42), (-75, 35),
     (-80, 32), (-85, 29), (-90, 21), (-97, 16), (-94, 17), (-103, 19),
     (-110, 23), (-117, 33), (-125, 40), (-124, 48), (-135, 58),
     (-155, 58), (-165, 60)],
    [(-58, 64), (-45, 60), (-30, 68), (-25, 70), (-40, 76), (-58, 74)],
    [(-79, 9), (-72, 11), (-62, 10), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-39, -15), (-40, -22), (-48, -27), (-57, -38),
     (-65, -41), (-70, -50), (-74, -53), (-73, -44), (-72, -30),
     (-70, -20), (-77, -12), (-81, -5), (-80, 1)],
    [(-10, 36), (-9, 43), (-2, 48), (-1, 51), (3, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (32, 70), (40, 68),
     (44, 66), (40, 60), (35, 55), (30, 50), (28, 46), (23, 40), (19, 42),
     (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37), (-9, 37)],
    [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (32, 31), (35, 28),
     (37, 22), (40, 15), (43, 12), (48, 11), (51, 12), (46, 5), (41, -2),
     (40, -10), (36, -18), (33, -26), (28, -33), (20, -35), (17, -29),
     (14, -22), (12, -17), (13, -10), (9, 4), (4, 6), (-8, 5), (-13, 8),
     (-17, 15), (-17, 21), (-16, 25), (-10, 31)],
    [(30, 70), (40, 72), (55, 73), (70, 73), (90, 75), (110, 76),
     (130, 72), (150, 70), (170, 67), (178, 65), (170, 60), (162, 58),
     (158, 52), (150, 59), (142, 55), (140, 45), (135, 43), (130, 38),
     (127, 35), (122, 30), (120, 25), (110, 20), (108, 12), (105, 9),
     (100, 8), (98, 12), (94, 16), (90, 22), (85, 20), (80, 13), (77, 8),
     (73, 20), (66, 25), (60, 25), (56, 26), (52, 28), (50, 30), (48, 30),
     (44, 29), (40, 32), (36, 36), (33, 38), (30, 42), (28, 46), (30, 50),
     (32, 55), (30, 60), (30, 65)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32),
     (137, -35), (140, -38), (145, -38), (150, -37), (153, -32),
     (153, -27), (146, -19), (142, -15), (142, -11), (137, -12),
     (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20)],
    [(-4, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53), (1, 51)],
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 38), (141, 42),
     (143, 44), (141, 45), (139, 41), (137, 37), (133, 35), (130, 33)],
    [(32, -26), (33, -19), (35, -16), (34, -22), (32, -26)],
]
MAP_LABELS = [("NORTH AMERICA", -125, 52), ("SOUTH AMERICA", -60, -18),
              ("EUROPE", 15, 55), ("AFRICA", 18, 8), ("ASIA", 95, 52),
              ("OCEANIA", 138, -28)]

# --------------------------------------------------------------------- layout
W, H = 1600, 2300
MX, MW = 60, 1480          # content margins
PIN_JITTER = {4: (-24, 26), 5: (30, 16), 13: (-26, -24)}

def map_xy(lon, lat, mx0, my0, mw, mh):
    return (mx0 + (lon + 170.0) / 360.0 * mw,
            my0 + (75.0 - lat) / 130.0 * mh)

def draw_lead(cv, x, y, w, h, st):
    num, head, summ, region, src, icon, lon, lat = st
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, 4, REGION_COLORS[region])
    ICONS[icon](cv, x + 14, y + 16, 190, 190)
    cv.rect(x + 14, y + 16, 34, 26, RED)
    draw_text(cv, x + 20, y + 21, str(num), 2, WHITE)
    tx = x + 220
    tw = w - 236
    hy = y + 16
    for ln in wrap_text(head, tw, 3):
        draw_text(cv, tx, hy, ln, 3, INK)
        hy += 26
    sy = hy + 6
    sy = draw_para(cv, tx, sy, summ, tw, 2, INK, 18)
    draw_text(cv, x + 14, y + h - 30,
              region + "  |  " + src, 2, REGION_COLORS[region])

def draw_feature(cv, x, y, w, h, st):
    num, head, summ, region, src, icon, lon, lat = st
    tmp = Canvas(190, 190)
    ICONS[icon](tmp, 0, 0, 190, 190)
    blit_scaled(cv, tmp, x, y + 6, 84, 84)
    cv.rect(x, y + 6, 28, 22, RED)
    draw_text(cv, x + 5, y + 10, str(num), 2, WHITE)
    tx = x + 98
    tw = w - 98
    hy = y + 6
    for ln in wrap_text(head, tw, 2)[:2]:
        draw_text(cv, tx, hy, ln, 2, INK)
        hy += 17
    sy = draw_para(cv, tx, hy + 1, summ, tw, 2, GREY, 16)
    draw_text(cv, tx, y + h - 18, region + "  |  " + src, 2,
              REGION_COLORS[region])

def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, (214, 230, 238))
    for poly in CONTINENTS:
        pts = [(x + (lon + 170.0) / 360.0 * w,
                y + (75.0 - lat) / 130.0 * h) for lon, lat in poly]
        cv.poly([(int(px), int(py)) for px, py in pts], (206, 198, 168))
    for name, lon, lat in MAP_LABELS:
        px, py = map_xy(lon, lat, x, y, w, h)
        draw_text(cv, int(px) - text_w(name, 2) // 2, int(py), name, 2, GREY)
    for st in FEATURED:
        num, head, summ, region, src, icon, lon, lat = st
        px, py = map_xy(lon, lat, x, y, w, h)
        jx, jy = PIN_JITTER.get(num, (0, 0))
        qx, qy = int(px) + jx, int(py) + jy
        if (jx, jy) != (0, 0):
            cv.line(int(px), int(py), qx, qy, INK, 2)
        cv.circle(qx, qy, 13, RED)
        cv.ring(qx, qy, 13, WHITE, 2)
        s = str(num)
        draw_text(cv, qx - text_w(s, 2) // 2, qy - 7, s, 2, WHITE)

def build():
    cv = Canvas(W, H)
    # top bar
    draw_text(cv, MX, 12, "THE WORLD IN ONE PAGE", 2, INK)
    draw_text(cv, W - MX - text_w("TUESDAY EDITION", 2), 12,
              "TUESDAY EDITION", 2, INK)
    cv.hline(MX, 34, MW, INK, 3)
    # masthead
    draw_text_centered(cv, W // 2, 52, "TUESDAY 24 NOVEMBER 2026", 8, INK)
    cv.hline(MX, 128, MW, RED, 5)
    draw_text_centered(cv, W // 2, 146,
                       "45 STORIES - 7 REGIONS - EVERY ONE FROM THIS TUESDAY",
                       3, RED)
    draw_text_centered(cv, W // 2, 182,
                       "THE DAY'S WORLD NEWS, DRAWN - NO PHOTOGRAPHS",
                       2, GREY)
    y = 214
    # lead stories
    draw_lead(cv, MX, y, 730, 250, FEATURED[0])
    draw_lead(cv, MX + 750, y, 730, 250, FEATURED[1])
    y += 264
    # featured grid: 12 stories, 2 columns x 6 rows
    for i, st in enumerate(FEATURED[2:]):
        col, row = i % 2, i // 2
        fx = MX + col * 750
        fy = y + row * 106
        draw_feature(cv, fx, fy, 730, 100, st)
        if row < 5:
            cv.hline(MX, fy + 100, MW, LIGHT, 2)
    y += 6 * 106 + 8
    # timeline
    cv.rect(MX, y, MW, 4, INK)
    draw_text(cv, MX, y + 12, "THE DAY IN UTC", 2, RED)
    slot_w = MW // 5
    ty = y + 38
    for i, (when, what) in enumerate(TIMELINE):
        sx = MX + i * slot_w
        draw_text(cv, sx, ty, when, 2, RED)
        draw_para(cv, sx, ty + 18, what, slot_w - 16, 2, INK, 16)
        if i:
            cv.vline(sx - 8, ty, 52, LIGHT, 2)
    y += 100
    # map
    draw_text(cv, MX, y, "WHERE IT HAPPENED - 14 FEATURED STORIES", 3, INK)
    draw_map(cv, MX, y + 34, MW, 340)
    y += 34 + 340 + 18
    # also list
    draw_text(cv, MX, y, "ALSO ON TUESDAY 24 NOVEMBER", 3, INK)
    y += 34
    col_y = [y, y]
    halves = [ALSO[:16], ALSO[16:]]
    for ci, items in enumerate(halves):
        cx = MX + ci * 750
        cy = col_y[ci]
        for num, txt in items:
            line = str(num) + ". " + txt
            for ln in wrap_text(line, 730, 2):
                draw_text(cv, cx, cy, ln, 2, INK)
                cy += 16
        col_y[ci] = cy
    y = max(col_y) + 12
    # date check
    cv.rect(MX, y, MW, 4, RED)
    draw_text(cv, MX, y + 12, "DATE CHECK - LEFT OUT ON PURPOSE", 2, RED)
    dy = y + 36
    for item in DATE_CHECK:
        draw_text(cv, MX + 16, dy, "- " + item, 2, INK)
        dy += 16
    y = dy + 14
    # footer
    cv.hline(MX, y, MW, INK, 3)
    draw_text_centered(
        cv, W // 2, y + 12,
        "EVERY STORY HERE HAPPENED OR WAS FIRST REPORTED ON TUESDAY 24 NOVEMBER 2026.",
        2, INK)
    draw_para(cv, MX, y + 34, "SOURCES: " + SOURCES, MW, 2, GREY, 16)
    draw_text_centered(cv, W // 2, y + 58,
                       "ORIGINAL DRAWINGS - NO PHOTOGRAPHS", 2, GREY)
    return cv

def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out, exist_ok=True)
    cv = build()
    cv.save(os.path.join(out, "entry.png"))
    print("wrote", os.path.join(out, "entry.png"), cv.w, "x", cv.h)

if __name__ == "__main__":
    main()
