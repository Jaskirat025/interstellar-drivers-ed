"""Hand-built 3D models for the simulator.

Everything here is geometry: no images, no external assets. Ships point along
+Z, rockets stand along +Y, and the hangar uses metres with the floor at y=0.
The faces are deliberately numerous enough to read as solid machinery when
flat-shaded, but still cheap enough for a 30 fps Canvas scene.
"""

import math
import random

from engine3d import Mesh


def _ring_points(radius, y, count=8):
    return [(radius * math.cos(2.0 * math.pi * index / count), y,
             radius * math.sin(2.0 * math.pi * index / count))
            for index in range(count)]


def xwing():
    mesh = Mesh()
    # Fuselage and nose.
    mesh.add_box(0, 0, 0, 0.62, 0.46, 3.0, "hull")
    mesh.add_cone((0, 0, 2.05), 0.31, 1.1, "z", 12, "hull")
    mesh.add_box(0, 0, 2.55, 0.12, 0.08, 0.3, "black")
    mesh.add_box(0, 0.24, 0.55, 0.44, 0.25, 1.15, "glass")
    mesh.add_box(0, 0.37, 0.55, 0.30, 0.05, 0.85, "hull_dark")
    mesh.add_box(0, 0.37, 0.13, 0.06, 0.05, 0.9, "hull_light")
    # Astromech socket and dome.
    mesh.add_cylinder((0, 0.28, -0.9), 0.19, 0.18, "y", 10, "black")
    mesh.add_sphere((0, 0.36, -0.9), 0.18, 10, 5, "droid")
    mesh.add_box(0, 0.42, -0.73, 0.10, 0.05, 0.05, "black")
    mesh.add_box(0.08, 0.38, -0.73, 0.04, 0.04, 0.04, "droid_red")
    # Rear equipment deck.
    mesh.add_box(0, 0.02, -1.55, 0.56, 0.46, 0.55, "hull_dark")
    mesh.add_box(0, 0.23, -1.7, 0.42, 0.12, 0.38, "panel")
    for side in (-1, 1):
        mesh.add_box(side * 0.18, 0.30, -1.72, 0.08, 0.08, 0.08, "engine")
    # Four S-foils with dihedral, accent stripes and panel lines.
    for side in (-1, 1):
        for upper in (-1, 1):
            y_root = upper * 0.10
            y_tip = upper * 0.36
            points = [
                (side * 0.30, y_root, 0.72),
                (side * 1.66, y_tip, 0.05),
                (side * 1.66, y_tip, -1.38),
                (side * 0.30, y_root, -1.18),
            ]
            mesh.add_thick_polygon(points, (0, 0.055, 0), "hull")
            accent = [
                (side * 0.46, y_root + upper * 0.01, 0.52),
                (side * 1.52, y_tip + upper * 0.01, -0.04),
                (side * 1.52, y_tip + upper * 0.01, -0.28),
                (side * 0.46, y_root + upper * 0.01, 0.20),
            ]
            mesh.add_thick_polygon(accent, (0, 0.012, 0), "accent")
            for line in range(1, 4):
                fraction = line / 4.0
                x = side * (0.30 + 1.36 * fraction)
                y = y_root + (y_tip - y_root) * fraction + upper * 0.035
                mesh.add_box(x, y, -0.70, 0.03, 0.008, 1.55, "hull_dark")
            # Cannon along the wing tip.
            mesh.add_beam((side * 1.58, y_tip + 0.02, -1.9),
                          (side * 1.58, y_tip + 0.02, 1.65), 0.075, "hull_dark")
            mesh.add_cylinder((side * 1.58, y_tip + 0.02, 1.72), 0.055,
                              0.34, "z", 8, "hull")
            mesh.add_cylinder((side * 1.58, y_tip + 0.02, 1.90), 0.035,
                              0.16, "z", 8, "accent")
            # Engine can, intake ring and emissive nozzle.
            mesh.add_cylinder((side * 0.62, upper * 0.30, -1.05), 0.22,
                              1.15, "z", 10, "hull_dark")
            mesh.add_torus((side * 0.62, upper * 0.30, -0.58), 0.23, 0.035,
                           12, 5, "steel", "z")
            mesh.add_cylinder((side * 0.62, upper * 0.30, -1.67), 0.16,
                              0.12, "z", 10, "engine")
            mesh.add_frustum((side * 0.62, upper * 0.30, -1.78), 0.17, 0.24,
                             0.18, "z", 10, "steel_dark")
            mesh.add_beam((side * 0.34, upper * 0.13, -0.92),
                          (side * 0.60, upper * 0.26, -0.92), 0.10, "hull")
    # Wing-root fairings.
    mesh.add_box(0, 0.02, -0.55, 0.70, 0.52, 1.3, "hull")
    mesh.add_box(0, -0.29, 0.25, 0.38, 0.14, 1.9, "hull_dark")
    # Small greebles.
    for x in (-0.18, 0.18):
        mesh.add_box(x, 0.16, 1.25, 0.10, 0.06, 0.38, "panel")
    for z in (-0.2, 0.2):
        mesh.add_box(0.26, -0.12, z, 0.04, 0.16, 0.08, "steel_dark")
    return mesh


