"""Ship meshes, a tiny 3D projector and the hangar exam.

The meshes are hand-built from vertices and faces; :func:`build_frame`
rotates, shades, projects and depth-sorts them so Tk Canvas can paint the
result with plain polygons. This module never imports Tk, which keeps the
geometry and the exam data testable without a display.
"""

import math

MATERIALS = {
    "hull": (150, 161, 174),
    "accent": (255, 232, 31),
    "dark": (44, 53, 63),
    "glass": (96, 158, 176),
    "planet": (52, 92, 108),
    "panel": (94, 106, 120),
}

LIGHT = (-0.45, 0.72, -0.52)
CAMERA_DISTANCE = 8.2


def _normalised(vector):
    length = math.sqrt(sum(component * component for component in vector)) or 1.0
    return tuple(component / length for component in vector)


LIGHT = _normalised(LIGHT)


class Mesh:
    """Accumulates vertices and faces for one ship."""

    def __init__(self):
        self.vertices = []
        self.faces = []

    def add_vertex(self, x, y, z):
        self.vertices.append((float(x), float(y), float(z)))
        return len(self.vertices) - 1

    def add_face(self, indices, material="hull"):
        self.faces.append((tuple(indices), material))

    def add_box(self, cx, cy, cz, sx, sy, sz, material="hull", roll=0.0):
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        corners = [(-hx, -hy, -hz), (hx, -hy, -hz),
                   (hx, hy, -hz), (-hx, hy, -hz),
                   (-hx, -hy, hz), (hx, -hy, hz),
                   (hx, hy, hz), (-hx, hy, hz)]
        if roll:
            cosine, sine = math.cos(roll), math.sin(roll)
            corners = [(x * cosine - y * sine, x * sine + y * cosine, z)
                       for x, y, z in corners]
        base = len(self.vertices)
        for x, y, z in corners:
            self.vertices.append((cx + x, cy + y, cz + z))
        quads = ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                 (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0))
        for quad in quads:
            self.add_face([base + index for index in quad], material)
        return base

    def add_frustum(self, cx, cy, cz, radius_a, radius_b, length,
                    segments=10, material="hull", axis="z"):
        rings = []
        for radius, offset in ((radius_a, -length / 2.0),
                               (radius_b, length / 2.0)):
            ring = []
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                cosine, sine = math.cos(angle), math.sin(angle)
                if axis == "y":
                    point = (cx + radius * cosine, cy + offset,
                             cz + radius * sine)
                elif axis == "x":
                    point = (cx + offset, cy + radius * cosine,
                             cz + radius * sine)
                else:
                    point = (cx + radius * cosine, cy + radius * sine,
                             cz + offset)
                ring.append(self.add_vertex(*point))
            rings.append(ring)
        for index in range(segments):
            following = (index + 1) % segments
            self.add_face([rings[0][index], rings[0][following],
                           rings[1][following], rings[1][index]], material)
        self.add_face(list(reversed(rings[0])), material)
        self.add_face(rings[1], material)

    def add_cylinder(self, cx, cy, cz, radius, length, segments=10,
                     material="hull", axis="z"):
        self.add_frustum(cx, cy, cz, radius, radius, length, segments,
                         material, axis)

    def add_sphere(self, cx, cy, cz, radius, segments=10, rings=5,
                   material="hull"):
        top = self.add_vertex(cx, cy + radius, cz)
        grid = []
        for ring in range(1, rings + 1):
            phi = math.pi * ring / (rings + 1.0)
            y = cy + radius * math.cos(phi)
            ring_radius = radius * math.sin(phi)
            row = []
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                row.append(self.add_vertex(
                    cx + ring_radius * math.cos(angle), y,
                    cz + ring_radius * math.sin(angle)))
            grid.append(row)
        bottom = self.add_vertex(cx, cy - radius, cz)
        for index in range(segments):
            following = (index + 1) % segments
            self.add_face([top, grid[0][index], grid[0][following]],
                          material)
            self.add_face([bottom, grid[-1][following], grid[-1][index]],
                          material)
        for ring in range(rings - 1):
            for index in range(segments):
                following = (index + 1) % segments
                self.add_face([grid[ring][index], grid[ring + 1][index],
                               grid[ring + 1][following],
                               grid[ring][following]], material)

    def add_ring(self, cx, cy, cz, radius, thickness=0.06, segments=16,
                 material="accent", tilt=0.0):
        rows = []
        for ring_radius in (radius - thickness, radius + thickness):
            row = []
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                x = ring_radius * math.cos(angle)
                z = ring_radius * math.sin(angle)
                row.append(self.add_vertex(
                    cx + x, cy - z * math.sin(tilt),
                    cz + z * math.cos(tilt)))
            rows.append(row)
        for index in range(segments):
            following = (index + 1) % segments
            self.add_face([rows[0][index], rows[0][following],
                           rows[1][following], rows[1][index]], material)

    def freeze(self):
        return tuple(self.vertices), tuple(self.faces)


