"""A small software 3D engine for the flight simulator.

The engine keeps geometry and presentation separate: meshes are plain vertex
and face lists, a camera turns world space into view space, and :func:`render`
returns shaded, depth-sorted polygons that any Canvas can paint. It never
imports Tk, so the geometry can be tested on a headless machine.

Coordinate system: +X right, +Y up, +Z forward. Ships are modelled nose-forward
along +Z; rockets are modelled along +Y.
"""

import math
import random


BACKGROUND = (3, 5, 7)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, scalar):
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def normalise(vector):
    length = math.sqrt(_dot(vector, vector)) or 1.0
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def clamp(value, low=0.0, high=1.0):
    return low if value < low else high if value > high else value


def _shade_channel(value):
    return int(max(0, min(255, round(value))))


def colour(base, intensity=1.0, fog=0.0, fog_colour=BACKGROUND,
           specular=0.0):
    """Mix a material colour with light, specular and distance fog."""
    channels = []
    for index in range(3):
        value = base[index] * intensity + specular * 255.0
        value = value + (fog_colour[index] - value) * fog
        channels.append(_shade_channel(value))
    return "#{0:02X}{1:02X}{2:02X}".format(*channels)


class Material:
    """Flat-shaded material with an optional emissive component."""

    __slots__ = ("base", "specular", "gloss", "emissive")

    def __init__(self, base, specular=0.22, gloss=18.0, emissive=0.0):
        self.base = tuple(base)
        self.specular = float(specular)
        self.gloss = float(gloss)
        self.emissive = float(emissive)


MATERIALS = {
    "hull": Material((158, 169, 182), 0.30, 24),
    "hull_light": Material((206, 214, 224), 0.34, 30),
    "hull_dark": Material((78, 88, 100), 0.20, 16),
    "panel": Material((90, 102, 116), 0.18, 12),
    "panel_light": Material((122, 134, 148), 0.24, 18),
    "black": Material((25, 29, 35), 0.12, 10),
    "rubber": Material((31, 35, 40), 0.06, 6),
    "glass": Material((52, 112, 132), 0.48, 42),
    "glass_dark": Material((22, 48, 60), 0.42, 36),
    "accent": Material((255, 232, 31), 0.28, 24, 0.08),
    "accent_dark": Material((150, 128, 18), 0.18, 16),
    "yellow_dim": Material((106, 92, 22), 0.10, 10),
    "engine": Material((255, 126, 32), 0.10, 10, 0.95),
    "engine_hot": Material((255, 226, 150), 0.05, 6, 1.0),
    "engine_blue": Material((86, 180, 255), 0.10, 10, 0.90),
    "light": Material((255, 242, 186), 0.06, 8, 0.95),
    "light_dim": Material((180, 156, 82), 0.08, 10, 0.30),
    "steel": Material((94, 105, 118), 0.22, 20),
    "steel_dark": Material((52, 61, 71), 0.14, 14),
    "rust": Material((127, 78, 46), 0.12, 12),
    "floor": Material((31, 38, 46), 0.10, 10),
    "floor_grid": Material((56, 68, 82), 0.08, 8),
    "hazard": Material((200, 164, 20), 0.16, 14),
    "planet": Material((36, 77, 99), 0.22, 20),
    "planet_light": Material((64, 123, 141), 0.26, 22),
    "asteroid": Material((88, 82, 74), 0.08, 8),
    "asteroid_dark": Material((57, 53, 48), 0.06, 6),
    "suit": Material((208, 210, 204), 0.30, 22),
    "suit_shadow": Material((136, 142, 138), 0.18, 14),
    "visor": Material((28, 72, 92), 0.55, 48),
    "droid": Material((198, 200, 196), 0.32, 26),
    "droid_blue": Material((64, 126, 158), 0.38, 30),
    "droid_red": Material((190, 52, 44), 0.26, 22),
    "tile": Material((52, 55, 58), 0.14, 12),
    "tile_light": Material((86, 90, 94), 0.16, 14),
}