def tie_fighter():
    mesh = Mesh()
    # Ball cockpit.
    mesh.add_sphere((0, 0, 0), 0.56, 12, 7, "hull_dark")
    mesh.add_sphere((0, 0, 0.05), 0.42, 10, 5, "panel")
    # Hexagonal viewport and frame.
    front = [(0.38 * math.cos(math.radians(60 * i - 30)),
              0.38 * math.sin(math.radians(60 * i - 30)), 0.49)
             for i in range(6)]
    mesh.add_thick_polygon(front, (0, 0, 0.02), "glass_dark")
    for index in range(6):
        a = front[index]
        b = front[(index + 1) % 6]
        mesh.add_beam((a[0], a[1], 0.52), (b[0], b[1], 0.52), 0.035,
                      "steel_dark")
    mesh.add_beam((0, 0, 0.50), (0.38, 0, 0.50), 0.025, "steel_dark")
    mesh.add_beam((0, 0, 0.50), (-0.19, 0.33, 0.50), 0.025, "steel_dark")
    mesh.add_beam((0, 0, 0.50), (-0.19, -0.33, 0.50), 0.025, "steel_dark")
    # Wing pylons.
    for side in (-1, 1):
        mesh.add_cylinder((side * 0.86, 0, 0), 0.10, 0.72, "x", 8, "steel")
        mesh.add_box(side * 1.10, 0, 0, 0.18, 0.42, 0.30, "hull_dark")
        # Hexagonal solar wing, built as a thick plate with a frame.
        wing = []
        for index in range(6):
            angle = math.radians(60 * index - 30)
            wing.append((side * 1.28, 1.22 * math.sin(angle),
                         1.22 * math.cos(angle)))
        mesh.add_thick_polygon(wing, (0.07, 0, 0), "panel")
        inner = []
        for index in range(6):
            angle = math.radians(60 * index - 30)
            inner.append((side * 1.30, 0.98 * math.sin(angle),
                          0.98 * math.cos(angle)))
        mesh.add_thick_polygon(inner, (0.02, 0, 0), "steel_dark")
        for index in range(6):
            a = wing[index]
            b = wing[(index + 1) % 6]
            mesh.add_beam(a, b, 0.045, "hull_light")
        for offset in (-0.55, 0.0, 0.55):
            mesh.add_beam((side * 1.32, -1.05, offset),
                          (side * 1.32, 1.05, offset), 0.018, "hull_dark")
        for offset in (-0.55, 0.0, 0.55):
            mesh.add_beam((side * 1.32, offset, -1.05),
                          (side * 1.32, offset, 1.05), 0.018, "hull_dark")
        # Wingtip cannon.
        mesh.add_beam((side * 1.32, -1.30, 0.25),
                      (side * 1.32, -1.30, -1.35), 0.05, "steel")
        mesh.add_cylinder((side * 1.32, -1.30, -1.45), 0.07, 0.28, "z", 6,
                          "hull_dark")
    # Chin guns.
    for side in (-1, 1):
        mesh.add_beam((side * 0.20, -0.42, 0.20),
                      (side * 0.20, -0.42, 0.95), 0.055, "steel")
        mesh.add_cylinder((side * 0.20, -0.42, 1.0), 0.04, 0.18, "z", 6,
                          "engine_blue")
    mesh.add_box(0, 0.48, -0.20, 0.18, 0.08, 0.32, "panel")
    return mesh


def star_destroyer():
    mesh = Mesh()
    # Dagger hull: a triangular slab with a raised spine.
    mesh.add_slab([(0, 4.2), (2.35, -2.7), (-2.35, -2.7)], -0.42, 0.42,
                  "hull")
    mesh.add_slab([(0, 3.6), (1.70, -2.1), (-1.70, -2.1)], 0.42, 0.62,
                  "panel")
    mesh.add_slab([(0, 2.7), (0.65, -1.7), (-0.65, -1.7)], 0.62, 0.78,
                  "hull_light")
    # Rim trenches and panel lines.
    for side in (-1, 1):
        mesh.add_beam((side * 2.05, 0, -2.3), (side * 0.18, 0, 3.9), 0.10,
                      "steel_dark")
        mesh.add_beam((side * 1.55, 0.02, -2.35), (side * 0.12, 0.02, 3.2),
                      0.035, "accent_dark")
        for index in range(5):
            fraction = index / 5.0
            x = side * (0.2 + 1.6 * fraction)
            z = 3.5 - 5.5 * fraction
            mesh.add_box(x, 0.44, z, 0.06, 0.02, 0.9, "hull_dark")
    for index in range(6):
        z = 2.8 - index * 0.85
        mesh.add_box(0, 0.46, z, 0.45 + index * 0.22, 0.02, 0.10,
                     "hull_dark")
    # Bridge tower and command deck.
    mesh.add_box(0, 0.95, -2.15, 1.15, 0.55, 0.95, "hull")
    mesh.add_box(0, 1.48, -2.28, 0.62, 0.55, 0.62, "panel")
    mesh.add_box(0, 1.91, -2.34, 1.02, 0.28, 0.50, "hull_light")
    mesh.add_box(0, 2.10, -2.34, 1.30, 0.12, 0.64, "hull_dark")
    for side in (-1, 1):
        mesh.add_sphere((side * 0.43, 2.20, -2.34), 0.15, 8, 4, "hull_light")
        mesh.add_beam((side * 0.30, 2.02, -2.34),
                      (side * 1.6, 1.65, -2.34), 0.03, "steel")
    # Engine bank.
    for x in (-1.15, 0, 1.15):
        mesh.add_cylinder((x, 0.05, -2.90), 0.34, 0.38, "z", 10, "steel_dark")
        mesh.add_cylinder((x, 0.05, -3.10), 0.24, 0.06, "z", 10, "engine_blue")
    # Hangar mouth and small surface greebles.
    mesh.add_box(0, -0.42, 0.6, 0.90, 0.05, 1.4, "black")
    mesh.add_box(0, -0.44, 0.0, 1.20, 0.04, 0.18, "light_dim")
    for x, z in ((-0.55, 1.4), (0.55, 1.4), (-0.8, -0.6), (0.8, -0.6),
                 (0.0, -1.1), (-0.35, 2.3), (0.35, 2.3)):
        mesh.add_box(x, 0.48, z, 0.24, 0.06, 0.30, "steel_dark")
    return mesh