def x_wing():
    mesh = Mesh()
    mesh.add_box(0.0, 0.0, -0.1, 0.72, 0.6, 4.0, "hull")
    base = len(mesh.vertices)
    for x, y in ((-0.36, -0.29), (0.36, -0.29), (0.36, 0.29),
                 (-0.36, 0.29)):
        mesh.add_vertex(x, y, 1.9)
    tip = mesh.add_vertex(0.0, 0.0, 3.6)
    for index in range(4):
        mesh.add_face([base + index, base + (index + 1) % 4, tip], "hull")
    mesh.add_box(0.0, 0.34, 0.45, 0.46, 0.18, 1.5, "glass")
    mesh.add_box(0.0, 0.44, 0.45, 0.3, 0.1, 0.9, "dark")
    for side_x in (-1, 1):
        for side_y in (-1, 1):
            roll = side_x * side_y * 0.42
            mesh.add_box(side_x * 1.32, side_y * 0.5, -0.75,
                         2.6, 0.08, 2.4, "hull", roll)
            mesh.add_box(side_x * 0.66, side_y * 0.3, -1.5,
                         0.4, 0.4, 1.9, "hull")
            mesh.add_box(side_x * 0.66, side_y * 0.3, -2.47,
                         0.34, 0.34, 0.12, "accent")
            mesh.add_box(side_x * 2.5, side_y * 0.98, 0.6,
                         0.06, 0.06, 3.0, "hull")
            mesh.add_box(side_x * 2.5, side_y * 0.98, 2.16,
                         0.1, 0.1, 0.14, "accent")
    return mesh.freeze()


def tie_fighter():
    mesh = Mesh()
    radius = 0.92
    base = len(mesh.vertices)
    for x, y, z in ((0, radius, 0), (0, 0, -radius), (radius, 0, 0),
                    (0, 0, radius), (-radius, 0, 0), (0, -radius, 0)):
        mesh.add_vertex(x, y, z)
    for face in ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
                 (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)):
        mesh.add_face([base + index for index in face], "hull")
    mesh.add_box(0.0, 0.12, -0.86, 0.34, 0.28, 0.14, "dark")
    mesh.add_box(0.0, 0.0, 0.18, 2.55, 0.16, 0.4, "dark")
    for side in (-1, 1):
        outer = len(mesh.vertices)
        for index in range(6):
            angle = math.radians(60.0 * index)
            mesh.add_vertex(side * 1.3, 1.58 * math.cos(angle),
                            0.5 + 1.58 * math.sin(angle))
        inner = len(mesh.vertices)
        for index in range(6):
            angle = math.radians(60.0 * index)
            mesh.add_vertex(side * 1.38, 1.48 * math.cos(angle),
                            0.5 + 1.48 * math.sin(angle))
        mesh.add_face([outer + index for index in range(6)], "hull")
        mesh.add_face([inner + index for index in range(6)], "dark")
        for index in range(6):
            following = (index + 1) % 6
            mesh.add_face([outer + index, outer + following,
                           inner + following, inner + index], "hull")
    mesh.add_box(0.0, 0.0, 0.92, 0.34, 0.34, 0.14, "accent")
    return mesh.freeze()


def star_destroyer():
    mesh = Mesh()
    base = len(mesh.vertices)
    for x, y, z in ((0, 0.45, 4.4), (-2.6, 0.45, -2.6), (2.6, 0.45, -2.6),
                    (0, -0.2, 3.9), (-2.25, -0.2, -2.6),
                    (2.25, -0.2, -2.6)):
        mesh.add_vertex(x, y, z)
    mesh.add_face([base, base + 1, base + 2], "hull")
    mesh.add_face([base + 3, base + 5, base + 4], "dark")
    mesh.add_face([base, base + 3, base + 4, base + 1], "hull")
    mesh.add_face([base + 1, base + 4, base + 5, base + 2], "hull")
    mesh.add_face([base + 2, base + 5, base + 3, base], "hull")
    mesh.add_box(0.0, 0.47, 1.0, 0.34, 0.05, 4.2, "dark")
    mesh.add_box(0.0, 0.62, -1.35, 1.7, 0.5, 1.9, "hull")
    mesh.add_box(0.0, 0.84, -1.8, 1.15, 0.36, 1.2, "hull")
    mesh.add_box(0.0, 1.05, -2.05, 0.85, 0.32, 0.6, "hull")
    for side in (-1, 1):
        mesh.add_box(side * 0.44, 1.05, -2.05, 0.16, 0.16, 0.16, "accent")
    for x in (-0.95, 0.0, 0.95):
        mesh.add_box(x, 0.1, -2.62, 0.55, 0.4, 0.1, "accent")
    return mesh.freeze()


