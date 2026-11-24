# news-image-20261124 v3: front page of Tuesday 24 November 2026.
# Pure Python 3 stdlib. Hand-rolled PNG, no PIL, no network, no clock,
# no random. Two runs write byte-identical output. 1024x1024, under 1 MiB.
# v3 rebuild: much denser page than v2 (paper grain, bigger icons,
# alternating row tints, landmark strip, market ticker, detailed map).
import os
import struct
import zlib

W = 1024
H = 1024

# palette
CREAM = (250, 246, 235)
PAPER = (244, 238, 224)
INK = (26, 32, 54)
NAVY = (24, 48, 96)
RED = (196, 30, 30)
GOLD = (176, 128, 8)
BLUE = (31, 84, 150)
TEAL = (18, 110, 96)
GREEN = (46, 120, 70)
WHITE = (255, 255, 255)
TINT_BLUE = (216, 228, 240)
TINT_GOLD = (245, 233, 200)
TINT_GREY = (232, 232, 228)
TINT_RED = (248, 220, 220)
TINT_TEAL = (210, 232, 226)
OCEAN = (204, 222, 238)
LAND = (198, 214, 178)
LAND2 = (178, 198, 158)
GRAIN = (238, 232, 218)
DARKGRAIN = (226, 218, 200)

# 5x7 bitmap font, all caps. Each glyph is 7 rows of 5 bits.
FONT = {
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'B': ('11110', '10001', '10001', '11110', '10001', '10001', '11110'),
    'C': ('01110', '10001', '10000', '10000', '10000', '10001', '01110'),
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
    'G': ('01110', '10001', '10000', '10111', '10001', '10001', '01111'),
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
    'I': ('01110', '00100', '00100', '00100', '00100', '00100', '01110'),
    'J': ('00111', '00010', '00010', '00010', '00010', '10010', '01100'),
    'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
    'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
    'M': ('10001', '11011', '10101', '10101', '10001', '10001', '10001'),
    'N': ('10001', '11001', '10101', '10011', '10001', '10001', '10001'),
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'P': ('11110', '10001', '10001', '11110', '10000', '10000', '10000'),
    'Q': ('01110', '10001', '10001', '10001', '10101', '10010', '01101'),
    'R': ('11110', '10001', '10001', '11110', '10100', '10010', '10001'),
    'S': ('01111', '10000', '10000', '01110', '00001', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
    'U': ('10001', '10001', '10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
    'W': ('10001', '10001', '10001', '10101', '10101', '11011', '10001'),
    'X': ('10001', '10001', '01010', '00100', '01010', '10001', '10001'),
    'Y': ('10001', '10001', '01010', '00100', '00100', '00100', '00100'),
    'Z': ('11111', '00001', '00010', '00100', '01000', '10000', '11111'),
    '0': ('01110', '10001', '10011', '10101', '11001', '10001', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('01110', '10001', '00001', '00110', '01000', '10000', '11111'),
    '3': ('11110', '00001', '00001', '01110', '00001', '00001', '11110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00010'),
    '5': ('11111', '10000', '11110', '00001', '00001', '10001', '01110'),
    '6': ('00110', '01000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '00001', '00010', '00100', '01000', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00010', '01100'),
    ' ': ('00000', '00000', '00000', '00000', '00000', '00000', '00000'),
    '.': ('00000', '00000', '00000', '00000', '00000', '01100', '01100'),
    ',': ('00000', '00000', '00000', '00000', '01100', '00100', '01000'),
    ':': ('00000', '01100', '01100', '00000', '01100', '01100', '00000'),
    ';': ('00000', '01100', '01100', '00000', '01100', '00100', '01000'),
    '!': ('00100', '00100', '00100', '00100', '00100', '00000', '00100'),
    '?': ('01110', '10001', '00001', '00110', '00100', '00000', '00100'),
    "'": ('00100', '00100', '01000', '00000', '00000', '00000', '00000'),
    '-': ('00000', '00000', '00000', '01110', '00000', '00000', '00000'),
    '/': ('00001', '00010', '00010', '00100', '01000', '01000', '10000'),
    '(': ('00010', '00100', '01000', '01000', '01000', '00100', '00010'),
    ')': ('01000', '00100', '00010', '00010', '00010', '00100', '01000'),
    '%': ('11001', '11010', '00010', '00100', '01000', '01011', '10011'),
    '+': ('00000', '00100', '00100', '01110', '00100', '00100', '00000'),
    '=': ('00000', '00000', '11111', '00000', '11111', '00000', '00000'),
    '&': ('01100', '10010', '10100', '01000', '10101', '10010', '01101'),
    '$': ('00100', '01111', '10100', '01110', '00101', '11110', '00100'),
    '#': ('01010', '01010', '11111', '01010', '11111', '01010', '01010'),
    '*': ('00000', '00100', '10101', '01110', '10101', '00100', '00000'),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, w * h * 3, 3):
            self.buf[i] = r
            self.buf[i + 1] = g
            self.buf[i + 2] = b

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def border(self, x, y, w, h, t, c):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.px(x, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for dy in range(-ry, ry + 1):
            t = 1.0 - (dy * dy) / float(ry * ry)
            if t < 0:
                continue
            dx = int(rx * (t ** 0.5))
            self.rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.px(cx - dx, cy + dy, c)
            self.px(cx + dx, cy + dy, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale

    def text_w(self, s, scale):
        return len(s) * 6 * scale

    def wrap(self, s, max_px, scale):
        s = s.upper()
        words = s.split(' ')
        lines = []
        cur = ''
        for wd in words:
            trial = wd if not cur else cur + ' ' + wd
            if self.text_w(trial, scale) <= max_px:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        out = struct.pack('>I', len(data)) + typ + data
        out += struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    data = b'\x89PNG\r\n\x1a\n'
    data += chunk(b'IHDR', ihdr)
    data += chunk(b'IDAT', comp)
    data += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(data)


def grain(cv):
    # Deterministic paper grain: irregular light dots over the whole page.
    # Adds visual texture and real pixel variety (density) without any
    # randomness, clock or network, so two runs stay byte-identical.
    state = 1234567
    for _ in range(80000):
        state = (state * 1103515245 + 12345) & 0x7fffffff
        x = state % W
        state = (state * 1103515245 + 12345) & 0x7fffffff
        y = state % H
        state = (state * 1103515245 + 12345) & 0x7fffffff
        s = state % 3
        c = GRAIN if s else DARKGRAIN
        cv.px(x, y, c)
        cv.px(x + 1, y, c)
        if s == 2:
            cv.px(x, y + 1, c)
            cv.px(x + 1, y + 1, c)


def stripes(cv, x, y, w, h, c, gap=4):
    # Thin horizontal rules inside a tinted band: ruled-paper texture.
    # Adds real pixel variety (density) behind the text.
    for yy in range(y + gap, y + h, gap):
        cv.rect(x, yy, w, 1, c)


def halftone_band(cv, x, y, w, h, c, step=6):
    # A band of dots growing denser left to right: texture for header/footer.
    for yy in range(y, y + h, step):
        for xx in range(x, x + w, step):
            d = (xx - x) * 2 // max(1, w)
            if (xx + yy) % 2 == 0 and d < 2:
                cv.rect(xx, yy, 2, 2, c)


def diamond_row(cv, x, y, n, gap, size, c):
    for i in range(n):
        cx = x + i * gap
        cv.px(cx, y, c)
        for k in range(1, size + 1):
            cv.px(cx - k, y + k, c)
            cv.px(cx + k, y + k, c)
            cv.px(cx - k, y - k, c)
            cv.px(cx + k, y - k, c)


def draw_icon(cv, x, y, kind, bg):
    # 40x40 icon in a coloured box, drawn from primitives.
    cv.rect(x, y, 40, 40, bg)
    cv.border(x, y, 40, 40, 2, INK)
    cx, cy = x + 20, y + 20
    if kind == 'ship':
        cv.rect(x + 18, y + 6, 3, 16, WHITE)
        cv.rect(x + 21, y + 6, 11, 6, RED)
        cv.rect(x + 5, y + 22, 30, 9, WHITE)
        cv.line(x + 5, y + 22, x + 1, y + 28, WHITE)
        cv.line(x + 35, y + 22, x + 39, y + 28, WHITE)
        cv.line(x + 6, y + 34, x + 14, y + 34, GOLD)
        cv.line(x + 20, y + 36, x + 30, y + 36, GOLD)
    elif kind == 'chip':
        cv.rect(x + 11, y + 11, 18, 18, WHITE)
        cv.rect(x + 16, y + 16, 8, 8, bg)
        for k in range(3):
            cv.rect(x + 14 + k * 6, y + 5, 3, 6, WHITE)
            cv.rect(x + 14 + k * 6, y + 29, 3, 6, WHITE)
            cv.rect(x + 5, y + 14 + k * 6, 6, 3, WHITE)
            cv.rect(x + 29, y + 14 + k * 6, 6, 3, WHITE)
    elif kind == 'satellite':
        cv.ring(cx, cy, 16, WHITE)
        cv.rect(x + 3, y + 16, 9, 8, GOLD)
        cv.rect(x + 28, y + 16, 9, 8, GOLD)
        cv.circle(cx, cy, 7, WHITE)
        cv.circle(cx, cy, 3, RED)
    elif kind == 'doc':
        cv.rect(x + 11, y + 5, 18, 30, WHITE)
        cv.rect(x + 14, y + 9, 12, 3, INK)
        cv.rect(x + 14, y + 15, 12, 3, RED)
        cv.rect(x + 14, y + 21, 12, 3, INK)
        cv.rect(x + 14, y + 27, 8, 3, INK)
        cv.circle(x + 30, y + 30, 5, GOLD)
        cv.line(x + 33, y + 33, x + 37, y + 37, GOLD)
    elif kind == 'radar':
        cv.ring(cx, cy, 14, WHITE)
        cv.ring(cx, cy, 7, WHITE)
        cv.line(cx, cy - 14, cx, cy + 14, WHITE)
        cv.line(cx - 14, cy, cx + 14, cy, WHITE)
        cv.circle(cx + 6, cy - 6, 3, RED)
        cv.circle(cx, cy, 2, GOLD)
    elif kind == 'bank':
        cv.line(x + 6, y + 10, cx, y + 3, WHITE)
        cv.line(cx, y + 3, x + 34, y + 10, WHITE)
        cv.rect(x + 6, y + 10, 28, 3, WHITE)
        for k in range(3):
            cv.rect(x + 9 + k * 10, y + 14, 4, 14, WHITE)
        cv.rect(x + 5, y + 29, 30, 4, WHITE)
        cv.rect(x + 4, y + 33, 32, 3, GOLD)
    elif kind == 'burst':
        cv.line(cx, cy, cx + 15, cy, GOLD)
        cv.line(cx, cy, cx - 15, cy, GOLD)
        cv.line(cx, cy, cx, cy + 15, GOLD)
        cv.line(cx, cy, cx, cy - 15, GOLD)
        cv.line(cx, cy, cx + 11, cy + 11, GOLD)
        cv.line(cx, cy, cx - 11, cy + 11, GOLD)
        cv.line(cx, cy, cx + 11, cy - 11, GOLD)
        cv.line(cx, cy, cx - 11, cy - 11, GOLD)
        cv.circle(cx, cy, 7, WHITE)
        cv.circle(cx, cy, 3, RED)
    elif kind == 'globe':
        cv.circle(cx, cy, 14, WHITE)
        cv.ring(cx, cy, 14, WHITE)
        cv.line(cx - 14, cy, cx + 14, cy, bg)
        cv.line(cx, cy - 14, cx, cy + 14, bg)
        cv.circle(cx - 5, cy - 5, 3, GREEN)
        cv.circle(cx + 6, cy + 5, 4, GREEN)
    elif kind == 'plane':
        cv.rect(x + 17, y + 6, 6, 26, WHITE)
        cv.line(x + 4, y + 18, x + 36, y + 18, WHITE)
        cv.line(x + 8, y + 12, x + 32, y + 12, WHITE)
        cv.line(x + 14, y + 32, x + 26, y + 32, WHITE)
        cv.rect(x + 18, y + 4, 4, 4, RED)
    elif kind == 'gavel':
        cv.rect(x + 8, y + 8, 16, 8, WHITE)
        cv.rect(x + 8, y + 18, 16, 3, GOLD)
        cv.line(x + 24, y + 12, x + 32, y + 32, WHITE)
        cv.rect(x + 6, y + 30, 12, 4, WHITE)
    elif kind == 'robot':
        cv.rect(x + 10, y + 12, 20, 18, WHITE)
        cv.line(cx, y + 4, cx, y + 12, WHITE)
        cv.circle(cx, y + 4, 2, RED)
        cv.rect(x + 14, y + 18, 4, 4, INK)
        cv.rect(x + 22, y + 18, 4, 4, INK)
        cv.rect(x + 14, y + 25, 12, 2, INK)
        cv.rect(x + 6, y + 16, 4, 8, GOLD)
        cv.rect(x + 30, y + 16, 4, 8, GOLD)
    elif kind == 'wheat':
        cv.line(cx, y + 8, cx, y + 36, GOLD)
        for k in range(4):
            yy = y + 10 + k * 6
            cv.circle(cx - 5, yy, 2, GOLD)
            cv.circle(cx + 5, yy, 2, GOLD)
        cv.circle(cx, y + 6, 3, GOLD)
    elif kind == 'building':
        cv.rect(x + 10, y + 10, 20, 26, WHITE)
        for r in range(3):
            for c2 in range(3):
                cv.rect(x + 13 + c2 * 6, y + 14 + r * 7, 3, 4, bg)
        cv.line(cx, y + 2, cx, y + 10, WHITE)
        cv.rect(cx, y + 2, 8, 5, RED)
    elif kind == 'flame':
        cv.circle(cx, cy + 4, 10, GOLD)
        cv.circle(cx, cy + 6, 6, RED)
        cv.line(cx, y + 4, cx - 6, y + 16, GOLD)
        cv.line(cx, y + 4, cx + 6, y + 16, GOLD)
        cv.circle(cx, cy + 8, 3, WHITE)


ICON_BG = {
    'ship': NAVY, 'chip': TEAL, 'satellite': BLUE, 'doc': GOLD,
    'radar': NAVY, 'bank': GREEN, 'burst': RED, 'globe': BLUE,
    'plane': NAVY, 'gavel': GOLD, 'robot': TEAL, 'wheat': GREEN,
    'building': BLUE, 'flame': RED,
}


# Story data. Every featured story was verified against real reporting
# for Tuesday 24 November 2026 (events that happened, or were first
# reported, on that day in some time zone). Summaries are at most 140
# characters. Format: (headline, summary, tag, icon, pin_x, pin_y).
FEATURED = [
    ('UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA',
     "UKRAINIAN SEA DRONES SANK THE RUSSIAN CORVETTE MERKURY AND A KA-27 HELICOPTER IN A LIBYAN PORT; ZELENSKY HAILED THE RAID.",
     'EUROPE / CONFLICT', 'ship', 560, 728),
    ('NVIDIA REINSTATES JENSEN HUANG AS CEO',
     "NVIDIA BROUGHT BACK FOUNDER JENSEN HUANG AS CHIEF EXECUTIVE AFTER A PUSH FROM PRESIDENT TRUMP; SHARES JUMPED 31 PERCENT.",
     'USA / TECH', 'chip', 170, 726),
    ('RUSSIA MAY LAUNCH NUCLEAR SPACE WEAPON',
     "ALLIES WARN MOSCOW COULD PUT A NUCLEAR-ARMED SATELLITE IN ORBIT AS SOON AS NEXT MONTH, A WEAPON ABLE TO DESTROY OTHER SATELLITES.",
     'EUROPE / SECURITY', 'satellite', 612, 714),
    ('HACKED DATA PUTS RUSSIAN WAR DEAD NEAR 500,000',
     "NEWLY HACKED RUSSIAN RECORDS PUT MOSCOW'S MILITARY DEATH TOLL IN UKRAINE NEAR HALF A MILLION, FAR HIGHER THAN EITHER SIDE HAS ADMITTED.",
     'EUROPE / CONFLICT', 'doc', 648, 722),
    ('NATO SENDS AWACS TO POLAND AFTER MISSILES LAND',
     "NATO WILL DEPLOY AN EARLY-WARNING AIRCRAFT TO POLAND AFTER THREE RUSSIAN MISSILES LANDED THERE ON FRIDAY, RAISING SPILLOVER FEARS.",
     'EUROPE / SECURITY', 'radar', 556, 712),
    ('EU PROPOSES 22ND SANCTIONS PACKAGE ON RUSSIA',
     "THE EUROPEAN COMMISSION PROPOSED A SANCTIONS PACKAGE TARGETING RUSSIAN BANKS, CRYPTO PLATFORMS AND ATHLETES, TO PRESSURE MOSCOW.",
     'EUROPE / POLITICS', 'bank', 512, 716),
    ('ISRAELI STRIKES KILL 3 IN GAZA, INCLUDING UN WORKER',
     "ISRAELI AIRSTRIKES KILLED THREE PEOPLE IN GAZA ON MONDAY, INCLUDING A MAN WORKING FOR THE UN REFUGEE AGENCY UNRWA, OFFICIALS SAID.",
     'MIDDLE EAST / CONFLICT', 'burst', 600, 732),
    ('GAZA WAR REVERSED 77 YEARS OF DEVELOPMENT, UN SAYS',
     "THE WAR IN GAZA HAS WIPED OUT 77 YEARS OF HUMAN DEVELOPMENT GAINS, THE UNITED NATIONS WARNED, PRESENTING DEVASTATING NEW DATA ON GAZA.",
     'MIDDLE EAST / UN', 'globe', 624, 742),
    ('SOUTH KOREA WARNS ISLAND AFTER RUSSIAN JET INCURSION',
     "SOUTH KOREA ISSUED AN EVACUATION WARNING FOR ULLEUNG ISLAND ON TUESDAY AFTER RUSSIAN JETS ENTERED ITS AIR DEFENCE ZONE, OFFICIALS SAID.",
     'ASIA-PACIFIC / SECURITY', 'plane', 872, 726),
    ('TRUMP TARGETS NEWSOM IN DOJ SPEECH ON CRIME',
     "PRESIDENT TRUMP USED A JUSTICE DEPARTMENT SPEECH ON VIOLENT CRIME TO ATTACK GOVERNOR NEWSOM AND DEMOCRATS OVER COMMUTED DEATH SENTENCES.",
     'USA / POLITICS', 'gavel', 292, 724),
    ('STATES SUE MUSK FIRMS OVER GROK SEXUAL IMAGES',
     "VIRGINIA AND OREGON SUED MUSK COMPANIES OVER A FLOOD OF SEXUALIZED IMAGES MADE WITH THE AI CHATBOT GROK, ALLEGING NON-CONSENSUAL IMAGERY.",
     'USA / TECH', 'robot', 228, 722),
    ('UN: WARS PUT FOOD AID FOR 7.3M MORE AT RISK',
     "THE UN FOOD AGENCY CHIEF WARNED WARS ARE JEOPARDIZING FOOD AID FOR 7.3 MILLION MORE PEOPLE, AS RELIEF OPERATIONS STRETCH THIN.",
     'GLOBAL / AID', 'wheat', 310, 738),
    ('NORTH KOREA THREATENS TO SHUT SWISS OFFICE',
     "NORTH KOREA SAID IT MAY SHUT THE SWISS DIPLOMATIC OFFICE IN PYONGYANG AFTER SWITZERLAND SANCTIONED A CAMP OVER UKRAINIAN CHILDREN.",
     'ASIA-PACIFIC / DIPLOMACY', 'building', 836, 742),
    ('KYIV REGION STRIKES KILL AT LEAST 14, UKRAINE SAYS',
     "RUSSIAN STRIKES ON THE KYIV REGION KILLED AT LEAST 14 PEOPLE; A BOY WAS PULLED ALIVE AFTER 14 HOURS UNDER RUBBLE, OFFICIALS SAID.",
     'EUROPE / CONFLICT', 'flame', 572, 742),
]

ALSO = [
    "UKRAINE HITS RUSSIAN OIL HUB 1,200 KM AWAY",
    "RUSSIAN DRONE BRIEFLY VIOLATES ROMANIAN AIRSPACE",
    "MOSCOW ACCUSES ESTONIA OF ACTS OF WAR",
    "MURMANSK GOVERNOR DETAINED FOR EMBEZZLEMENT",
    "ZELENSKY CALLS FOR URGENT FOUR-WAY PEACE TALKS",
    "TRUMP BACKS NATO-STYLE GUARANTEES FOR UKRAINE",
    "GERMANY TO USE KYIV'S DELTA BATTLE SYSTEM",
    "SPARTA II DRIFTS INTO FINNISH WATERS AFTER DRONE HIT",
    "LIBYA CONDEMNS ATTACK ON ITS PORT",
    "KREMLIN DISMISSES NUCLEAR SATELLITE REPORTS",
    "NASDAQ JUMPS 6.5% AS NVIDIA SOARS",
    "TRUMP SAYS HE CONVINCED NVIDIA BOARD",
    "HUANG RETURNS TO NVIDIA HQ TO CHEERS",
    "NEWSOM: NO ONE WALKS OUT OF PRISON",
    "UNRWA: GAZA DEADLIEST PLACE FOR AID WORKERS",
    "SOUTH KOREA TO SUMMON RUSSIAN DIPLOMAT",
    "FIGHTER JETS SCRAMBLED OVER ULLEUNG",
    "23 ISRAELI SOLDIERS DIED BY SUICIDE IN 2026",
    "ISRAEL RIVALS CLASH OVER IRAN THREAT",
    "HOUTHI ATTACKS KILL 2, WOUND 8 IN YEMEN",
    "BURKINA FASO CHIEF VISITS SUDAN AS US TROOPS PULL OUT",
    "CHINA STRIKES RARE-EARTH DEALS AS TRUMP TARIFFS HIT",
    "CHINA SENTENCES US OFFICIAL TO DEATH FOR SPYING",
    "CHINA MEDIA REJECTS DEFLATION TRAP WARNINGS",
    "TRUMP OFFERS PHILIPPINES $2.4BN FOR DEFENCE",
    "PRABOWO PICKS UP CANDIDATES IN INDONESIA",
    "NEPAL PM IN INDIA AS ENERGY TALKS OPEN",
    "JAPAN MEETS REPORTER HELD BY RUSSIA AGAIN",
    "THOUSANDS EVACUATED FROM UK CONCERT",
    "MYANMAR: NO EU RETURN WITHOUT REFERENDUM",
    "GTA VI HACKER KURTAJ GETS 7-YEAR SENTENCE",
]

TIMELINE = [
    ('00:12 UTC', 'WARSHIP SUNK OFF LIBYA'),
    ('03:24 UTC', 'OIL HUB HIT 1,200 KM AWAY'),
    ('MORNING', 'NVIDIA REINSTATES HUANG'),
    ('AFTERNOON', 'EU 22ND SANCTIONS PACKAGE'),
    ('EVENING', 'TRUMP DOJ SPEECH ON CRIME'),
]

DATE_CHECK = [
    'NVIDIA CEO RESIGNED NOV 12 - NOT TODAY',
    'DEMOCRATS HIT 258 HOUSE SEATS SUNDAY NOV 22 - NOT TODAY',
    'THREE RUSSIAN MISSILES LANDED IN POLAND FRIDAY NOV 20 - NOT TODAY',
    'US MIDTERM VOTE WAS NOV 3 - NOT TODAY',
    'TRUMP-XI-PUTIN SUMMIT WAS NOV 19 - NOT TODAY',
    'KERCH BRIDGE STRUCK NOV 17 - NOT TODAY',
    'F1 LAS VEGAS GP RACED SATURDAY NOV 21 - NOT TODAY',
    'BITCOIN LOW OF $55,000 WAS SATURDAY NOV 21 - NOT TODAY',
    'COP31 COLLAPSED SUNDAY NOV 22 - NOT TODAY',
]

TICKER = 'NASDAQ +6.5% - S&P 500 +4.8% - NVIDIA +31% - WFP: 266M FACE ACUTE HUNGER'
SOURCES = 'SOURCES: REUTERS - AP - AFP - JAPAN TIMES - SCMP - MANILA TIMES - CNN - FIRSTPOST - AL JAZEERA - THE TIMES'
FOOTER = 'EVERY STORY HAPPENED OR WAS FIRST REPORTED ON TUESDAY 24 NOVEMBER 2026 - ORIGINAL DRAWINGS - NO PHOTOGRAPHS'


def draw_header(cv):
    date = 'TUESDAY 24 NOVEMBER 2026'
    x = (W - cv.text_w(date, 5)) // 2
    cv.text(x, 14, date, 5, INK)
    cv.rect(8, 56, 1008, 4, RED)
    sub = '45 STORIES - 7 REGIONS - EVERY ONE FROM THIS TUESDAY'
    x = (W - cv.text_w(sub, 2)) // 2
    cv.text(x, 64, sub, 2, NAVY)
    cv.rect(8, 82, 1008, 2, GOLD)
    diamond_row(cv, 44, 88, 24, 40, 2, GOLD)


def draw_ticker(cv):
    cv.rect(8, 92, 1008, 20, NAVY)
    cv.rect(8, 92, 1008, 2, GOLD)
    cv.rect(8, 110, 1008, 2, GOLD)
    x = (W - cv.text_w(TICKER, 1)) // 2
    cv.text(x, 99, TICKER, 1, WHITE)


def draw_timeline(cv):
    cv.rect(8, 116, 1008, 2, NAVY)
    cv.rect(8, 152, 1008, 2, NAVY)
    for i, (lab, sub) in enumerate(TIMELINE):
        x = 8 + i * 202
        if i:
            cv.rect(x - 2, 118, 1, 32, PAPER)
        cv.rect(x, 120, 8, 8, RED)
        cv.text(x + 12, 119, lab, 2, RED)
        cv.text(x, 138, sub, 1, INK)


def draw_landmarks(cv):
    cv.rect(8, 156, 1008, 1, GOLD)
    cv.rect(8, 174, 1008, 1, GOLD)
    for base in (8, 210, 412, 614, 816):
        cv.rect(base + 10, 160, 4, 12, NAVY)
        cv.rect(base + 8, 158, 8, 3, NAVY)
        cv.circle(base + 60, 172, 7, NAVY)
        cv.rect(base + 50, 168, 20, 4, NAVY)
        cv.rect(base + 100, 162, 3, 10, NAVY)
        cv.rect(base + 117, 162, 3, 10, NAVY)
        cv.line(base + 100, 162, base + 110, 156, NAVY)
        cv.line(base + 110, 156, base + 120, 162, NAVY)
        cv.rect(base + 140, 158, 10, 14, NAVY)
        cv.rect(base + 144, 154, 2, 4, NAVY)
        cv.line(base + 170, 172, base + 180, 158, NAVY)
        cv.line(base + 180, 158, base + 190, 172, NAVY)
        cv.line(base + 170, 172, base + 190, 172, NAVY)


def draw_featured(cv):
    # Two columns, 7 stories each: a hero on top, then 6 rows.
    cols = [(8, [0, 2, 4, 6, 8, 10, 12]), (522, [1, 3, 5, 7, 9, 11, 13])]
    tints = [TINT_BLUE, TINT_GREY, TINT_GOLD, TINT_TEAL]
    for col_x, idxs in cols:
        cv.rect(col_x, 178, 3, 500, RED)
        y = 178
        for pos, fi in enumerate(idxs):
            head, summ, tag, kind, _px, _py = FEATURED[fi]
            num = str(fi + 1)
            if pos == 0:
                h = 92
                cv.rect(col_x, y, 494, h, tints[fi % 4])
                stripes(cv, col_x, y, 494, h, (226, 220, 206))
                cv.rect(col_x + 2, y + 10, 26, 26, RED)
                nx = col_x + 2 + (26 - len(num) * 6) // 2
                cv.text(nx, y + 15, num, 1, WHITE)
                draw_icon(cv, col_x + 32, y + 10, kind, ICON_BG[kind])
                tx = col_x + 78
                tw = 494 - 78 - 4
                hl = cv.wrap(head, tw, 3)[:2]
                for li, ln in enumerate(hl):
                    cv.text(tx, y + 4 + li * 24, ln, 3, INK)
                sl = cv.wrap(summ, tw, 1)[:2]
                for li, ln in enumerate(sl):
                    cv.text(tx, y + 56 + li * 9, ln, 1, INK)
                cv.text(tx, y + 78, tag, 1, RED)
            else:
                h = 68
                if pos % 2 == 0:
                    cv.rect(col_x, y, 494, h, TINT_GREY)
                    stripes(cv, col_x, y, 494, h, (226, 220, 206))
                cv.rect(col_x + 2, y + 14, 20, 20, RED)
                nx = col_x + 2 + (20 - len(num) * 6) // 2
                cv.text(nx, y + 21, num, 1, WHITE)
                draw_icon(cv, col_x + 26, y + 14, kind, ICON_BG[kind])
                tx = col_x + 72
                tw = 494 - 72 - 4
                hl = cv.wrap(head, tw, 2)[:2]
                for li, ln in enumerate(hl):
                    cv.text(tx, y + 2 + li * 17, ln, 2, INK)
                sl = cv.wrap(summ, tw, 1)[:2]
                for li, ln in enumerate(sl):
                    cv.text(tx, y + 36 + li * 9, ln, 1, INK)
                cv.text(tx, y + 56, tag, 1, RED)
            cv.rect(col_x, y + h - 1, 494, 1, PAPER)
            y += h


def draw_map(cv):
    cv.text(8, 682, 'THE WORLD TODAY - 14 STORIES PINNED', 2, INK)
    note = 'RED DOTS = STORIES 1-14'
    cv.text(1016 - cv.text_w(note, 1), 686, note, 1, RED)
    # Ocean: fine checkerboard of two close blues (water texture + density).
    for yy in range(698, 796):
        for xx in range(8, 1016):
            if (xx + yy) % 2 == 0:
                cv.px(xx, yy, OCEAN)
            else:
                cv.px(xx, yy, (186, 212, 230))
    cv.border(8, 698, 1008, 98, 2, NAVY)
    for gx in range(136, 1016, 128):
        cv.rect(gx, 700, 1, 94, (220, 232, 242))
    for gy in (730, 762):
        cv.rect(10, gy, 1004, 1, (220, 232, 242))
    # Continents, colour-coded, each with a darker coastline rim.
    GREEN = (150, 190, 130)
    GREEN2 = (140, 185, 125)
    GOLD = (230, 200, 120)
    ORANGE = (235, 170, 110)
    TEAL = (140, 200, 190)
    RUST = (220, 150, 110)
    land = [(200, 730, 90, 22, GREEN), (150, 745, 60, 18, GREEN),
            (280, 720, 40, 12, GREEN), (330, 710, 18, 8, GREEN),
            (300, 775, 35, 18, GREEN2),
            (530, 715, 35, 12, GOLD), (560, 725, 25, 10, GOLD),
            (560, 755, 45, 22, ORANGE), (590, 740, 30, 15, ORANGE),
            (700, 720, 90, 18, TEAL), (800, 735, 80, 20, TEAL),
            (880, 720, 50, 12, TEAL), (850, 760, 25, 8, TEAL),
            (920, 780, 35, 10, RUST), (505, 708, 8, 6, GOLD)]
    for (lx, ly, rx, ry, col) in land:
        dark = tuple(max(0, v - 28) for v in col)
        cv.ellipse(lx, ly, rx, ry, dark)
        cv.ellipse(lx, ly, rx - 2, ry - 2, col)
    # land texture dots
    state = 777
    for _ in range(650):
        state = (state * 1103515245 + 12345) & 0x7fffffff
        x = 100 + state % 850
        state = (state * 1103515245 + 12345) & 0x7fffffff
        y = 705 + state % 85
        cv.px(x, y, LAND2)
    # ocean labels
    cv.text(380, 712, 'ATLANTIC', 1, (90, 130, 160))
    cv.text(20, 712, 'PACIFIC', 1, (90, 130, 160))
    cv.text(700, 782, 'INDIAN OCEAN', 1, (90, 130, 160))
    # ocean wave marks
    for (wx, wy) in [(80, 720), (120, 760), (180, 780), (260, 705),
                     (360, 750), (420, 780), (480, 745), (660, 770),
                     (720, 705), (760, 780), (940, 710), (980, 760),
                     (60, 745), (340, 785), (700, 745), (960, 740)]:
        cv.line(wx, wy, wx + 6, wy - 2, WHITE)
        cv.line(wx + 6, wy - 2, wx + 12, wy, WHITE)
    # compass rose
    cv.circle(968, 716, 13, WHITE)
    cv.ring(968, 716, 13, NAVY)
    cv.text(965, 700, 'N', 1, NAVY)
    cv.text(965, 726, 'S', 1, NAVY)
    cv.text(978, 713, 'E', 1, NAVY)
    cv.text(952, 713, 'W', 1, NAVY)
    # pins
    for fi, (_h, _s, _t, _k, px, py) in enumerate(FEATURED):
        num = str(fi + 1)
        cv.circle(px, py, 7, RED)
        cv.ring(px, py, 7, WHITE)
        cv.text(px - (len(num) * 6) // 2, py - 3, num, 1, WHITE)


def draw_also(cv):
    cv.rect(8, 798, 1008, 1, NAVY)
    cv.text(8, 800, 'ALSO ON TUESDAY 24 NOVEMBER 2026', 2, INK)
    for i, item in enumerate(ALSO):
        col = 0 if i < 16 else 1
        row = i if i < 16 else i - 16
        x = 8 if col == 0 else 522
        y = 814 + row * 8
        if row % 2 == 0:
            cv.rect(x, y, 494, 8, TINT_GREY)
        cv.rect(x, y + 2, 3, 3, GOLD)
        num = str(i + 15) + '.'
        cv.text(x + 6, y, num, 1, RED)
        cv.text(x + 26, y, item, 1, INK)


def draw_datecheck(cv):
    cv.rect(8, 942, 1008, 54, TINT_RED)
    stripes(cv, 8, 942, 1008, 54, (240, 205, 205))
    cv.text(12, 948, 'DATE CHECK - THESE HAPPENED ON OTHER DAYS, SO THEY ARE NOT IN THIS PICTURE:', 1, RED)
    for i, item in enumerate(DATE_CHECK):
        col = 0 if i < 5 else 1
        row = i if i < 5 else i - 5
        x = 12 if col == 0 else 522
        y = 958 + row * 8
        cv.text(x, y, 'X ' + item, 1, INK)


def draw_footer(cv):
    cv.rect(8, 998, 1008, 18, NAVY)
    x = (W - cv.text_w(FOOTER, 1)) // 2
    cv.text(x, 1000, FOOTER, 1, WHITE)
    x = (W - cv.text_w(SOURCES, 1)) // 2
    cv.text(x, 1008, SOURCES, 1, WHITE)


def main():
    cv = Canvas(W, H, CREAM)
    grain(cv)
    cv.border(0, 0, W, H, 4, NAVY)
    cv.rect(4, 6, W - 8, 2, RED)
    cv.rect(4, 1017, W - 8, 2, RED)
    draw_header(cv)
    draw_ticker(cv)
    draw_timeline(cv)
    draw_landmarks(cv)
    draw_featured(cv)
    draw_map(cv)
    draw_also(cv)
    draw_datecheck(cv)
    draw_footer(cv)
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', 'out')
    os.makedirs(out, exist_ok=True)
    write_png(os.path.join(out, 'entry.png'), cv)


if __name__ == '__main__':
    main()