def falcon9():
    mesh = Mesh()
    # Octaweb and nine engine bells.
    mesh.add_cylinder((0, 0.35, 0), 0.46, 0.7, "y", 12, "steel_dark")
    positions = [(0, 0)]
    for index in range(8):
        angle = 2 * math.pi * index / 8
        positions.append((0.30 * math.cos(angle), 0.30 * math.sin(angle)))
    for x, z in positions:
        mesh.add_frustum((x, 0.05, z), 0.055, 0.13, 0.34, "y", 8,
                         "steel_dark")
        mesh.add_ring((x, -0.12, z), 0.14, 0.10, 8, "engine", "y")
    # First stage.
    mesh.add_cylinder((0, 3.45, 0), 0.46, 7.0, "y", 14, "hull_light")
    mesh.add_cylinder((0, 1.0, 0), 0.47, 0.35, "y", 14, "black")
    mesh.add_cylinder((0, 5.6, 0), 0.47, 0.18, "y", 14, "black")
    mesh.add_beam((0.0, 0.75, 0.47), (0.0, 6.6, 0.47), 0.07, "hull")
    # Raceway, pipes and four landing legs.
    for side in (-1, 1):
        for z in (-0.20, 0.20):
            mesh.add_beam((side * 0.68, 0.35, z),
                          (side * 0.68, 0.30, z), 0.08, "steel_dark")
            mesh.add_beam((side * 0.55, 0.55, z),
                          (side * 0.92, 0.06, z * 1.7), 0.10, "steel")
            mesh.add_box(side * 0.98, 0.04, z * 1.7, 0.24, 0.08, 0.28,
                         "black")
    # Grid fins at the top of the first stage.
    for side in (-1, 1):
        for z in (-1, 1):
            panel = [
                (side * 0.58, 6.35, z * 0.34),
                (side * 0.95, 6.35, z * 0.34),
                (side * 0.95, 6.35, z * 0.52),
                (side * 0.58, 6.35, z * 0.52),
            ]
            mesh.add_thick_polygon(panel, (0, 0.42, 0), "steel_dark")
            mesh.add_beam((side * 0.60, 6.55, z * 0.43),
                          (side * 0.93, 6.55, z * 0.43), 0.025, "steel")
    # Interstage, second stage and fairing.
    mesh.add_cylinder((0, 7.15, 0), 0.46, 0.55, "y", 14, "black")
    mesh.add_cylinder((0, 8.8, 0), 0.43, 2.6, "y", 14, "hull_light")
    mesh.add_cylinder((0, 9.4, 0), 0.44, 0.10, "y", 14, "steel_dark")
    mesh.add_cylinder((0, 10.24, 0), 0.46, 0.25, "y", 14, "hull")
    mesh.add_frustum((0, 11.25, 0), 0.46, 0.08, 1.8, "y", 14, "hull_light")
    mesh.add_sphere((0, 12.13, 0), 0.09, 8, 4, "hull_dark")
    # Fairing seam and payload marks.
    mesh.add_box(0, 10.45, 0.45, 0.02, 0.18, 0.02, "black")
    mesh.add_box(0, 9.1, 0.44, 0.12, 0.42, 0.02, "black")
    mesh.add_box(0, 8.2, 0.44, 0.20, 0.03, 0.02, "accent")
    return mesh


def starship():
    mesh = Mesh()
    # Engine skirt and six engines.
    mesh.add_cylinder((0, 0.55, 0), 0.60, 0.90, "y", 14, "steel_dark")
    for index in range(6):
        angle = 2 * math.pi * index / 6
        x, z = 0.34 * math.cos(angle), 0.34 * math.sin(angle)
        mesh.add_frustum((x, 0.12, z), 0.10, 0.18, 0.45, "y", 8, "steel")
        mesh.add_ring((x, -0.08, z), 0.19, 0.13, 8, "engine_blue", "y")
    # Main tank and nose.
    mesh.add_cylinder((0, 4.55, 0), 0.58, 7.1, "y", 16, "hull_light")
    mesh.add_cylinder((0, 1.45, 0), 0.60, 0.18, "y", 16, "steel_dark")
    mesh.add_cylinder((0, 5.2, 0), 0.59, 0.16, "y", 16, "steel")
    mesh.add_frustum((0, 9.55, 0), 0.58, 0.08, 2.9, "y", 16, "hull_light")
    mesh.add_sphere((0, 11.0, 0), 0.075, 8, 4, "steel_dark")
    # Welded seams.
    for y in (2.6, 3.9, 5.2, 6.5, 7.8):
        mesh.add_ring((0, y, 0), 0.595, 0.58, 16, "steel_dark", "y")
    # Windward heat-shield tiles.
    for row in range(9):
        y = 1.7 + row * 0.65
        for column in range(4):
            angle = math.radians(150 + column * 20)
            mesh.add_box(0.58 * math.cos(angle), y, 0.58 * math.sin(angle),
                         0.22, 0.42, 0.02, "tile" if (row + column) % 2
                         else "tile_light")
    # Forward and aft flaps.
    for side in (-1, 1):
        front = [
            (side * 0.58, 9.2, 0.0),
            (side * 1.45, 8.6, 0.0),
            (side * 1.25, 7.7, 0.0),
            (side * 0.58, 7.9, 0.0),
        ]
        mesh.add_thick_polygon(front, (0, 0, 0.16), "steel_dark")
        aft = [
            (side * 0.58, 2.2, 0.0),
            (side * 1.55, 1.5, 0.0),
            (side * 1.35, 0.55, 0.0),
            (side * 0.58, 0.9, 0.0),
        ]
        mesh.add_thick_polygon(aft, (0, 0, 0.16), "steel")
    # Catch pins and small vents.
    for side in (-1, 1):
        mesh.add_box(side * 0.30, 1.05, -0.55, 0.10, 0.10, 0.10, "hazard")
    for index in range(3):
        mesh.add_box(0, 4.0 + index * 1.6, -0.59, 0.18, 0.22, 0.03, "black")
    return mesh