def exam_falcon9():
    mesh = Mesh()
    mesh.add_cylinder(0, 0.1, 0, 0.42, 3.6, 12, "hull", "y")
    mesh.add_cylinder(0, 2.05, 0, 0.45, 0.3, 12, "dark", "y")
    mesh.add_cylinder(0, 2.75, 0, 0.36, 1.1, 12, "hull", "y")
    mesh.add_cylinder(0, 3.65, 0, 0.52, 0.8, 12, "hull", "y")
    mesh.add_frustum(0, 4.45, 0, 0.52, 0.12, 0.8, 12, "hull", "y")
    mesh.add_frustum(0, -1.95, 0, 0.3, 0.24, 0.4, 10, "dark", "y")
    for side in (-1, 1):
        mesh.add_box(side * 0.6, -1.55, 0, 0.1, 0.95, 0.12, "dark",
                     side * 0.4)
        mesh.add_box(side * 0.55, 1.55, 0, 0.08, 0.5, 0.5, "dark")
        mesh.add_box(0, 1.55, side * 0.55, 0.5, 0.5, 0.08, "dark")
    return mesh.freeze()


def exam_tower():
    mesh = Mesh()
    for x in (-0.6, 0.6):
        for z in (-0.6, 0.6):
            mesh.add_box(x, 0.4, z, 0.12, 5.6, 0.12, "dark")
    for y in (-2.2, -1.2, -0.2, 0.8, 1.8, 2.8):
        for z in (-0.6, 0.6):
            mesh.add_box(0, y, z, 1.32, 0.08, 0.08, "hull")
        for x in (-0.6, 0.6):
            mesh.add_box(x, y, 0, 0.08, 0.08, 1.32, "hull")
    mesh.add_box(-0.95, 3.0, 0, 0.18, 0.18, 2.6, "dark")
    mesh.add_box(0.95, 3.0, 0, 0.18, 0.18, 2.6, "dark")
    mesh.add_box(0, 3.0, 0, 1.9, 0.18, 0.18, "dark")
    mesh.add_cylinder(0, 1.4, 0, 0.32, 2.6, 10, "hull", "y")
    mesh.add_frustum(0, 2.85, 0, 0.32, 0.12, 0.35, 10, "hull", "y")
    return mesh.freeze()


def exam_landing():
    mesh = Mesh()
    mesh.add_cylinder(0, 0.3, 0, 0.4, 3.4, 12, "hull", "y")
    mesh.add_frustum(0, -1.55, 0, 0.28, 0.45, 0.4, 10, "dark", "y")
    mesh.add_frustum(0, -2.45, 0, 0.6, 0.2, 1.2, 10, "accent", "y")
    for side in (-1, 1):
        mesh.add_box(side * 0.58, 1.55, 0, 0.08, 0.5, 0.5, "dark")
        mesh.add_box(side * 0.5, -1.3, 0, 0.1, 1.1, 0.12, "dark",
                     side * 0.6)
        mesh.add_box(side * 0.85, -1.9, 0, 0.22, 0.1, 0.16, "dark")
        mesh.add_box(0, 1.55, side * 0.58, 0.5, 0.5, 0.08, "dark")
    return mesh.freeze()


def exam_raptor():
    mesh = Mesh()
    mesh.add_frustum(0, -0.7, 0, 0.95, 0.32, 2.2, 12, "hull", "y")
    mesh.add_ring(0, -1.75, 0, 0.95, 0.06, 16, "accent")
    mesh.add_box(0, 0.7, 0, 0.65, 0.55, 0.65, "dark")
    for side in (-1, 1):
        mesh.add_cylinder(side * 0.48, 0.95, 0, 0.22, 0.7, 8, "hull", "y")
        mesh.add_box(side * 0.3, 0.25, 0.32, 0.1, 0.9, 0.1, "dark")
    mesh.add_box(0, 1.1, 0, 1.4, 0.12, 0.3, "dark")
    return mesh.freeze()


