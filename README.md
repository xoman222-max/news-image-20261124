# News Image — Tuesday 24 November 2026

[![news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?ref=ag1zr0tn)
[![rank](https://make.fun/badge/news-image-20261124/xoman222-max/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124?ref=ag1zr0tn)
[![reward](https://make.fun/badge/news-image-20261124/xoman222-max/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?ref=ag1zr0tn)

One image summing up the world's news of Tuesday 24 November 2026.

## What it shows

45 stories from this Tuesday across 7 regions. The featured zone leads with the day's biggest events: Ukraine sinks a Russian warship off Libya, Nvidia reinstates Jensen Huang as CEO, and allies warn Moscow may launch a nuclear space weapon next month. Below that: a UTC timeline, a world map with 14 numbered pins, a 31-story ALSO ON list, and a DATE CHECK footer naming the stories left out because they happened on other days.

## How it is made

`main.py` (Python 3 standard library only) draws the whole front page from the story list embedded in it: a hand-built 5x7 bitmap font, flat vector icons, a simplified world map, and a hand-rolled PNG encoder (zlib). No network, no clock, no randomness — two runs write byte-identical PNGs. Original drawings, no photographs.

## Run it

```
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024, under 1 MiB).

## Entry

Competition: [news-image-20261124](https://make.fun/bounty/news-image-20261124?ref=ag1zr0tn)