def booster():
    mesh = Mesh()
    mesh.add_cylinder((0, 0.35, 0), 0.46, 0.7, "y", 12, "steel_dark")
    for index in range(4):
        angle = 2 * math.pi * index / 4
        x, z = 0.28 * math.cos(angle), 0.28 * math.sin(angle)
        mesh.add_frustum((x, 0.04, z), 0.07, 0.16, 0.36, "y", 8, "steel_dark")
    mesh.add_cylinder((0, 3.55, 0), 0.46, 6.8, "y", 14, "hull_light")
    mesh.add_cylinder((0, 7.0, 0), 0.46, 0.45, "y", 14, "black")
    mesh.add_cylinder((0, 0.95, 0), 0.47, 0.28, "y", 14, "black")
    mesh.add_beam((0, 0.7, 0.47), (0, 6.7, 0.47), 0.06, "hull")
    for side in (-1, 1):
        for z in (-0.22, 0.22):
            mesh.add_beam((side * 0.55, 0.55, z),
                          (side * 0.92, 0.06, z * 1.7), 0.10, "steel")
            mesh.add_box(side * 0.98, 0.04, z * 1.7, 0.24, 0.08, 0.28,
                         "black")
        for z in (-1, 1):
            panel = [
                (side * 0.58, 6.2, z * 0.34),
                (side * 0.95, 6.2, z * 0.34),
                (side * 0.95, 6.2, z * 0.52),
                (side * 0.58, 6.2, z * 0.52),
            ]
            mesh.add_thick_polygon(panel, (0, 0.40, 0), "steel_dark")
    mesh.add_cylinder((0, 7.25, 0), 0.44, 0.08, "y", 12, "engine")
    return mesh


def astronaut():
    mesh = Mesh()
    # Legs and boots.
    for side in (-1, 1):
        mesh.add_box(side * 0.16, 0.48, 0, 0.22, 0.86, 0.24, "suit")
        mesh.add_box(side * 0.16, 0.08, 0.08, 0.25, 0.16, 0.40, "suit_shadow")
        mesh.add_box(side * 0.16, 0.62, 0.0, 0.23, 0.10, 0.25, "suit_shadow")
        # Arms, slightly out from the body.
        mesh.add_beam((side * 0.29, 1.48, 0), (side * 0.46, 1.05, 0.08),
                      0.19, "suit")
        mesh.add_box(side * 0.48, 0.96, 0.12, 0.20, 0.18, 0.24, "suit_shadow")
    # Torso, chest control box and backpack.
    mesh.add_box(0, 1.18, 0, 0.58, 0.78, 0.34, "suit")
    mesh.add_box(0, 1.18, 0.19, 0.30, 0.24, 0.05, "panel")
    mesh.add_box(0.10, 1.22, 0.22, 0.06, 0.06, 0.02, "accent")
    mesh.add_box(-0.10, 1.22, 0.22, 0.06, 0.06, 0.02, "droid_red")
    mesh.add_box(0, 1.25, -0.29, 0.48, 0.64, 0.22, "suit_shadow")
    mesh.add_box(0, 1.48, -0.42, 0.20, 0.18, 0.08, "steel")
    # Helmet, visor and neck ring.
    mesh.add_box(0, 1.72, 0, 0.30, 0.18, 0.26, "suit_shadow")
    mesh.add_sphere((0, 1.96, 0), 0.30, 12, 6, "suit")
    mesh.add_box(0, 1.98, 0.24, 0.36, 0.24, 0.12, "visor")
    mesh.add_box(0, 2.08, 0.26, 0.24, 0.05, 0.05, "accent")
    mesh.add_torus((0, 1.72, 0), 0.20, 0.035, 12, 5, "steel", "y")
    # Chest tether and suit details.
    mesh.add_beam((0.20, 1.38, 0.20), (0.20, 1.68, 0.20), 0.025, "steel")
    mesh.add_beam((-0.20, 1.38, 0.20), (-0.20, 1.68, 0.20), 0.025, "steel")
    for x, y in ((-0.18, 0.90), (0.18, 0.90)):
        mesh.add_box(x, y, 0.16, 0.05, 0.05, 0.02, "accent")
    return mesh