def exam_merlin():
    mesh = Mesh()
    mesh.add_frustum(0, -1.0, 0, 1.3, 0.3, 2.6, 14, "hull", "y")
    mesh.add_ring(0, -2.25, 0, 1.3, 0.07, 18, "accent")
    mesh.add_cylinder(0, 1.6, 0, 0.4, 1.6, 12, "hull", "y")
    mesh.add_frustum(0, 2.55, 0, 0.4, 0.15, 0.5, 10, "hull", "y")
    for side in (-1, 1):
        mesh.add_box(side * 0.32, 0.6, 0.2, 0.12, 1.4, 0.12, "dark")
    return mesh.freeze()


def exam_heavy():
    mesh = Mesh()
    for x in (-0.85, 0, 0.85):
        mesh.add_cylinder(x, 0.2, 0, 0.36, 3.2, 12, "hull", "y")
        mesh.add_frustum(x, -1.8, 0, 0.26, 0.32, 0.3, 10, "dark", "y")
        mesh.add_frustum(x, 2.15, 0, 0.36, 0.12, 0.8, 12, "hull", "y")
    mesh.add_cylinder(0, 2.9, 0, 0.34, 1.1, 12, "hull", "y")
    mesh.add_frustum(0, 3.8, 0, 0.34, 0.1, 0.7, 12, "hull", "y")
    for x in (-0.5, 0.5):
        mesh.add_box(x, 1.7, 0.2, 0.08, 0.45, 0.4, "dark")
    return mesh.freeze()


def exam_dragon_chute():
    mesh = Mesh()
    mesh.add_frustum(0, 0, 0, 0.85, 0.4, 0.8, 12, "hull", "y")
    mesh.add_cylinder(0, -0.9, 0, 0.55, 0.9, 12, "dark", "y")
    for x in (-0.75, 0, 0.75):
        mesh.add_frustum(x, 2.1, 0, 0.06, 0.75, 0.55, 10, "accent", "y")
        mesh.add_box(x * 0.5, 1.2, 0, 0.04, 1.2, 0.04, "dark")
    return mesh.freeze()


def exam_starship():
    mesh = Mesh()
    mesh.add_cylinder(0, 0.2, 0, 0.5, 4.2, 14, "hull", "y")
    mesh.add_frustum(0, 3.05, 0, 0.5, 0.08, 1.5, 14, "hull", "y")
    for side in (-1, 1):
        mesh.add_box(side * 0.62, 2.1, 0, 0.25, 0.7, 0.1, "hull",
                     side * 0.5)
        mesh.add_box(side * 0.55, -1.5, 0, 0.3, 0.6, 0.1, "hull",
                     -side * 0.4)
    mesh.add_box(0, 0.2, 0.52, 0.55, 3.4, 0.06, "dark")
    for y in (-1.2, -0.4, 0.4, 1.2):
        mesh.add_box(0, y, 0.56, 0.8, 0.18, 0.04, "dark")
    return mesh.freeze()


def exam_tiles():
    mesh = Mesh()
    mesh.add_box(0, 0, 0, 2.4, 2.8, 0.2, "dark")
    for row in range(5):
        for column in range(4):
            mesh.add_box(-0.9 + column * 0.6, -1.1 + row * 0.55,
                         0.14 + 0.05 * abs(column - 1.5),
                         0.5, 0.45, 0.1,
                         "hull" if (row + column) % 2 else "panel")
    return mesh.freeze()


def exam_earth():
    mesh = Mesh()
    mesh.add_sphere(0, 0, 0, 1.5, 12, 6, "planet")
    mesh.add_ring(0, 0, 0, 2.3, 0.04, 18, "accent", 0.5)
    for angle in (0.5, 2.7):
        mesh.add_box(2.3 * math.cos(angle),
                     -2.3 * math.sin(angle) * math.sin(0.5),
                     2.3 * math.sin(angle) * math.cos(0.5),
                     0.18, 0.18, 0.18, "hull")
    return mesh.freeze()


def exam_drone_ship():
    mesh = Mesh()
    mesh.add_box(0, 0, 0, 4.4, 0.32, 2.4, "dark")
    mesh.add_box(0, 0.22, 0, 4.0, 0.08, 2.0, "hull")
    mesh.add_ring(0, 0.3, 0, 0.7, 0.05, 16, "accent")
    for z in (-0.9, 0.9):
        mesh.add_box(0, 0.32, z, 2.2, 0.04, 0.08, "accent")
    for x in (-1.6, 1.6):
        for z in (-0.8, 0.8):
            mesh.add_box(x, -0.35, z, 0.4, 0.3, 0.4, "dark")
    mesh.add_box(-1.9, 0.75, 0, 0.35, 1.0, 0.35, "hull")
    return mesh.freeze()


