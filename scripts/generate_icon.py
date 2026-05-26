#!/usr/bin/env python3
"""Generate circular minimalist app icons for Screen Off Timer."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "icons" / "screen-off-timer-master.png"
HICOLOR = ROOT / "data" / "icons" / "hicolor"
SIZES = (16, 32, 48, 64, 128, 256)

# Bright palette
MAGENTA = (233, 30, 140)
ORANGE = (255, 152, 0)
YELLOW = (255, 213, 79)
CYAN = (0, 229, 255)
CORAL = (255, 107, 107)
WHITE = (255, 255, 255)
NAVY = (26, 35, 64)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    cx = cy = size / 2.0
    radius = size * 0.48

    # Circular gradient fill
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist > radius:
                continue
            # diagonal gradient factor
            t = (x / size * 0.55 + y / size * 0.45)
            t = max(0.0, min(1.0, t))
            color = lerp_color(MAGENTA, ORANGE, t)
            if t > 0.72:
                color = lerp_color(ORANGE, YELLOW, (t - 0.72) / 0.28)
            px[x, y] = (*color, 255)

    draw = ImageDraw.Draw(img)
    s = size / 256.0
    lw = max(2, int(5 * s))

    def rr(box: tuple[float, float, float, float], **kwargs) -> None:
        x0, y0, x1, y1 = (int(v) for v in box)
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        if x1 - x0 < 2 or y1 - y0 < 2:
            return
        r = kwargs.pop("radius", 0)
        kwargs["radius"] = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
        draw.rounded_rectangle((x0, y0, x1, y1), **kwargs)

    # Monitor body (rounded rect)
    rr((72 * s, 98 * s, 184 * s, 168 * s), radius=int(10 * s), outline=WHITE, width=lw)
    if size >= 48:
        sw = 36 * s
        rr((cx - sw / 2, 168 * s, cx + sw / 2, 182 * s), radius=int(4 * s), fill=WHITE)
        rr((cx - 52 * s, 180 * s, cx + 52 * s, 192 * s), radius=int(5 * s), fill=WHITE)

    # Power symbol inside screen
    pcx, pcy = cx, 128 * s
    pr = max(4, 22 * s)
    draw.ellipse(
        (pcx - pr, pcy - pr, pcx + pr, pcy + pr),
        outline=CYAN,
        width=lw,
    )
    draw.line((pcx, pcy - pr * 0.72, pcx, pcy + pr * 0.15), fill=CYAN, width=lw)

    # Timer dots (arc above monitor)
    for i, angle in enumerate((205, 270, 335)):
        rad = math.radians(angle)
        r = 78 * s
        dot_r = max(3, int((5 if i == 1 else 4) * s))
        dx = cx + r * math.cos(rad)
        dy = 88 * s + r * math.sin(rad) * 0.35
        fill = CORAL if i != 1 else WHITE
        draw.ellipse(
            (dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r),
            fill=fill,
        )

    # Subtle inner ring for depth
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        outline=(255, 255, 255, 60),
        width=max(1, int(2 * s)),
    )

    return img


def main() -> None:
    master = render(512)
    MASTER.parent.mkdir(parents=True, exist_ok=True)
    master.save(MASTER)

    for size in SIZES:
        out_dir = HICOLOR / f"{size}x{size}" / "apps"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "screen-off-timer.png"
        render(size).save(out, optimize=True)
        print(f"Wrote {out}")

    print(f"Master: {MASTER}")

    ico_path = ROOT / "data" / "icons" / "screen-off-timer.ico"
    master.resize((256, 256), Image.Resampling.LANCZOS).save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print(f"ICO:   {ico_path}")


if __name__ == "__main__":
    main()