def astromech():
    mesh = Mesh()
    # Feet and legs.
    for side in (-1, 1):
        mesh.add_box(side * 0.30, 0.10, 0.0, 0.26, 0.20, 0.48, "steel_dark")
        mesh.add_beam((side * 0.30, 0.18, 0.0), (side * 0.28, 0.62, 0.0),
                      0.20, "droid_blue")
        mesh.add_box(side * 0.30, 0.21, 0.16, 0.16, 0.05, 0.06, "accent")
    mesh.add_box(0, 0.08, 0.0, 0.18, 0.16, 0.34, "steel_dark")
    # Body and dome.
    mesh.add_cylinder((0, 0.62, 0), 0.34, 0.80, "y", 14, "droid")
    mesh.add_cylinder((0, 0.30, 0), 0.35, 0.10, "y", 14, "droid_blue")
    mesh.add_sphere((0, 1.03, 0), 0.34, 14, 7, "droid")
    mesh.add_cylinder((0, 1.03, 0), 0.30, 0.18, "y", 14, "droid_blue")
    mesh.add_sphere((0, 1.20, 0.27), 0.075, 8, 4, "black")
    mesh.add_box(0, 1.20, 0.345, 0.10, 0.07, 0.02, "engine_blue")
    mesh.add_box(0.18, 1.28, 0.10, 0.08, 0.16, 0.08, "droid_red")
    mesh.add_box(-0.15, 1.31, -0.02, 0.05, 0.22, 0.05, "steel")
    # Front panels and a little tool arm.
    mesh.add_box(0, 0.62, 0.335, 0.24, 0.30, 0.03, "droid_blue")
    mesh.add_box(0.12, 0.58, 0.355, 0.08, 0.08, 0.02, "accent")
    mesh.add_box(-0.08, 0.46, 0.355, 0.06, 0.12, 0.02, "black")
    mesh.add_beam((0.20, 0.55, 0.32), (0.42, 0.38, 0.42), 0.05, "steel")
    return mesh


def hangar():
    mesh = Mesh()
    # Floor and landing platform.
    mesh.add_quad([(-9, 0, -8), (9, 0, -8), (9, 0, 6), (-9, 0, 6)], "floor")
    for index in range(-8, 9, 2):
        mesh.add_box(index, 0.012, -1.0, 0.025, 0.01, 14.0, "floor_grid")
    for index in range(-8, 7, 2):
        mesh.add_box(0, 0.012, index, 18.0, 0.01, 0.025, "floor_grid")
    mesh.add_cylinder((0, 0.06, 0), 3.35, 0.12, "y", 24, "steel_dark")
    mesh.add_torus((0, 0.13, 0), 3.35, 0.06, 24, 5, "accent", "y")
    mesh.add_torus((0, 0.13, 0), 2.35, 0.025, 24, 4, "steel", "y")
    for index in range(16):
        angle = 2 * math.pi * index / 16
        mesh.add_box(3.65 * math.cos(angle), 0.16, 3.65 * math.sin(angle),
                     0.38, 0.05, 0.14, "hazard")
    # Back wall with a large bay door and windows.
    mesh.add_box(0, 3.5, -8.0, 18.0, 7.0, 0.18, "panel")
    mesh.add_box(0, 2.2, -7.88, 4.0, 4.4, 0.12, "steel_dark")
    mesh.add_box(0, 2.2, -7.80, 4.3, 4.7, 0.10, "hull_dark")
    for x in (-2.0, 2.0):
        mesh.add_beam((x, 0.0, -7.70), (x, 4.4, -7.70), 0.16, "hazard")
    for y in (1.1, 2.2, 3.3):
        mesh.add_box(0, y, -7.76, 4.0, 0.08, 0.04, "steel")
    for x in (-2.4, 2.4):
        mesh.add_beam((x, 0.0, -7.70), (x, 4.8, -7.70), 0.12, "steel")
    # Glowing observation windows.
    for x in (-5.6, 5.6):
        mesh.add_box(x, 5.1, -7.86, 1.8, 0.9, 0.08, "glass")
        mesh.add_box(x, 5.1, -7.80, 1.9, 1.0, 0.04, "light_dim")
        for offset in (-0.8, 0.8):
            mesh.add_box(x + offset, 5.1, -7.72, 0.06, 1.0, 0.06, "steel")
    # Side walls and columns.
    for side in (-1, 1):
        mesh.add_box(side * 9.0, 3.5, -1.0, 0.20, 7.0, 14.0, "floor")
        for z in (-6.5, -3.0, 0.5, 4.0):
            mesh.add_beam((side * 8.6, 0, z), (side * 8.6, 7.0, z), 0.24,
                          "steel")
            mesh.add_box(side * 8.45, 3.4, z, 0.18, 0.18, 0.35, "light_dim")
        mesh.add_beam((side * 8.4, 6.6, -7.0), (side * 8.4, 6.6, 5.0),
                      0.18, "steel")
    # Ceiling trusses and hanging lamps.
    mesh.add_box(0, 7.0, -1.0, 18.0, 0.18, 14.0, "steel_dark")
    for z in (-6.0, -2.5, 1.0, 4.5):
        mesh.add_beam((-8.6, 6.85, z), (8.6, 6.85, z), 0.20, "steel")
    for x in (-4.8, 0.0, 4.8):
        for z in (-3.5, 1.5):
            mesh.add_beam((x, 6.8, z), (x, 6.1, z), 0.10, "steel")
            mesh.add_box(x, 5.95, z, 1.5, 0.12, 0.42, "light")
            mesh.add_box(x, 6.02, z, 1.7, 0.08, 0.52, "steel_dark")
    # Gantry on the left.
    for x in (-5.2, -6.2):
        mesh.add_beam((x, 0, -2.0), (x, 5.6, -2.0), 0.24, "steel")
    for y in (1.6, 3.2, 4.8):
        mesh.add_beam((-6.4, y, -2.0), (-3.4, y, -2.0), 0.16, "steel")
        mesh.add_beam((-6.2, y, -2.0), (-6.2, y + 1.3, -2.0), 0.09, "steel")
    mesh.add_box(-4.9, 4.95, -2.0, 2.0, 0.10, 0.9, "steel_dark")
    mesh.add_beam((-5.8, 5.7, -2.0), (-3.4, 6.2, -2.0), 0.22, "steel")
    mesh.add_beam((-3.6, 6.1, -2.0), (-3.6, 5.2, -2.0), 0.14, "steel")
    mesh.add_box(-3.6, 5.0, -2.0, 0.25, 0.35, 0.35, "hazard")
    # Crates, barrels and a fuel tank on the right.
    for index, (x, z, size) in enumerate(((5.6, 1.6, 1.2), (6.7, 0.4, 0.9),
                                         (5.4, -0.9, 1.0), (7.1, -2.1, 0.7))):
        mesh.add_box(x, size / 2 + 0.05, z, size, size, size, "steel_dark")
        mesh.add_box(x, size / 2 + 0.06, z, size * 0.72, size * 0.10,
                     size * 0.72, "rust" if index % 2 else "panel")
        mesh.add_box(x, size * 0.75, z, size * 0.80, 0.05, 0.12, "hazard")
    for x, z in ((4.6, 2.5), (5.2, 2.5), (4.9, 3.2)):
        mesh.add_cylinder((x, 0.55, z), 0.28, 0.9, "y", 10, "rust")
        mesh.add_cylinder((x, 0.95, z), 0.29, 0.06, "y", 10, "hazard")
    mesh.add_cylinder((6.8, 1.5, -5.6), 1.0, 3.0, "y", 16, "hull")
    mesh.add_sphere((6.8, 3.0, -5.6), 1.0, 12, 5, "hull")
    for y in (0.8, 1.8, 2.8):
        mesh.add_torus((6.8, y, -5.6), 1.02, 0.04, 16, 4, "steel_dark", "y")
    for y in (0.5, 1.5, 2.5):
        mesh.add_beam((5.85, y, -5.6), (4.6, y, -5.6), 0.14, "steel")
        mesh.add_beam((4.6, y, -5.6), (4.6, y - 0.4, -5.6), 0.14, "steel")
    # Holographic projector ring around the display platform.
    mesh.add_torus((0, 0.22, 0), 3.05, 0.035, 28, 4, "accent_dark", "y")
    mesh.add_box(0, 0.26, 3.6, 0.8, 0.20, 0.5, "steel_dark")
    mesh.add_box(0, 0.36, 3.6, 0.5, 0.05, 0.3, "engine_blue")
    # Cables across the floor.
    for offset in (-0.2, 0.2):
        mesh.add_beam((-7.8, 0.04, 3.2 + offset), (-4.8, 0.04, 1.4),
                      0.06, "rubber")
        mesh.add_beam((7.8, 0.04, 2.2 + offset), (5.4, 0.04, 0.2),
                      0.06, "rubber")
    return mesh