def exam_starlink():
    mesh = Mesh()
    mesh.add_box(0, 0, 0, 0.9, 0.55, 0.6, "hull")
    for side in (-1, 1):
        mesh.add_box(side * 1.65, 0, 0, 2.2, 0.06, 0.95, "panel")
    mesh.add_frustum(0, -0.45, 0, 0.25, 0.12, 0.25, 8, "dark", "y")
    mesh.add_box(0, 0.36, 0, 0.5, 0.12, 0.4, "dark")
    return mesh.freeze()


def exam_grid_fin():
    mesh = Mesh()
    mesh.add_cylinder(0, 0, 0, 0.48, 2.2, 12, "hull", "y")
    mesh.add_frustum(0, 1.15, 0, 0.48, 0.16, 0.3, 12, "hull", "y")
    for side in (-1, 1):
        x = side * 0.82
        for offset in (-0.4, 0.4):
            mesh.add_box(x, 0.9, offset, 0.06, 0.9, 0.06, "dark")
            mesh.add_box(x, 0.9 + offset, 0, 0.06, 0.06, 0.86, "dark")
        for offset in (-0.15, 0.15):
            mesh.add_box(x, 0.9 + offset, 0, 0.06, 0.04, 0.86, "dark")
        z = side * 0.82
        for offset in (-0.4, 0.4):
            mesh.add_box(offset, 0.9, z, 0.06, 0.9, 0.06, "dark")
            mesh.add_box(0, 0.9 + offset, z, 0.86, 0.06, 0.06, "dark")
        for offset in (-0.15, 0.15):
            mesh.add_box(0, 0.9 + offset, z, 0.86, 0.04, 0.06, "dark")
    return mesh.freeze()


def exam_staging():
    mesh = Mesh()
    mesh.add_cylinder(0, -1.3, 0, 0.48, 2.8, 12, "hull", "y")
    mesh.add_cylinder(0, 1.95, 0, 0.44, 2.4, 12, "hull", "y")
    mesh.add_frustum(0, 3.4, 0, 0.44, 0.12, 0.8, 12, "hull", "y")
    mesh.add_frustum(0, -2.75, 0, 0.3, 0.46, 0.3, 10, "dark", "y")
    mesh.add_ring(0, 0.18, 0, 0.48, 0.05, 16, "accent")
    for side in (-1, 1):
        mesh.add_box(side * 0.3, 0.55, 0, 0.1, 0.35, 0.1, "dark")
    return mesh.freeze()


def exam_dragon_iss():
    mesh = Mesh()
    mesh.add_cylinder(0, 0, 0, 0.55, 3.0, 12, "hull", "x")
    for side in (-1, 1):
        mesh.add_box(side * 1.15, 0, 0, 0.4, 0.14, 1.5, "dark")
        for z in (-1, 1):
            mesh.add_box(side * 2.1, 0, z * 0.85, 1.6, 0.06, 1.1, "panel")
    mesh.add_frustum(2.1, 0, 0, 0.42, 0.3, 0.7, 10, "hull", "x")
    mesh.add_cylinder(2.6, 0, 0, 0.28, 0.4, 10, "dark", "x")
    return mesh.freeze()


def exam_fairing():
    mesh = Mesh()
    for side in (-1, 1):
        mesh.add_box(side * 0.55, 0.4, 0, 0.12, 2.6, 1.1, "hull",
                     side * 0.3)
    mesh.add_box(0, -1.35, 0, 1.0, 0.5, 1.0, "dark")
    mesh.add_box(0, 0.3, 0, 0.6, 0.9, 0.6, "accent")
    for side in (-1, 1):
        mesh.add_box(side * 0.45, 0.3, 0, 0.08, 0.8, 0.8, "panel")
    return mesh.freeze()


def exam_range():
    mesh = Mesh()
    mesh.add_cylinder(0, 0.2, 0, 0.32, 3.0, 12, "hull", "y")
    mesh.add_frustum(0, 1.95, 0, 0.32, 0.1, 0.6, 12, "hull", "y")
    mesh.add_frustum(0, -1.55, 0, 0.22, 0.3, 0.3, 10, "dark", "y")
    mesh.add_cylinder(0, 0.65, 0, 0.35, 0.16, 12, "accent", "y")
    for side in (-1, 1):
        mesh.add_box(side * 0.85, -1.7, 0, 0.45, 0.3, 0.45, "dark")
        mesh.add_frustum(side * 0.85, -1.3, 0, 0.32, 0.16, 0.4, 10,
                         "hull", "y")
    return mesh.freeze()


