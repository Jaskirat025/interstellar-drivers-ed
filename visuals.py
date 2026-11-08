"""Vector art shared by the simulator screens.

Everything here draws straight onto a Tk Canvas with flat lines and fills:
no image files, no gradients and no charting dependency. The palette is
repeated here so this module can also be used by small standalone canvas
widgets without importing the simulator.
"""

import math

BG = "#000000"
YELLOW = "#FFE81F"
TEXT = "#C9D1D9"
MUTED = "#8B96A3"
GRID = "#14181D"
DEEP = "#080A0C"


def _hexagon(cx, cy, radius, rotation=-90.0):
    points = []
    for index in range(6):
        angle = math.radians(rotation + index * 60.0)
        points.extend((cx + radius * math.cos(angle),
                       cy + radius * math.sin(angle)))
    return points


def draw_grid(c, width, height, step=64, colour=GRID):
    step = max(20, int(step))
    x = 0
    while x <= width:
        c.create_line(x, 0, x, height, fill=colour)
        x += step
    y = 0
    while y <= height:
        c.create_line(0, y, width, y, fill=colour)
        y += step


def draw_corner_marks(c, x0, y0, x1, y1, colour=MUTED, length=14, width=1):
    length = max(4, int(length))
    for x, y, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1),
                         (x0, y1, 1, -1), (x1, y1, -1, -1)):
        c.create_line(x, y, x + sx * length, y, fill=colour, width=width)
        c.create_line(x, y, x, y + sy * length, fill=colour, width=width)


def draw_backdrop(c, width, height, stars=42):
    """Dim archival grid and corner registration marks for a screen."""
    if width < 4 or height < 4:
        return
    c.delete("all")
    c.create_rectangle(0, 0, width, height, fill=BG, outline="")
    draw_grid(c, width, height, 72, GRID)
    for index in range(stars):
        x = ((index * 193 + 37) % 997) / 997.0 * width
        y = ((index * 311 + 89) % 991) / 991.0 * height
        radius = 1 if index % 11 else 2
        c.create_oval(x - radius, y - radius, x + radius, y + radius,
                      fill=MUTED if index % 3 else TEXT, outline="")
    c.create_line(24, height - 28, width - 24, height - 28, fill=GRID)
    c.create_line(24, 28, width - 24, 28, fill=GRID)
    draw_corner_marks(c, 24, 24, width - 24, height - 24, MUTED, 15)


def draw_orbit(c, cx, cy, rx, ry, colour=GRID, dash=(2, 9)):
    c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry,
                  outline=colour, dash=dash)
    c.create_oval(cx - rx * 0.64, cy - ry * 0.64,
                  cx + rx * 0.64, cy + ry * 0.64,
                  outline=colour, dash=dash)
    for angle in (20, 145, 265):
        radians = math.radians(angle)
        x = cx + rx * math.cos(radians)
        y = cy + ry * math.sin(radians)
        c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=MUTED, outline="")


def draw_planet(c, cx, cy, radius, colour=MUTED):
    if radius < 8:
        return
    c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                  fill=DEEP, outline=colour)
    c.create_arc(cx - radius * 0.9, cy - radius * 0.9,
                 cx + radius * 0.9, cy + radius * 0.9,
                 start=205, extent=115, style="arc", outline=GRID)
    c.create_arc(cx - radius * 0.7, cy - radius * 0.7,
                 cx + radius * 0.7, cy + radius * 0.7,
                 start=20, extent=75, style="arc", outline=GRID)
    c.create_arc(cx - radius * 0.45, cy - radius * 0.45,
                 cx + radius * 0.45, cy + radius * 0.45,
                 start=280, extent=60, style="arc", outline=GRID)
    for angle, distance, size in ((-35, .46, .18), (25, .58, .10),
                                  (120, .40, .12)):
        radians = math.radians(angle)
        x = cx + radius * distance * math.cos(radians)
        y = cy + radius * distance * math.sin(radians)
        r = radius * size
        c.create_oval(x - r, y - r, x + r, y + r, outline=GRID)
    c.create_line(cx - radius * 1.18, cy, cx + radius * 1.18, cy,
                  fill=GRID, dash=(2, 7))


def draw_star_destroyer(c, x, y, size, colour=MUTED):
    if size < 10:
        return
    points = (x, y,
              x + size, y + size * 0.18,
              x + size * 0.56, y + size * 0.34,
              x + size * 0.14, y + size * 0.42,
              x - size * 0.58, y + size * 0.32,
              x - size, y + size * 0.18)
    c.create_polygon(points, fill=DEEP, outline=colour)
    c.create_polygon(x - size * 0.16, y + size * 0.04,
                     x + size * 0.16, y + size * 0.08,
                     x + size * 0.13, y + size * 0.17,
                     x - size * 0.13, y + size * 0.17,
                     fill=BG, outline=colour)
    c.create_line(x - size * 0.72, y + size * 0.23,
                  x + size * 0.62, y + size * 0.23, fill=GRID)
    c.create_line(x - size * 0.52, y + size * 0.29,
                  x + size * 0.40, y + size * 0.29, fill=GRID)
    c.create_line(x, y - size * 0.17, x, y - size * 0.04, fill=colour)