class Mesh:
    """Accumulates vertices and material-tagged faces."""

    __slots__ = ("vertices", "faces")

    def __init__(self):
        self.vertices = []
        self.faces = []

    def add_vertex(self, x, y, z):
        self.vertices.append((float(x), float(y), float(z)))
        return len(self.vertices) - 1

    def add_face(self, indices, material="hull"):
        if len(indices) >= 3:
            self.faces.append((tuple(indices), material))

    def add_quad(self, points, material="hull"):
        base = len(self.vertices)
        for point in points:
            self.add_vertex(*point)
        self.add_face((base, base + 1, base + 2, base + 3), material)
        return base

    def add_triangle(self, points, material="hull"):
        base = len(self.vertices)
        for point in points:
            self.add_vertex(*point)
        self.add_face((base, base + 1, base + 2), material)

    def add_box(self, cx, cy, cz, sx, sy, sz, material="hull"):
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        corners = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz),
                   (-hx, hy, -hz), (-hx, -hy, hz), (hx, -hy, hz),
                   (hx, hy, hz), (-hx, hy, hz)]
        base = len(self.vertices)
        for x, y, z in corners:
            self.add_vertex(cx + x, cy + y, cz + z)
        for quad in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                     (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.add_face([base + index for index in quad], material)
        return base

    def add_slab(self, points, y0, y1, material="hull"):
        """Extrude a convex XZ polygon between two heights."""
        base = len(self.vertices)
        for y in (y0, y1):
            for x, z in points:
                self.add_vertex(x, y, z)
        count = len(points)
        bottom = list(range(base, base + count))
        top = list(range(base + count, base + count * 2))
        self.add_face(list(reversed(bottom)), material)
        self.add_face(top, material)
        for index in range(count):
            following = (index + 1) % count
            self.add_face((bottom[index], bottom[following], top[following], top[index]),
                          material)
        return base

    def add_thick_polygon(self, points, offset, material="hull"):
        """Extrude an arbitrary 3D polygon along ``offset``."""
        half = _mul(offset, 0.5)
        base = len(self.vertices)
        count = len(points)
        for point in points:
            self.add_vertex(*(_sub(point, half)))
        for point in points:
            self.add_vertex(*(_add(point, half)))
        bottom = list(range(base, base + count))
        top = list(range(base + count, base + count * 2))
        self.add_face(list(reversed(bottom)), material)
        self.add_face(top, material)
        for index in range(count):
            following = (index + 1) % count
            self.add_face((bottom[index], bottom[following], top[following], top[index]),
                          material)
        return base

    def add_beam(self, start, end, thickness, material="steel"):
        direction = normalise(_sub(end, start))
        helper = (0.0, 1.0, 0.0)
        if abs(_dot(direction, helper)) > 0.92:
            helper = (1.0, 0.0, 0.0)
        side = normalise(_cross(direction, helper))
        up = normalise(_cross(direction, side))
        half = thickness / 2.0
        corners = []
        for anchor in (start, end):
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                corners.append(_add(anchor, _add(_mul(side, su * half),
                                                 _mul(up, sv * half))))
        base = len(self.vertices)
        for point in corners:
            self.add_vertex(*point)
        for quad in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                     (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.add_face([base + index for index in quad], material)

    def _axis_basis(self, axis):
        if axis == "x":
            return (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
        if axis == "y":
            return (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)
        return (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)

    def add_frustum(self, centre, radius_a, radius_b, length, axis="z",
                    segments=12, material="hull", caps=True):
        u, v, w = self._axis_basis(axis)
        centre = tuple(centre)
        start = _sub(centre, _mul(w, length / 2.0))
        end = _add(centre, _mul(w, length / 2.0))
        rings = []
        for radius, anchor in ((radius_a, start), (radius_b, end)):
            ring = []
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                point = _add(anchor, _add(_mul(u, radius * math.cos(angle)),
                                          _mul(v, radius * math.sin(angle))))
                ring.append(self.add_vertex(*point))
            rings.append(ring)
        for index in range(segments):
            following = (index + 1) % segments
            self.add_face((rings[0][index], rings[0][following],
                           rings[1][following], rings[1][index]), material)
        if caps:
            if radius_a > 0.001:
                self.add_face(list(reversed(rings[0])), material)
            if radius_b > 0.001:
                self.add_face(rings[1], material)
        return rings

    def add_cylinder(self, centre, radius, length, axis="z", segments=12,
                     material="hull", caps=True):
        return self.add_frustum(centre, radius, radius, length, axis,
                                segments, material, caps)

    def add_cone(self, centre, radius, length, axis="z", segments=12,
                 material="hull", capped=True):
        return self.add_frustum(centre, radius, 0.0, length, axis,
                                segments, material, capped)

    def add_sphere(self, centre, radius, segments=12, rings=6, material="hull"):
        cx, cy, cz = centre
        top = self.add_vertex(cx, cy + radius, cz)
        grid = []
        for ring in range(1, rings + 1):
            phi = math.pi * ring / (rings + 1.0)
            y = cy + radius * math.cos(phi)
            ring_radius = radius * math.sin(phi)
            row = []
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                row.append(self.add_vertex(cx + ring_radius * math.cos(angle), y,
                                           cz + ring_radius * math.sin(angle)))
            grid.append(row)
        bottom = self.add_vertex(cx, cy - radius, cz)
        for index in range(segments):
            following = (index + 1) % segments
            self.add_face((top, grid[0][index], grid[0][following]), material)
            self.add_face((bottom, grid[-1][following], grid[-1][index]), material)
        for ring in range(rings - 1):
            for index in range(segments):
                following = (index + 1) % segments
                self.add_face((grid[ring][index], grid[ring + 1][index],
                               grid[ring + 1][following], grid[ring][following]),
                              material)

    def add_torus(self, centre, major, minor, segments=18, tube=6,
                  material="accent", axis="y"):
        cx, cy, cz = centre
        u, v, w = self._axis_basis(axis)
        rings = []
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            centre_ring = _add(centre, _add(_mul(u, major * math.cos(angle)),
                                            _mul(v, major * math.sin(angle))))
            row = []
            for side in range(tube):
                phi = 2.0 * math.pi * side / tube
                point = _add(centre_ring,
                             _add(_mul(u, minor * math.cos(angle) * math.cos(phi)),
                                  _add(_mul(v, minor * math.sin(angle) * math.cos(phi)),
                                       _mul(w, minor * math.sin(phi)))))
                row.append(self.add_vertex(*point))
            rings.append(row)
        for index in range(segments):
            following = (index + 1) % segments
            for side in range(tube):
                next_side = (side + 1) % tube
                self.add_face((rings[index][side], rings[following][side],
                               rings[following][next_side], rings[index][next_side]),
                              material)

    def add_ring(self, centre, outer, inner, segments=20, material="accent",
                 axis="y"):
        u, v, _w = self._axis_basis(axis)
        centre = tuple(centre)
        rows = []
        for radius in (outer, inner):
            row = []
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                point = _add(centre, _add(_mul(u, radius * math.cos(angle)),
                                          _mul(v, radius * math.sin(angle))))
                row.append(self.add_vertex(*point))
            rows.append(row)
        for index in range(segments):
            following = (index + 1) % segments
            self.add_face((rows[0][index], rows[0][following],
                           rows[1][following], rows[1][index]), material)

    def extend(self, other):
        base = len(self.vertices)
        self.vertices.extend(other.vertices)
        for indices, material in other.faces:
            self.faces.append((tuple(base + index for index in indices), material))
        return self


class Camera:
    """Orbit camera with a perspective projection."""

    __slots__ = ("eye", "target", "right", "up", "forward", "fov")

    def __init__(self, eye=(0.0, 1.5, 9.0), target=(0.0, 0.0, 0.0),
                 up=(0.0, 1.0, 0.0), fov=0.95):
        self.eye = tuple(float(value) for value in eye)
        self.target = tuple(float(value) for value in target)
        self.fov = float(fov)
        forward = normalise(_sub(self.target, self.eye))
        right = _cross(forward, up)
        if _dot(right, right) < 1e-6:
            right = _cross(forward, (1.0, 0.0, 0.0))
        self.right = normalise(right)
        self.up = normalise(_cross(self.right, forward))
        self.forward = forward

    @classmethod
    def orbit(cls, target=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.16,
              distance=9.0):
        target = tuple(float(value) for value in target)
        cosine = math.cos(pitch)
        eye = (target[0] + distance * cosine * math.sin(yaw),
               target[1] + distance * math.sin(pitch),
               target[2] + distance * cosine * math.cos(yaw))
        return cls(eye, target)

    def view(self, point):
        delta = _sub(point, self.eye)
        return (_dot(delta, self.right), _dot(delta, self.up),
                _dot(delta, self.forward))

    def project_view(self, view_point, width, height, zoom=1.0):
        depth = view_point[2]
        if depth <= 0.12:
            return None
        focal = min(width, height) * 0.9 * self.fov * zoom
        return (width / 2.0 + view_point[0] * focal / depth,
                height / 2.0 - view_point[1] * focal / depth)

    def project(self, point, width, height, zoom=1.0):
        return self.project_view(self.view(point), width, height, zoom)


class Part:
    """A mesh placed in the world with position, rotation and scale."""

    __slots__ = ("mesh", "position", "rotation", "scale")

    def __init__(self, mesh, position=(0.0, 0.0, 0.0),
                 rotation=(0.0, 0.0, 0.0), scale=1.0):
        self.mesh = mesh
        self.position = tuple(float(value) for value in position)
        self.rotation = tuple(float(value) for value in rotation)
        self.scale = scale

    def transform(self, point):
        scale = self.scale
        if isinstance(scale, (int, float)):
            x, y, z = point[0] * scale, point[1] * scale, point[2] * scale
        else:
            x = point[0] * scale[0]
            y = point[1] * scale[1]
            z = point[2] * scale[2]
        yaw, pitch, roll = self.rotation
        if roll:
            cosine, sine = math.cos(roll), math.sin(roll)
            x, y = x * cosine - y * sine, x * sine + y * cosine
        if pitch:
            cosine, sine = math.cos(pitch), math.sin(pitch)
            y, z = y * cosine - z * sine, y * sine + z * cosine
        if yaw:
            cosine, sine = math.cos(yaw), math.sin(yaw)
            x, z = x * cosine + z * sine, -x * sine + z * cosine
        return (x + self.position[0], y + self.position[1],
                z + self.position[2])


KEY_LIGHT = normalise((-0.38, 0.72, -0.58))
FILL_LIGHT = normalise((0.68, 0.18, 0.70))
RIM_LIGHT = normalise((0.05, -0.25, -0.96))


def _clip_near(points, near=0.14):
    """Clip a view-space polygon against the near plane."""
    if not points:
        return []
    if all(point[2] >= near for point in points):
        return points
    if all(point[2] < near for point in points):
        return []
    clipped = []
    count = len(points)
    for index in range(count):
        current = points[index]
        following = points[(index + 1) % count]
        current_in = current[2] >= near
        following_in = following[2] >= near
        if current_in:
            clipped.append(current)
        if current_in != following_in:
            ratio = (near - current[2]) / (following[2] - current[2])
            clipped.append((current[0] + (following[0] - current[0]) * ratio,
                            current[1] + (following[1] - current[1]) * ratio,
                            near))
    return clipped


def render(parts, width, height, camera, zoom=1.0, fog_start=13.0,
           fog_end=30.0, fog_colour=BACKGROUND, near=0.14):
    """Return depth-sorted, shaded polygons for a list of :class:`Part`."""
    if width < 8 or height < 8:
        return []
    polygons = []
    for part in parts:
        world = [part.transform(vertex) for vertex in part.mesh.vertices]
        view = [camera.view(point) for point in world]
        for indices, material_name in part.mesh.faces:
            material = MATERIALS.get(material_name, MATERIALS["hull"])
            points = [view[index] for index in indices]
            points = _clip_near(points, near)
            if len(points) < 3:
                continue
            world_points = [world[index] for index in indices[:3]]
            edge_a = _sub(world_points[1], world_points[0])
            edge_b = _sub(world_points[2], world_points[0])
            normal = _cross(edge_a, edge_b)
            if _dot(normal, normal) < 1e-10:
                continue
            normal = normalise(normal)
            centre = _add(_add(world_points[0], world_points[1]),
                          world_points[2])
            centre = _mul(centre, 1.0 / 3.0)
            view_dir = normalise(_sub(camera.eye, centre))
            half = normalise(_add(KEY_LIGHT, view_dir))
            diffuse = abs(_dot(normal, KEY_LIGHT))
            fill = abs(_dot(normal, FILL_LIGHT))
            rim = abs(_dot(normal, RIM_LIGHT))
            facing = abs(_dot(normal, view_dir))
            intensity = 0.32 + 0.62 * diffuse + 0.24 * fill + 0.10 * rim
            if material.emissive:
                intensity = max(intensity, 0.52 + material.emissive * 0.42)
            specular = (abs(_dot(normal, half)) ** material.gloss) * material.specular
            specular *= 0.35 + 0.65 * facing
            depth = sum(point[2] for point in points) / float(len(points))
            fog = 0.0
            if fog_end > fog_start:
                fog = clamp((depth - fog_start) / (fog_end - fog_start)) * 0.86
            screen = []
            for point in points:
                projected = camera.project_view(point, width, height, zoom)
                if projected is None:
                    break
                screen.append(projected)
            if len(screen) != len(points):
                continue
            fill_colour = colour(material.base, intensity, fog, fog_colour,
                                 specular)
            outline_colour = colour(material.base,
                                    max(0.10, intensity * 0.32), fog,
                                    fog_colour, 0.0)
            polygons.append({
                "depth": depth,
                "points": screen,
                "fill": fill_colour,
                "outline": outline_colour,
                "width": 1,
                "fog": fog,
            })
    polygons.sort(key=lambda polygon: -polygon["depth"])
    return polygons


def starfield(camera, width, height, count=110, seed=7, radius=40.0,
              zoom=1.0):
    """Project a deterministic sphere of stars around the camera target."""
    if width < 8 or height < 8:
        return []
    generator = random.Random(seed)
    stars = []
    target = camera.target
    for _ in range(count * 2):
        z = generator.uniform(-1.0, 1.0)
        angle = generator.uniform(0.0, math.pi * 2.0)
        ring = math.sqrt(max(0.0, 1.0 - z * z))
        direction = (ring * math.cos(angle), z, ring * math.sin(angle))
        point = _add(target, _mul(direction, radius))
        view_point = camera.view(point)
        projected = camera.project_view(view_point, width, height, zoom)
        if projected is None:
            continue
        depth = view_point[2]
        stars.append({
            "x": projected[0],
            "y": projected[1],
            "r": 1 if depth > radius * 0.7 else 2,
            "c": "#4B5663" if depth > radius * 0.7 else "#8B96A3",
            "depth": depth,
        })
        if len(stars) >= count:
            break
    return stars


def projected_glow(camera, point, width, height, zoom=1.0):
    projected = camera.project(point, width, height, zoom)
    if projected is None:
        return None
    depth = camera.view(point)[2]
    focal = min(width, height) * 0.9 * camera.fov * zoom
    radius = max(2.0, focal / max(0.4, depth) * 0.05)
    return projected[0], projected[1], radius


def lerp(a, b, t):
    return a + (b - a) * t


def rotation_point(point, yaw=0.0, pitch=0.0, roll=0.0):
    x, y, z = point
    if roll:
        cosine, sine = math.cos(roll), math.sin(roll)
        x, y = x * cosine - y * sine, x * sine + y * cosine
    if pitch:
        cosine, sine = math.cos(pitch), math.sin(pitch)
        y, z = y * cosine - z * sine, y * sine + z * cosine
    if yaw:
        cosine, sine = math.cos(yaw), math.sin(yaw)
        x, z = x * cosine + z * sine, -x * sine + z * cosine
    return x, y, z