def launch_pad():
    mesh = Mesh()
    mesh.add_quad([(-8, 0, -5), (8, 0, -5), (8, 0, 8), (-8, 0, 8)], "floor")
    for x in range(-7, 8, 2):
        mesh.add_box(x, 0.02, 1.5, 0.04, 0.01, 13.0, "floor_grid")
    for z in range(-4, 8, 2):
        mesh.add_box(0, 0.02, z, 16.0, 0.01, 0.04, "floor_grid")
    mesh.add_cylinder((0, 0.15, 0), 2.2, 0.3, "y", 20, "steel_dark")
    mesh.add_cylinder((0, 0.32, 0), 1.1, 0.25, "y", 16, "steel")
    for index in range(8):
        angle = 2 * math.pi * index / 8
        x, z = 1.6 * math.cos(angle), 1.6 * math.sin(angle)
        mesh.add_box(x, 0.35, z, 0.45, 0.20, 0.45, "hazard")
    # Launch tower.
    for x, z in ((-3.4, -1.6), (-3.4, 1.0), (-4.8, -1.6), (-4.8, 1.0)):
        mesh.add_beam((x, 0, z), (x, 9.0, z), 0.20, "steel")
    for y in (1.5, 3.2, 5.0, 6.8, 8.4):
        mesh.add_beam((-4.8, y, -1.6), (-3.4, y, -1.6), 0.10, "steel")
        mesh.add_beam((-4.8, y, 1.0), (-3.4, y, 1.0), 0.10, "steel")
        mesh.add_box(-4.1, y, -0.3, 1.1, 0.10, 2.4, "steel_dark")
    for y in (2.6, 4.4, 6.2):
        mesh.add_beam((-3.3, y, 0), (-1.2, y + 0.2, 0), 0.16, "steel")
    mesh.add_beam((-3.3, 8.8, 0), (-0.8, 9.1, 0), 0.22, "steel")
    mesh.add_box(-4.1, 9.2, -0.3, 0.25, 0.25, 0.25, "light")
    # Lightning masts and searchlights.
    for x, z in ((-6.5, 4.5), (6.5, 4.5), (6.5, -4.0)):
        mesh.add_beam((x, 0, z), (x, 6.0, z), 0.10, "steel")
        mesh.add_beam((x - 0.4, 5.4, z), (x + 0.4, 5.4, z), 0.08, "steel")
        mesh.add_box(x, 6.05, z, 0.18, 0.18, 0.18, "light")
    for x, z in ((-5.8, 3.0), (5.8, 2.0)):
        mesh.add_cylinder((x, 0.45, z), 0.35, 0.6, "y", 8, "steel_dark")
        mesh.add_box(x, 0.9, z, 0.45, 0.30, 0.45, "light_dim")
    # Flame trench and blast marks.
    mesh.add_box(0, 0.02, -3.0, 4.4, 0.03, 3.0, "black")
    for x in (-0.4, 0.3):
        mesh.add_box(x, 0.05, -2.0, 1.6, 0.02, 0.4, "steel_dark")
    # Small service buildings.
    for x, z, sx, sz in ((5.6, -4.6, 2.2, 1.4), (-6.2, -4.4, 1.6, 1.2)):
        mesh.add_box(x, 0.55, z, sx, 1.1, sz, "panel")
        mesh.add_box(x, 1.14, z, sx + 0.12, 0.10, sz + 0.12, "steel_dark")
        mesh.add_box(x, 0.8, z + sz / 2 + 0.01, 0.5, 0.25, 0.02, "light_dim")
    return mesh