def draw_xwing(c, cx, cy, size, colour=YELLOW):
    if size < 12:
        return
    s = size
    c.create_line(cx, cy - s * 0.58, cx, cy + s * 0.38,
                  fill=colour, width=2)
    c.create_polygon(cx, cy - s * 0.62,
                     cx + s * 0.12, cy - s * 0.34,
                     cx + s * 0.10, cy + s * 0.30,
                     cx - s * 0.10, cy + s * 0.30,
                     cx - s * 0.12, cy - s * 0.34,
                     fill=BG, outline=colour)
    for side in (-1, 1):
        c.create_polygon(cx + side * s * 0.10, cy - s * 0.14,
                         cx + side * s * 0.95, cy + s * 0.18,
                         cx + side * s * 0.82, cy + s * 0.36,
                         cx + side * s * 0.20, cy + s * 0.14,
                         fill=BG, outline=colour)
        c.create_line(cx + side * s * 0.20, cy + s * 0.14,
                      cx + side * s * 0.95, cy + s * 0.18,
                      fill=colour)
        ex = cx + side * s * 0.67
        ey = cy + s * 0.27
        c.create_oval(ex - s * 0.08, ey - s * 0.08,
                      ex + s * 0.08, ey + s * 0.08,
                      outline=colour)
        c.create_line(ex, ey - s * 0.08, ex, ey + s * 0.08,
                      fill=colour)
    c.create_polygon(cx, cy - s * 0.38,
                     cx + s * 0.10, cy - s * 0.20,
                     cx, cy - s * 0.08,
                     cx - s * 0.10, cy - s * 0.20,
                     fill=BG, outline=colour)
    c.create_line(cx - s * 0.10, cy + s * 0.30,
                  cx - s * 0.18, cy + s * 0.48, fill=colour)
    c.create_line(cx + s * 0.10, cy + s * 0.30,
                  cx + s * 0.18, cy + s * 0.48, fill=colour)


def draw_radar(c, cx, cy, radius, colour=YELLOW, muted=MUTED):
    if radius < 6:
        return
    for scale in (1.0, 0.66, 0.33):
        c.create_oval(cx - radius * scale, cy - radius * scale,
                      cx + radius * scale, cy + radius * scale,
                      outline=muted)
    c.create_line(cx - radius, cy, cx + radius, cy, fill=muted)
    c.create_line(cx, cy - radius, cx, cy + radius, fill=muted)
    c.create_line(cx, cy, cx + radius * 0.72, cy - radius * 0.72,
                  fill=colour)
    c.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                 start=45, extent=45, style="arc", outline=GRID)


def draw_rank_badge(c, cx, cy, radius, rank, font=None):
    if radius < 10:
        return
    font = font or ("Courier", 9, "bold")
    c.create_polygon(_hexagon(cx, cy, radius), fill=DEEP,
                     outline=YELLOW, width=2)
    c.create_polygon(_hexagon(cx, cy, radius * 0.82), fill="",
                     outline=MUTED, dash=(2, 4))
    c.create_oval(cx - radius * 0.55, cy - radius * 0.55,
                  cx + radius * 0.55, cy + radius * 0.55,
                  outline=MUTED)
    for index in range(3):
        y = cy + radius * (-0.28 + index * 0.28)
        c.create_line(cx - radius * 0.34, y,
                      cx + radius * 0.34, y, fill=YELLOW)
    initials = "".join(part[0] for part in rank.split())[:3]
    c.create_text(cx, cy - radius * 0.74, text="RAA",
                  fill=MUTED, font=font)
    c.create_text(cx, cy + radius * 0.72, text=initials,
                  fill=YELLOW, font=font)
    for angle in (0, 60, 120, 180, 240, 300):
        radians = math.radians(angle)
        x = cx + radius * 0.94 * math.cos(radians)
        y = cy + radius * 0.94 * math.sin(radians)
        c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=YELLOW, outline="")


def draw_auth_art(c, width, height, progress=0.0, font=None):
    font = font or ("Courier", 8, "normal")
    cx, cy = width / 2.0, height / 2.0
    radius = min(width, height) * 0.30
    c.create_line(12, cy, width - 12, cy, fill=GRID, dash=(2, 8))
    c.create_line(cx, 12, cx, height - 12, fill=GRID, dash=(2, 8))
    draw_radar(c, cx, cy, radius + 18, MUTED, GRID)
    c.create_polygon(_hexagon(cx, cy, radius, -90), fill=BG,
                     outline=MUTED, width=2)
    c.create_polygon(_hexagon(cx, cy, radius * 0.72, -90), fill="",
                     outline=YELLOW, dash=(2, 4))
    c.create_oval(cx - radius * 0.28, cy - radius * 0.28,
                  cx + radius * 0.28, cy + radius * 0.28,
                  outline=MUTED)
    c.create_text(cx, cy, text="RAA",
                  fill=YELLOW, font=font)
    c.create_arc(cx - radius - 25, cy - radius - 25,
                 cx + radius + 25, cy + radius + 25,
                 start=90, extent=-359 * max(0.0, min(1.0, progress)),
                 style="arc", outline=YELLOW, width=2)
    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        x = cx + (radius + 32) * math.cos(radians)
        y = cy + (radius + 32) * math.sin(radians)
        c.create_line(x, y,
                      cx + (radius + 25) * math.cos(radians),
                      cy + (radius + 25) * math.sin(radians),
                      fill=MUTED)