def exam_geo_sat():
    mesh = Mesh()
    mesh.add_box(0, 0, 0, 1.0, 1.3, 1.0, "hull")
    for side in (-1, 1):
        mesh.add_box(side * 1.9, 0, 0, 2.4, 0.06, 1.5, "panel")
        mesh.add_box(side * 0.8, 0, 0, 0.5, 0.1, 1.2, "dark")
    mesh.add_frustum(0, 0, 0.8, 0.65, 0.15, 0.45, 12, "accent", "z")
    mesh.add_box(0, 0.9, 0, 0.15, 0.5, 0.15, "dark")
    return mesh.freeze()


def exam_launch_arc():
    mesh = Mesh()
    mesh.add_sphere(0, -0.4, 0, 1.4, 12, 6, "planet")
    for index in range(9):
        angle = 0.1 + index * 0.17
        mesh.add_box(2.0 * math.cos(angle),
                     2.0 * math.sin(angle) - 0.5, 0,
                     0.15, 0.15, 0.15, "accent")
    mesh.add_box(2.35, 1.55, 0, 0.1, 0.6, 0.1, "hull")
    mesh.add_frustum(2.35, 1.95, 0, 0.1, 0.03, 0.25, 8, "hull", "y")
    return mesh.freeze()


def _centre(model):
    vertices, faces = model
    if not vertices:
        return model
    xs, ys, zs = zip(*vertices)
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    return tuple((x - cx, y - cy, z - cz) for x, y, z in vertices), faces


SHIPS = (
    {
        "id": "xwing",
        "name": "X-WING",
        "build": x_wing,
        "zoom": 1.16,
        "yaw": 0.55,
        "pitch": 0.18,
        "class": "Incom T-65B",
        "role": "Space superiority",
        "crew": "1 pilot + astromech",
        "length": "12.5 m",
        "arms": "4 laser cannons · 2 torpedo launchers",
        "note": ("S-foils split for combat to spread the cannons and radiators. "
                 "This silhouette flies the Mission 03 debris run."),
    },
    {
        "id": "tie",
        "name": "TIE FIGHTER",
        "build": tie_fighter,
        "zoom": 1.05,
        "yaw": 0.18,
        "pitch": 0.1,
        "class": "Sienar TIE/ln",
        "role": "Fleet interceptor",
        "crew": "1 pilot",
        "length": "8.8 m",
        "arms": "2 laser cannons",
        "note": ("Twin hexagonal solar arrays feed the ion engines. No shields, "
                 "no hyperdrive: speed and numbers are the whole doctrine."),
    },
    {
        "id": "destroyer",
        "name": "STAR DESTROYER",
        "build": star_destroyer,
        "zoom": 0.92,
        "yaw": 0.85,
        "pitch": 0.32,
        "class": "Kuat Imperial I-class",
        "role": "Fleet command",
        "crew": "~37,000",
        "length": "1,600 m",
        "arms": "Turbolasers · ion cannons · tractor beams",
        "note": ("A dagger hull built around a raised bridge and three engine "
                 "banks. The wedge is the silhouette everything else hides in."),
    },
)

MODELS = {ship["id"]: ship["build"]() for ship in SHIPS}

_EXAM_MODELS = {
    "falcon9": {"name": "FALCON 9", "mesh": exam_falcon9()},
    "tower": {"name": "LAUNCH TOWER", "mesh": exam_tower()},
    "landing": {"name": "BOOSTER", "mesh": exam_landing()},
    "raptor": {"name": "RAPTOR", "mesh": exam_raptor()},
    "merlin": {"name": "MERLIN VAC", "mesh": exam_merlin()},
    "heavy": {"name": "FALCON HEAVY", "mesh": exam_heavy()},
    "dragon_chute": {"name": "DRAGON + CHUTES", "mesh": exam_dragon_chute()},
    "tiles": {"name": "HEAT TILES", "mesh": exam_tiles()},
    "earth": {"name": "EARTH", "mesh": exam_earth()},
    "drone": {"name": "DRONE SHIP", "mesh": exam_drone_ship()},
    "starlink": {"name": "STARLINK", "mesh": exam_starlink()},
    "grid_fin": {"name": "GRID FIN", "mesh": exam_grid_fin()},
    "staging": {"name": "STAGING", "mesh": exam_staging()},
    "dragon_iss": {"name": "DRAGON / ISS", "mesh": exam_dragon_iss()},
    "fairing": {"name": "FAIRING", "mesh": exam_fairing()},
    "starship": {"name": "STARSHIP", "mesh": exam_starship()},
    "range": {"name": "RANGE SAFETY", "mesh": exam_range()},
    "geo": {"name": "GEO SAT", "mesh": exam_geo_sat()},
    "launch_arc": {"name": "LAUNCH ARC", "mesh": exam_launch_arc()},
    "xwing": {"name": "X-WING", "mesh": MODELS["xwing"]},
}