def drone_ship():
    mesh = Mesh()
    # Deck and side walls.
    mesh.add_box(0, 0, 0, 9.0, 0.35, 4.6, "steel_dark")
    mesh.add_box(0, 0.20, 0, 8.6, 0.06, 4.2, "panel")
    for side in (-1, 1):
        mesh.add_box(0, 0.35, side * 2.2, 9.0, 0.55, 0.22, "steel")
        mesh.add_box(side * 4.45, 0.32, 0, 0.22, 0.5, 4.4, "steel")
        for x in (-3.0, 0.0, 3.0):
            mesh.add_box(x, 0.52, side * 2.2, 0.6, 0.10, 0.16, "hazard")
    # Landing target.
    mesh.add_ring((0, 0.25, 0), 2.1, 2.0, 28, "accent", "y")
    mesh.add_ring((0, 0.25, 0), 0.9, 0.82, 24, "accent", "y")
    for side in (-1, 1):
        mesh.add_box(side * 1.5, 0.26, 0, 0.9, 0.02, 0.10, "accent")
        mesh.add_box(0, 0.26, side * 1.5, 0.10, 0.02, 0.9, "accent")
    # Ocean around the deck.
    mesh.add_quad([(-20, -0.8, -20), (20, -0.8, -20), (20, -0.8, 20),
                   (-20, -0.8, 20)], "planet")
    for index in range(14):
        x = -18 + index * 2.7
        z = -16 + (index * 5.1) % 32
        mesh.add_box(x, -0.72, z, 2.6, 0.04, 0.10, "hull_dark")
    # Thruster pods and cranes.
    for x in (-3.0, 3.0):
        mesh.add_box(x, -0.35, 0, 1.1, 0.60, 2.4, "black")
        mesh.add_cylinder((x, -0.85, 0), 0.35, 0.5, "y", 8, "engine")
    for x in (-4.2, 4.2):
        mesh.add_beam((x, 0.4, -2.0), (x, 1.4, -2.0), 0.10, "steel")
        mesh.add_beam((x, 1.4, -2.0), (x, 1.4, 0.4), 0.08, "steel")
    mesh.add_box(0, 0.28, 2.15, 1.4, 0.10, 0.18, "light_dim")
    return mesh


def planet():
    mesh = Mesh()
    mesh.add_sphere((0, 0, 0), 4.0, 20, 10, "planet")
    for index in range(5):
        mesh.add_torus((0, 0, 0), 4.02 - index * 0.25, 0.02, 24, 3,
                       "planet_light", "y")
    # A few brighter cloud bands.
    for index in range(3):
        mesh.add_torus((0, 0, 0), 3.99, 0.05, 28, 3, "hull_dark", "y")
    return mesh


def planet_low():
    """A cheaper planet for flight scenes, where every polygon counts."""
    mesh = Mesh()
    mesh.add_sphere((0, 0, 0), 4.0, 14, 7, "planet")
    for index in range(3):
        mesh.add_torus((0, 0, 0), 4.01 - index * 0.38, 0.025, 18, 3,
                       "planet_light", "y")
    return mesh


def shield_globe():
    """Three thin rings used as a 3D deflector-shield cue."""
    mesh = Mesh()
    for radius in (1.75, 2.05):
        mesh.add_torus((0, 0, 0), radius, 0.018, 18, 3, "accent_dark", "y")
        mesh.add_torus((0, 0, 0), radius, 0.014, 18, 3, "accent_dark", "z")
    return mesh


def flame(length=1.8, radius=0.30):
    """A bright exhaust plume pointing down from a rocket engine."""
    mesh = Mesh()
    mesh.add_frustum((0, -length / 2.0, 0), 0.02, radius, length, "y", 10,
                     "engine_hot")
    mesh.add_cone((0, -length - 0.35, 0), radius * 0.55, 0.8, "y", 8,
                  "engine", capped=True)
    return mesh


