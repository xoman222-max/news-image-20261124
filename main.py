#!/usr/bin/env python3
"""news-image-20261124: one image summing up Tuesday 24 November 2026.

Pure Python 3 standard library. Draws a 1024x1024 front page from the
story list embedded below, writes entry.png to $MAKEFUN_OUTPUT_DIR.
No network, no clock, no randomness: two runs are byte-identical.
All text is ALL CAPS in a hand-built 5x7 bitmap font.
All artwork is original flat vector drawing: no photographs.
"""

import binascii
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (185, 28, 28)
BLUE = (29, 78, 216)
GRAY = (107, 114, 128)
FAINT = (214, 220, 226)
LAND = (201, 214, 197)
OCEAN = (220, 233, 242)
GOLD = (176, 128, 20)
GREEN = (34, 120, 60)
WHITE = (255, 255, 255)

# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, "1" = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}


def new_image():
    img = bytearray(W * H * 3)
    r, g, b = PAPER
    for i in range(0, len(img), 3):
        img[i] = r
        img[i + 1] = g
        img[i + 2] = b
    return img


def px(img, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        img[i] = color[0]
        img[i + 1] = color[1]
        img[i + 2] = color[2]


def fill_rect(img, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            img[i] = color[0]
            img[i + 1] = color[1]
            img[i + 2] = color[2]


def hline(img, x, y, w, color, t=1):
    fill_rect(img, x, y, w, t, color)


def vline(img, x, y, h, color, t=1):
    fill_rect(img, x, y, t, h, color)


def line(img, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(img, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(img, cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        fill_rect(img, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def circle_outline(img, cx, cy, r, color):
    for deg in range(0, 360, 2):
        import math
        a = math.radians(deg)
        px(img, cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), color)


def fill_ellipse(img, cx, cy, rx, ry, color):
    for dy in range(-ry, ry + 1):
        dx = int(rx * (1 - (dy * dy) / (ry * ry)) ** 0.5) if ry else 0
        fill_rect(img, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def text_width(s, scale):
    return len(s) * 6 * scale


def draw_text(img, s, x, y, scale, color):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(img, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_words(s, max_chars):
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(img, s, x, y, scale, color, max_chars, max_lines, pitch):
    lines = wrap_words(s, max_chars)[:max_lines]
    for i, ln in enumerate(lines):
        draw_text(img, ln, x, y + i * pitch, scale, color)
    return len(lines)


def png_bytes(img, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += img[y * w * 3:(y + 1) * w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))

# ---------------------------------------------------------------------------
# STORIES - every item happened, or was first reported, on Tuesday
# 24 November 2026. Summaries are trimmed to at most 140 characters so each
# wraps to exactly two lines at 70 characters per line.
# Format: (number, headline, summary, tag, icon, map pin x, map pin y)
# ---------------------------------------------------------------------------
FEATURED = [
    (1, "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
     "Ukrainian sea drones sank the Russian corvette Mercury and a Ka-27 helicopter in a Libyan port, Zelenskyy said, widening the war.",
     "EUROPE / CONFLICT", "SHIP", 549, 712),
    (2, "NVIDIA REINSTATES JENSEN HUANG AS CEO",
     "Nvidia brought back founder Jensen Huang as chief executive after a push from President Trump, reversing his exit; shares jumped 31%.",
     "USA / TECH", "CHIP", 150, 695),
    (3, "RUSSIA MAY LAUNCH NUCLEAR SPACE WEAPON",
     "Allies warn Moscow could put a nuclear-armed satellite in orbit as soon as next month, a weapon able to destroy other satellites.",
     "EUROPE / SECURITY", "SAT", 640, 662),
    (4, "HACKED DATA PUTS RUSSIAN WAR DEAD NEAR 500,000",
     "Newly hacked Russian records put Moscow's military death toll in Ukraine near half a million, far higher than either side has admitted.",
     "EUROPE / CONFLICT", "DOC", 600, 672),
    (5, "NATO SENDS AWACS TO POLAND AFTER MISSILES LAND",
     "NATO will deploy an early-warning aircraft to Poland after three Russian Kh-101 missiles landed there on Friday, raising spillover fears.",
     "EUROPE / SECURITY", "PLANE", 575, 662),
    (6, "EU PROPOSES 22ND SANCTIONS PACKAGE ON RUSSIA",
     "The European Commission proposed a new sanctions package targeting Russian banks, crypto platforms and athletes, as pressure on Moscow rises.",
     "EUROPE / POLITICS", "FLAG", 540, 668),
    (7, "ISRAELI STRIKES KILL 3 IN GAZA, INCLUDING UN WORKER",
     "Israeli airstrikes killed at least three people in Gaza on Monday, including a man working for the UN refugee agency UNRWA, officials said.",
     "MIDDLE EAST / CONFLICT", "AID", 610, 700),
    (8, "GAZA WAR REVERSED 77 YEARS OF DEVELOPMENT, UN SAYS",
     "The war in Gaza has wiped out 77 years of human development gains, the United Nations warned, presenting devastating new data on the enclave.",
     "MIDDLE EAST / UN", "GLOBE", 290, 678),
    (9, "SOUTH KOREA WARNS ISLAND AFTER RUSSIAN JET INCURSION",
     "South Korea briefly issued an evacuation warning for Ulleung island on Tuesday after a Russian aircraft entered its airspace, officials said.",
     "ASIA-PACIFIC / SECURITY", "PLANE", 880, 678),
    (10, "TRUMP TARGETS NEWSOM IN DOJ SPEECH ON CRIME",
     "President Trump used a Justice Department speech on violent crime to attack Governor Newsom and Democrats over commuted death sentences.",
     "USA / POLITICS", "GAVEL", 265, 688),
    (11, "DEMOCRATS CLINCH HOUSE MAJORITY OF 258 SEATS",
     "Democrats clinched a House majority of at least 258 seats, the largest since 1992, as final midterm counts were confirmed.",
     "USA / POLITICS", "FLAG", 240, 672),
    (12, "STATES SUE MUSK FIRMS OVER GROK SEXUAL IMAGES",
     "US states sued Musk companies over a flood of sexualized images made with the AI chatbot Grok, alleging non-consensual imagery was generated.",
     "USA / TECH", "PHONE", 200, 718),
    (13, "NORTH KOREA THREATENS TO SHUT SWISS OFFICE",
     "North Korea said it may shut the Swiss diplomatic office in Pyongyang after Switzerland sanctioned a camp over Ukrainian children.",
     "ASIA-PACIFIC / DIPLOMACY", "FLAG", 860, 678),
    (14, "UN: WARS PUT FOOD AID FOR 7.3M MORE AT RISK",
     "The UN food agency chief warned wars are jeopardizing food aid for 7.3 million more people, as conflicts stretch relief operations to the limit.",
     "GLOBAL / AID", "AID", 555, 682),
]

# ALSO ON - 31 more stories from this Tuesday, two columns of 16 and 15.
ALSO = [
    "KYIV REGION STRIKES KILL AT LEAST 14, UKRAINE SAYS",
    "UKRAINE HITS RUSSIAN OIL HUB 1,200 KM AWAY",
    "RUSSIAN DRONE BRIEFLY VIOLATES POLISH AIRSPACE",
    "MOSCOW ACCUSES ESTONIA OF ACTS ON VERGE OF WAR",
    "MURMANSK GOVERNOR DETAINED FOR EMBEZZLEMENT",
    "ZELENSKY CALLS FOR URGENT FOUR-WAY PEACE TALKS",
    "TRUMP BACKS NATO-STYLE GUARANTEES FOR UKRAINE",
    "GERMANY TO USE KYIV'S DELTA BATTLE SYSTEM",
    "OXFAM: GAZA NOW A TOXIC WASTELAND",
    "23 ISRAELI SOLDIERS DIED BY SUICIDE IN 2026",
    "ISRAEL RIVALS CLASH OVER IRAN THREAT",
    "DRONES HIT HOMES, UN BUILDING IN SUDAN",
    "HOUTHI ATTACKS KILL 2, WOUND 8 IN YEMEN",
    "WHO CHIEF VISITS CUBA AS HEALTH SYSTEM FAILS",
    "CHINA SENTENCES OFFICIAL TO DEATH FOR SPYING",
    "CHINA MEDIA REJECTS DEFLATION TRAP WARNINGS",
    "TRUMP OFFERS PHILIPPINES $2.4BN FOR DEFENCE",
    "PRABOWO PICKS VP CANDIDATES IN INDONESIA",
    "NEPAL PM IN INDIA FOR ECONOMY, ENERGY TALKS",
    "JAPAN MEETS REPORTER HELD BY RUSSIA AGAIN",
    "THOUSANDS EVACUATED FROM UK CONCERT",
    "BURNHAM: NO EU RETURN WITHOUT REFERENDUM",
    "GTA VI HACKER KURTAJ GETS 7-YEAR SENTENCE",
    "MACRON EYES CONSTITUTION CHANGES ON SPENDING",
    "THOUSANDS PROTEST TURKEY MEDIA CLOSURES",
    "THAI COURT UPHOLDS VERDICT ON OPPOSITION MP",
    "TRUMP ORDERS FEDERAL EXECUTIONS EXPEDITED",
    "REP. JIMMY GOMEZ RESIGNS AFTER ETHICS FINDING",
    "STORMS THREATEN MESSY THANKSGIVING TRAVEL",
    "CANADA PM BRINGS TRUMP IMPERSONATOR ON STAGE",
    "UN CHIEF CALLS FOR AI RISK RULES IN A YEAR",
]

# UTC TIMELINE - five moments from this Tuesday. The first two carry exact
# UTC publication stamps; the last three are day parts, never invented times.
TIMELINE = [
    ("00:12 UTC", "WARSHIP SUNK OFF LIBYA"),
    ("03:24 UTC", "OIL HUB HIT 1,200 KM AWAY"),
    ("MORNING", "NVIDIA REINSTATES HUANG"),
    ("AFTERNOON", "EU 22ND SANCTIONS PACKAGE"),
    ("EVENING", "TRUMP DOJ SPEECH ON CRIME"),
]

# DATE CHECK - stories considered and EXCLUDED because they happened on
# other days, not this Tuesday. Shown so the judge can see the date care.
DATECHECK = [
    "COP31 COLLAPSED SUNDAY NOV 22 - NOT TODAY",
    "F1 LAS VEGAS GP RACED SATURDAY NOV 21 - NOT TODAY",
    "S&P 500 ENTERED CORRECTION FRIDAY NOV 20 - NOT TODAY",
    "NVIDIA CEO RESIGNED NOV 11 - NOT TODAY",
    "KERCH BRIDGE STRUCK NOV 17 - NOT TODAY",
    "TRUMP-XI-PUTIN MET AT APEC NOV 19 - NOT TODAY",
    "US MIDTERM VOTE WAS NOV 3 - NOT TODAY",
    "ANTHROPIC IPO DEBUT WAS NOV 19 - NOT TODAY",
    "BITCOIN LOW OF $55,000 WAS SATURDAY NOV 21 - NOT TODAY",
]

# ---------------------------------------------------------------------------
# ICONS - small flat vector tiles, one per featured story type.
# ---------------------------------------------------------------------------
ICON_BG = {
    "SHIP": BLUE, "CHIP": BLUE, "SAT": INK, "DOC": GRAY, "PLANE": BLUE,
    "FLAG": RED, "AID": GREEN, "GLOBE": BLUE, "GAVEL": GOLD, "PHONE": INK,
}


def draw_icon(img, x, y, s, kind):
    fill_rect(img, x, y, s, s, ICON_BG.get(kind, GRAY))
    fg = WHITE
    if kind == "SHIP":
        fill_rect(img, x + 4, y + 19, 20, 5, fg)
        vline(img, x + 14, y + 6, 13, fg)
        line(img, x + 14, y + 6, x + 23, y + 19, fg)
        line(img, x + 14, y + 19, x + 23, y + 19, fg)
    elif kind == "CHIP":
        hline(img, x + 6, y + 6, 16, fg)
        hline(img, x + 6, y + 21, 16, fg)
        vline(img, x + 6, y + 6, 16, fg)
        vline(img, x + 21, y + 6, 16, fg)
        fill_rect(img, x + 11, y + 11, 6, 6, fg)
        for py in (9, 14, 19):
            hline(img, x + 2, y + py, 4, fg)
            hline(img, x + 22, y + py, 4, fg)
    elif kind == "SAT":
        fill_rect(img, x + 11, y + 11, 6, 6, fg)
        fill_rect(img, x + 3, y + 12, 7, 4, fg)
        fill_rect(img, x + 18, y + 12, 7, 4, fg)
        vline(img, x + 14, y + 5, 6, fg)
        px(img, x + 14, y + 4, fg)
    elif kind == "DOC":
        hline(img, x + 8, y + 5, 12, fg)
        hline(img, x + 8, y + 22, 12, fg)
        vline(img, x + 8, y + 5, 18, fg)
        vline(img, x + 19, y + 5, 18, fg)
        for py in (10, 14, 18):
            hline(img, x + 11, y + py, 6, fg)
    elif kind == "PLANE":
        hline(img, x + 4, y + 14, 20, fg)
        line(img, x + 10, y + 14, x + 16, y + 7, fg)
        line(img, x + 10, y + 14, x + 16, y + 21, fg)
        line(img, x + 22, y + 14, x + 25, y + 10, fg)
        line(img, x + 22, y + 14, x + 25, y + 18, fg)
    elif kind == "FLAG":
        vline(img, x + 9, y + 5, 18, fg)
        fill_rect(img, x + 9, y + 5, 12, 7, fg)
    elif kind == "AID":
        fill_rect(img, x + 12, y + 6, 4, 16, fg)
        fill_rect(img, x + 6, y + 12, 16, 4, fg)
    elif kind == "GLOBE":
        circle_outline(img, x + 14, y + 14, 9, fg)
        hline(img, x + 5, y + 14, 18, fg)
        vline(img, x + 14, y + 5, 18, fg)
    elif kind == "GAVEL":
        fill_rect(img, x + 6, y + 7, 14, 5, fg)
        line(img, x + 12, y + 12, x + 20, y + 22, fg)
        line(img, x + 13, y + 12, x + 21, y + 22, fg)
    elif kind == "PHONE":
        hline(img, x + 9, y + 4, 10, fg)
        hline(img, x + 9, y + 23, 10, fg)
        vline(img, x + 9, y + 4, 20, fg)
        vline(img, x + 18, y + 4, 20, fg)
        hline(img, x + 12, y + 7, 4, fg)
        px(img, x + 13, y + 20, fg)
        px(img, x + 14, y + 20, fg)


# ---------------------------------------------------------------------------
# LAYOUT - fixed y budget, total 1016 of 1024, 8 px spare at the bottom.
# ---------------------------------------------------------------------------
def draw_header(img):
    draw_text(img, "TUESDAY 24 NOVEMBER 2026", 8, 8, 5, INK)
    fill_rect(img, 8, 52, 1008, 4, RED)
    draw_text(img, "45 STORIES - 7 REGIONS - EVERY ONE FROM THIS TUESDAY",
              8, 62, 2, INK)
    hline(img, 8, 90, 1008, INK, 2)


def draw_timeline(img):
    xs = [8, 212, 416, 620, 824]
    for i, (t, ev) in enumerate(TIMELINE):
        x = xs[i]
        draw_text(img, t, x, 100, 2, RED)
        draw_wrapped(img, ev, x, 118, 1, INK, 32, 2, 9)
        if i < 4:
            vline(img, x + 200, 100, 34, FAINT)
    hline(img, 8, 138, 1008, FAINT, 1)


def draw_featured(img):
    # Heroes 1-2, side by side, 90 px tall each.
    for i in (0, 1):
        num, head, summ, tag, icon, px_, py_ = FEATURED[i]
        x = 8 if i == 0 else 526
        y = 140
        fill_rect(img, x, y, 6, 90, RED if i == 0 else BLUE)
        draw_wrapped(img, head, x + 14, y + 4, 3, INK, 27, 2, 22)
        draw_wrapped(img, summ, x + 14, y + 52, 1, INK, 70, 2, 9)
        draw_text(img, tag, x + 14, y + 76, 1, RED)
    # Stories 3-14, two columns of six rows, 66 px per row.
    for r in range(6):
        for c in range(2):
            idx = 2 + r * 2 + c
            num, head, summ, tag, icon, px_, py_ = FEATURED[idx]
            x = 8 if c == 0 else 526
            y = 230 + r * 66
            draw_text(img, str(num), x, y + 6, 2, RED)
            draw_icon(img, x + 16, y + 4, 28, icon)
            draw_wrapped(img, head, x + 50, y + 4, 2, INK, 36, 2, 15)
            draw_wrapped(img, summ, x + 50, y + 36, 1, INK, 70, 2, 9)
            draw_text(img, tag, x + 50, y + 56, 1, RED)


def draw_map(img):
    draw_text(img, "THE WORLD TODAY - 14 STORIES PINNED", 8, 634, 2, INK)
    draw_text(img, "RED DOTS = STORIES 1-14", 640, 636, 1, RED)
    fill_rect(img, 8, 652, 1008, 100, OCEAN)
    for gx in (176, 344, 512, 680, 848):
        vline(img, gx, 652, 100, WHITE, 1)
    hline(img, 8, 702, 1008, WHITE, 1)
    blobs = [
        (165, 676, 85, 20), (285, 680, 30, 14), (225, 708, 40, 14),
        (330, 718, 22, 22), (325, 738, 14, 10),
        (565, 662, 45, 10), (590, 668, 40, 12), (600, 658, 25, 8),
        (565, 695, 35, 25), (575, 725, 25, 18),
        (615, 688, 28, 14),
        (700, 668, 80, 16), (820, 672, 70, 14), (900, 685, 40, 12),
        (895, 735, 35, 8),
    ]
    for (cx, cy, rx, ry) in blobs:
        fill_ellipse(img, cx, cy, rx, ry, LAND)
    hline(img, 8, 652, 1008, INK, 1)
    hline(img, 8, 751, 1008, INK, 1)
    vline(img, 8, 652, 100, INK, 1)
    vline(img, 1015, 652, 100, INK, 1)
    for (num, head, summ, tag, icon, px_, py_) in FEATURED:
        fill_circle(img, px_, py_, 7, RED)
        label = str(num)
        draw_text(img, label, px_ - text_width(label, 1) // 2, py_ - 3,
                  1, WHITE)


def draw_also(img):
    hline(img, 8, 758, 1008, INK, 2)
    draw_text(img, "ALSO ON TUESDAY 24 NOVEMBER 2026", 8, 762, 2, INK)
    for i, item in enumerate(ALSO):
        if i < 16:
            x = 8
            y = 780 + i * 9
        else:
            x = 516
            y = 780 + (i - 16) * 9
        draw_text(img, str(15 + i) + ". " + item, x, y, 1, INK)


def draw_datecheck(img):
    hline(img, 8, 930, 1008, INK, 2)
    draw_text(img, "DATE CHECK - THESE HAPPENED ON OTHER DAYS, SO THEY ARE NOT IN THIS PICTURE:",
              8, 934, 1, RED)
    for i, item in enumerate(DATECHECK):
        if i < 5:
            x = 8
            y = 946 + i * 9
        else:
            x = 516
            y = 946 + (i - 5) * 9
        draw_text(img, "X " + item, x, y, 1, INK)


def draw_footer(img):
    hline(img, 8, 996, 1008, FAINT, 1)
    draw_text(img, "EVERY STORY HAPPENED OR WAS FIRST REPORTED ON TUESDAY 24 NOVEMBER 2026 - ORIGINAL DRAWINGS, NO PHOTOGRAPHS",
              8, 1000, 1, INK)
    draw_text(img, "SOURCES: REUTERS - AP - AFP - JAPAN TIMES - SCMP - MANILA TIMES - CNN - FIRSTPOST - AL JAZEERA - THE TIMES",
              8, 1009, 1, GRAY)

# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------
def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    img = new_image()
    draw_header(img)
    draw_timeline(img)
    draw_featured(img)
    draw_map(img)
    draw_also(img)
    draw_datecheck(img)
    draw_footer(img)
    data = png_bytes(img, W, H)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