EXAM_MODELS = {
    key: {"name": entry["name"], "mesh": _centre(entry["mesh"])}
    for key, entry in _EXAM_MODELS.items()
}

QUESTION_MODEL_IDS = (
    "falcon9", "tower", "landing", "raptor", "merlin", "heavy",
    "dragon_chute", "tiles", "earth", "drone", "starlink", "grid_fin",
    "staging", "dragon_iss", "fairing", "starship", "range", "geo",
    "launch_arc", "xwing",
)

QUESTIONS = (
    {
        "question": "Which propellants power a Falcon 9 first stage?",
        "answers": ("Solid rocket fuel", "RP-1 and liquid oxygen",
                    "Liquid methane and oxygen"),
        "correct": 1,
        "explain": ("Falcon 9 burns RP-1 and liquid oxygen; Starship moves to "
                    "subcooled methane and oxygen."),
    },
    {
        "question": "How does Super Heavy return to the tower at Starbase?",
        "answers": ("A runway with landing gear", "A net on a drone ship",
                    "Chopstick arms catch it"),
        "correct": 2,
        "explain": ("Super Heavy is caught by the chopstick arms, no landing "
                    "legs required. The tower is the new drone ship."),
    },
    {
        "question": "What does a Falcon 9 booster do in a hoverslam?",
        "answers": ("Glide 10 km with no engines",
                    "Light one engine and reach zero velocity at the deck",
                    "Deploy parachutes"),
        "correct": 1,
        "explain": ("Falcon 9 lights a single Merlin for the final burn and "
                    "reaches zero velocity at the deck. Mission 02 borrows that loop."),
    },
    {
        "question": "Which combustion cycle does Raptor use?",
        "answers": ("Full-flow staged combustion", "A gas-generator cycle",
                    "A solid motor"),
        "correct": 0,
        "explain": ("Raptor runs full-flow staged combustion on methane and "
                    "oxygen, a step beyond the Merlin's gas-generator cycle."),
    },
    {
        "question": "Which engine powers the Falcon 9 second stage?",
        "answers": ("Raptor", "Merlin Vacuum", "Kestrel"),
        "correct": 1,
        "explain": ("Merlin Vacuum expands the Merlin design for the "
                    "near-vacuum of the second stage."),
    },
    {
        "question": "How many Merlin engines fire on a Falcon Heavy at liftoff?",
        "answers": ("9", "27", "33"),
        "correct": 1,
        "explain": ("Falcon Heavy is three Falcon 9 cores: 27 Merlin engines "
                    "at liftoff."),
    },
    {
        "question": "How does Crew Dragon finish its return to Earth?",
        "answers": ("Parachutes", "Retro rockets", "A runway landing"),
        "correct": 0,
        "explain": ("Crew Dragon splashes down under four main parachutes; no "
                    "runway and no powered landing."),
    },
    {
        "question": "What protects Starship's windward side during reentry?",
        "answers": ("Titanium plates", "Ablative cork",
                    "Hexagonal ceramic tiles"),
        "correct": 2,
        "explain": ("Starship is covered in hexagonal ceramic tiles that take "
                    "the reentry heat, like a beskar shell made of stone."),
    },
    {
        "question": "Where does the Kármán line sit?",
        "answers": ("400 km, the ISS orbit", "About 100 km",
                    "20 km, an airliner's ceiling"),
        "correct": 1,
        "explain": ("The Kármán line is roughly 100 km up; the ISS orbits much "
                    "higher, near 400 km."),
    },
    {
        "question": "Where do Falcon 9 boosters land at sea?",
        "answers": ("The Bahamas", "The Moon", "Autonomous drone ships"),
        "correct": 2,
        "explain": ("Boosters land on drone ships such as Of Course I Still "
                    "Love You, parked downrange."),
    },
    {
        "question": "What is Starlink?",
        "answers": ("A Mars rover", "A satellite internet constellation",
                    "A lunar lander"),
        "correct": 1,
        "explain": ("Starlink is a low-Earth-orbit constellation delivering "
                    "internet service."),
    },
    {
        "question": "What do the Falcon 9 grid fins do?",
        "answers": ("Cool the engine", "Hold the fairing",
                    "Steer the booster during descent"),
        "correct": 2,
        "explain": ("Titanium grid fins steer the booster through its descent "
                    "burn before the landing leg deploy."),
    },
    {
        "question": "Why does a rocket stage the first stage?",
        "answers": ("Shed dry mass and finish on a smaller engine",
                    "Refuel in orbit", "Slow the booster for landing"),
        "correct": 0,
        "explain": ("Staging drops the empty first stage so the upper stage can "
                    "finish the climb on a smaller engine."),
    },
    {
        "question": "Which craft carried NASA's Demo-2 crew to the ISS?",
        "answers": ("Orion", "Crew Dragon", "Starliner"),
        "correct": 1,
        "explain": ("Crew Dragon carried NASA's Demo-2 crew to the ISS in 2020, "
                    "the first crewed flight from US soil in years."),
    },
    {
        "question": "What is a Falcon 9 fairing?",
        "answers": ("The landing leg", "The interstage",
                    "A clamshell nose cone that protects the payload"),
        "correct": 2,
        "explain": ("The fairing is a clamshell nose cone that shields the "
                    "payload during ascent, then splits away."),
    },
    {
        "question": "Why does Starship use stainless steel?",
        "answers": ("It is lighter than aluminum",
                    "It keeps strength at cryogenic and reentry temperatures",
                    "It needs no heat shield"),
        "correct": 1,
        "explain": ("Stainless steel stays strong across cryogenic propellant "
                    "and reentry heat, and it is cheap to weld."),
    },
    {
        "question": "What does a flight termination system do?",
        "answers": ("Separates the fairing", "Restarts the engine",
                    "Destroys the vehicle if it leaves the safe corridor"),
        "correct": 2,
        "explain": ("The flight termination system ends the flight if the "
                    "vehicle leaves its safe corridor."),
    },
    {
        "question": "What is geostationary orbit?",
        "answers": ("About 35,786 km above the equator", "400 km", "100 km"),
        "correct": 0,
        "explain": ("At about 35,786 km the satellite matches Earth's rotation "
                    "and appears to hang over one spot."),
    },
    {
        "question": "Why does SpaceX launch east from Cape Canaveral?",
        "answers": ("To land downrange", "To avoid storms",
                    "Earth's rotation adds speed"),
        "correct": 2,
        "explain": ("Launching east lets Earth's rotation add free speed to "
                    "the rocket before it ever lights."),
    },
    {
        "question": "In this simulator, what does the Beskar decision change?",
        "answers": ("The login scopes", "How much hull the X-wing carries",
                    "The number of missions"),
        "correct": 1,
        "explain": ("The shield layout sets Mission 03's hull budget: more "
                    "plating means more impacts tolerated."),
    },
)