def asteroid(seed=1):
    generator = random.Random(seed)
    mesh = Mesh()
    radius = 1.0
    top = mesh.add_vertex(0, radius * generator.uniform(0.8, 1.15), 0)
    rings = []
    for ring_index in range(1, 4):
        phi = math.pi * ring_index / 4.0
        y = radius * math.cos(phi)
        ring_radius = radius * math.sin(phi)
        row = []
        count = 7
        for index in range(count):
            angle = 2 * math.pi * index / count + generator.uniform(-0.18, 0.18)
            jitter = generator.uniform(0.72, 1.22)
            row.append(mesh.add_vertex(ring_radius * math.cos(angle) * jitter,
                                       y * jitter,
                                       ring_radius * math.sin(angle) * jitter))
        rings.append(row)
    bottom = mesh.add_vertex(0, -radius * generator.uniform(0.75, 1.1), 0)
    count = len(rings[0])
    for index in range(count):
        following = (index + 1) % count
        mesh.add_face((top, rings[0][index], rings[0][following]),
                      "asteroid" if index % 2 else "asteroid_dark")
    for ring_index in range(len(rings) - 1):
        for index in range(count):
            following = (index + 1) % count
            mesh.add_face((rings[ring_index][index],
                           rings[ring_index + 1][index],
                           rings[ring_index + 1][following],
                           rings[ring_index][following]),
                          "asteroid" if (index + ring_index) % 3
                          else "asteroid_dark")
    for index in range(count):
        following = (index + 1) % count
        mesh.add_face((bottom, rings[-1][following], rings[-1][index]),
                      "asteroid_dark")
    # Craters as small inset boxes.
    for _ in range(4):
        angle = generator.uniform(0, math.pi * 2)
        height = generator.uniform(-0.45, 0.6)
        size = generator.uniform(0.12, 0.24)
        mesh.add_box(0.82 * math.cos(angle), height, 0.82 * math.sin(angle),
                     size, size * 0.4, size, "asteroid_dark")
    return mesh


SHIPS = (
    {"id": "xwing", "name": "X-WING", "mesh": xwing(), "scale": 2.15,
     "target": (0, 1.9, 0), "distance": 9.2, "zoom": 1.05,
     "class": "Incom T-65B", "role": "Space superiority",
     "crew": "1 pilot + astromech", "length": "12.5 m",
     "arms": "4 laser cannons · 2 torpedo launchers",
     "note": ("Four S-foils, four engines and an astromech socket. "
              "This is the silhouette that flies the debris run.")},
    {"id": "tie", "name": "TIE FIGHTER", "mesh": tie_fighter(), "scale": 2.35,
     "target": (0, 1.8, 0), "distance": 9.4, "zoom": 1.0,
     "class": "Sienar TIE/ln", "role": "Fleet interceptor",
     "crew": "1 pilot", "length": "8.8 m", "arms": "2 laser cannons",
     "note": ("Twin hexagonal solar arrays feed the ion engines. No shields, "
              "no hyperdrive: speed and numbers are the whole doctrine.")},
    {"id": "destroyer", "name": "STAR DESTROYER", "mesh": star_destroyer(),
     "scale": 1.55, "target": (0, 1.9, 0), "distance": 10.4, "zoom": 0.92,
     "class": "Kuat Imperial I-class", "role": "Fleet command",
     "crew": "~37,000", "length": "1,600 m",
     "arms": "Turbolasers · ion cannons · tractor beams",
     "note": ("A dagger hull built around a raised bridge and three engine "
              "banks. The wedge is the silhouette everything else hides in.")},
    {"id": "falcon9", "name": "FALCON 9", "mesh": falcon9(), "scale": 0.62,
     "target": (0, 3.8, 0), "distance": 12.0, "zoom": 1.0,
     "class": "SpaceX two-stage", "role": "Medium-lift launch",
     "crew": "Uncrewed", "length": "70 m",
     "arms": "9 Merlin engines · 4 landing legs · grid fins",
     "note": ("The full stack: octaweb, nine Merlins, landing legs, grid fins "
              "and a fairing. This is the vehicle loaded in Mission 01.")},
    {"id": "starship", "name": "STARSHIP", "mesh": starship(), "scale": 0.52,
     "target": (0, 5.0, 0), "distance": 13.5, "zoom": 1.0,
     "class": "SpaceX reusable", "role": "Heavy-lift / Mars",
     "crew": "Up to 100", "length": "50 m (ship)",
     "arms": "6 Raptor engines · steel hull · ceramic tiles",
     "note": ("Stainless steel, methane and oxygen, and a windward face made "
              "of hexagonal tiles. The upper stage is the spacecraft.")},
)

MODELS = {ship["id"]: ship["mesh"] for ship in SHIPS}

# Camera and placement metadata used by the hangar and the art panels.
_PLACEMENT = {
    "xwing": {"position": (0.0, 1.9, 0.0), "yaw": 0.55, "pitch": 0.16,
              "target": (0.0, 1.9, 0.0), "distance": 9.2},
    "tie": {"position": (0.0, 1.8, 0.0), "yaw": 0.35, "pitch": 0.10,
            "target": (0.0, 1.8, 0.0), "distance": 9.4},
    "destroyer": {"position": (0.0, 1.9, 0.0), "yaw": 0.85, "pitch": 0.28,
                  "target": (0.0, 1.9, 0.0), "distance": 10.4},
    "falcon9": {"position": (0.0, 0.0, 0.0), "yaw": 0.55, "pitch": 0.02,
                "target": (0.0, 4.0, 0.0), "distance": 12.0},
    "starship": {"position": (0.0, 0.0, 0.0), "yaw": 0.55, "pitch": 0.02,
                 "target": (0.0, 5.0, 0.0), "distance": 13.5},
}
for _ship in SHIPS:
    _ship.update(_PLACEMENT[_ship["id"]])

HANGAR = hangar()
LAUNCH_PAD = launch_pad()
DRONE_SHIP = drone_ship()
PLANET = planet()
PLANET_LOW = planet_low()
SHIELD_GLOBE = shield_globe()
FLAME = flame()
BOOSTER = booster()
ASTRONAUT = astronaut()
ASTROMECH = astromech()
ASTEROIDS = tuple(asteroid(index) for index in range(1, 9))