def _rotate(point, yaw, pitch):
    x, y, z = point
    cosine, sine = math.cos(yaw), math.sin(yaw)
    x, z = x * cosine - z * sine, x * sine + z * cosine
    cosine, sine = math.cos(pitch), math.sin(pitch)
    y, z = y * cosine - z * sine, y * sine + z * cosine
    return x, y, z


def _shade(colour, intensity):
    values = [int(max(0, min(255, channel * intensity))) for channel in colour]
    return "#{0:02X}{1:02X}{2:02X}".format(*values)


def build_frame(model, width, height, yaw=0.0, pitch=0.0, zoom=1.0):
    """Project one rotated, shaded, depth-sorted frame of ``model``."""
    if width < 20 or height < 20:
        return []
    vertices, faces = model
    focal = min(width, height) * 0.9 * zoom
    view = []
    for vertex in vertices:
        x, y, z = _rotate(vertex, yaw, pitch)
        view.append((x, y, z + CAMERA_DISTANCE))
    polygons = []
    for indices, material in faces:
        points = [view[index] for index in indices]
        depth = sum(point[2] for point in points) / float(len(points))
        ax, ay, az = points[0]
        bx, by, bz = points[1]
        cx, cy, cz = points[2]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        facing = abs((nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / length)
        base_colour = MATERIALS.get(material, MATERIALS["hull"])
        intensity = 0.32 + 0.68 * facing
        screen = []
        for x, y, z in points:
            factor = focal / max(0.35, z)
            screen.append((width / 2.0 + x * factor,
                           height / 2.0 - y * factor))
        polygons.append({
            "depth": depth,
            "points": screen,
            "fill": _shade(base_colour, intensity),
            "outline": _shade(base_colour, max(0.16, intensity * 0.45)),
        })
    polygons.sort(key=lambda polygon: -polygon["depth"])
    return polygons
