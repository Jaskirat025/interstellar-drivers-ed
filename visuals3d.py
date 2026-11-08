"""3D scene painters shared by the simulator screens.

The engine renders polygons; this module owns the composition: cameras,
lighting pools, engine glows and the six scenes used by the game. It only
uses the Canvas subset that Tk and the headless test harness understand.
"""

import math

import engine3d
import fleet3d
import visuals

BG = visuals.BG
YELLOW = visuals.YELLOW
TEXT = visuals.TEXT
MUTED = visuals.MUTED

DEEP_BLUE = "#07121A"
LIGHT_POOL = "#2A2106"
WARM_GLOW = "#B98610"
HOT_GLOW = "#FFE96A"


def _paint(canvas, polygons, tag):
    for polygon in polygons:
        points = []
        for x, y in polygon["points"]:
            points.extend((x, y))
        canvas.create_polygon(points, fill=polygon["fill"],
                              outline=polygon["outline"],
                              width=polygon.get("width", 1), tags=tag)


def _clear(canvas, tag):
    canvas.delete(tag)


def _backdrop(canvas, width, height, tag):
    canvas.create_rectangle(0, 0, width, height, fill=BG, outline="", tags=tag)
    # Layered stippled ovals fake a soft, colour-graded fog without alpha.
    for scale, colour, stipple in ((1.25, "#050B10", "gray12"),
                                   (0.82, DEEP_BLUE, "gray25"),
                                   (0.42, "#0A1A24", "gray12")):
        radius = max(width, height) * scale
        canvas.create_oval(width / 2 - radius, height * 0.55 - radius * 0.7,
                           width / 2 + radius, height * 0.55 + radius * 0.7,
                           fill=colour, outline="", stipple=stipple, tags=tag)
    canvas.create_rectangle(0, 0, width, 3, fill="#101820", outline="",
                            tags=tag)
    canvas.create_rectangle(0, height - 3, width, height, fill="#101820",
                            outline="", tags=tag)


def _stars(canvas, camera, width, height, tag, count=110, seed=9, zoom=1.0):
    for star in engine3d.starfield(camera, width, height, count=count,
                                   seed=seed, radius=45.0, zoom=zoom):
        radius = star["r"]
        canvas.create_oval(star["x"] - radius, star["y"] - radius,
                           star["x"] + radius, star["y"] + radius,
                           fill=star["c"], outline="", tags=tag)


def glow(canvas, x, y, radius, tag, colour="engine"):
    """Concentric ovals read as bloom on a black Canvas."""
    radius = max(2.0, radius)
    if colour == "engine":
        layers = ((1.0, "#3A2506", "gray25"), (0.62, WARM_GLOW, "gray50"),
                  (0.34, HOT_GLOW, None))
    elif colour == "blue":
        layers = ((1.0, "#061A26", "gray25"), (0.62, "#2A88B8", "gray50"),
                  (0.34, "#B5F1FF", None))
    else:
        layers = ((1.0, "#232004", "gray25"), (0.62, YELLOW, "gray50"),
                  (0.34, "#FFFFFF", None))
    for scale, fill, stipple in layers:
        r = radius * scale
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill,
                           outline="" if stipple else fill,
                           stipple=stipple, tags=tag)


def light_pool(canvas, x, y, radius, tag, colour=LIGHT_POOL):
    for scale, stipple in ((1.0, "gray12"), (0.65, "gray25"),
                           (0.34, "gray50")):
        r = radius * scale
        canvas.create_oval(x - r, y - r * 0.30, x + r, y + r * 0.30,
                           fill=colour, outline="", stipple=stipple, tags=tag)


def hangar_camera(ship):
    return engine3d.Camera.orbit(target=ship["target"], yaw=0.015,
                                 pitch=0.10, distance=ship["distance"])


SHIP_GLOWS = {
    "xwing": (((-0.62, 0.30, -1.92), "engine", 15),
              ((0.62, 0.30, -1.92), "engine", 15),
              ((-0.62, -0.30, -1.92), "engine", 15),
              ((0.62, -0.30, -1.92), "engine", 15)),
    "tie": (((0.0, 0.10, -0.62), "blue", 16),),
    "destroyer": (((-1.15, 0.05, -3.20), "blue", 11),
                   ((0.0, 0.05, -3.20), "blue", 11),
                   ((1.15, 0.05, -3.20), "blue", 11)),
    "falcon9": (((0.0, 0.0, 0.0), "engine", 17),),
    "starship": (((0.0, 0.10, 0.0), "blue", 16),),
}


def draw_engine_glows(canvas, camera, part, ship_id, width, height, tag,
                      zoom=1.0):
    for point, colour, radius in SHIP_GLOWS.get(ship_id, ()):
        world = part.transform(point)
        projected = camera.project(world, width, height, zoom)
        if projected is None:
            continue
        depth = camera.view(world)[2]
        scale = max(0.55, min(1.7, 9.0 / max(1.0, depth)))
        glow(canvas, projected[0], projected[1], radius * scale, tag, colour)


def draw_hangar_environment(canvas, ship, width, height, tag="env"):
    """Paint the static bay, instructor and droid. Returns the camera."""
    _clear(canvas, tag)
    _backdrop(canvas, width, height, tag)
    camera = hangar_camera(ship)
    _stars(canvas, camera, width, height, tag, count=70, seed=21,
           zoom=ship["zoom"])
    parts = [
        engine3d.Part(fleet3d.HANGAR),
        engine3d.Part(fleet3d.ASTRONAUT, position=(-3.95, 0.0, 2.1),
                      rotation=(-0.35, 0.0, 0.0), scale=1.0),
        engine3d.Part(fleet3d.ASTROMECH, position=(3.55, 0.0, 2.4),
                      rotation=(0.0, 1.55, 0.0), scale=1.0),
    ]
    polygons = engine3d.render(parts, width, height, camera,
                               zoom=ship["zoom"], fog_start=15.0,
                               fog_end=32.0)
    _paint(canvas, polygons, tag)
    # Warm pools under the ceiling lamps and a wash around the platform.
    for x, z in ((-4.8, -3.5), (0.0, -3.5), (4.8, -3.5),
                 (-4.8, 1.5), (0.0, 1.5), (4.8, 1.5)):
        projected = camera.project((x, 0.02, z), width, height,
                                   ship["zoom"])
        if projected is not None:
            light_pool(canvas, projected[0], projected[1],
                       max(24, width * 0.075), tag)
    projected = camera.project((0, 0.30, 0), width, height, ship["zoom"])
    if projected is not None:
        light_pool(canvas, projected[0], projected[1],
                   max(50, width * 0.20), tag, "#3A3008")
    # Thin light shafts from the three nearest ceiling fixtures.
    for x, z in ((-4.8, -3.5), (0.0, -3.5), (4.8, -3.5)):
        top = camera.project((x, 5.9, z), width, height, ship["zoom"])
        floor = camera.project((x, 0.0, z), width, height, ship["zoom"])
        if top and floor:
            half = max(18, width * 0.045)
            canvas.create_polygon(top[0] - 6, top[1], top[0] + 6, top[1],
                                  floor[0] + half, floor[1],
                                  floor[0] - half, floor[1],
                                  fill="#2A2208", outline="",
                                  stipple="gray12", tags=tag)
    return camera


def draw_hangar_ship(canvas, ship, yaw, pitch, zoom, width, height,
                     tag="ship", elapsed=0.0, auto=True):
    _clear(canvas, tag)
    camera = hangar_camera(ship)
    position = list(ship["position"])
    position[1] += math.sin(elapsed * 1.15) * 0.035
    part = engine3d.Part(ship["mesh"], position=tuple(position),
                         rotation=(yaw, pitch, 0.0), scale=ship["scale"])
    polygons = engine3d.render([part], width, height, camera, zoom=zoom,
                               fog_start=15.0, fog_end=32.0)
    _paint(canvas, polygons, tag)
    draw_engine_glows(canvas, camera, part, ship["id"], width, height, tag,
                      zoom)
    ground = camera.project((0.0, 0.16, 0.0), width, height, zoom)
    if ground is not None:
        ring = max(22.0, min(width, height) * (0.085 if ship["id"] not in
                                               ("falcon9", "starship") else 0.11))
        canvas.create_oval(ground[0] - ring, ground[1] - ring * 0.24,
                           ground[0] + ring, ground[1] + ring * 0.24,
                           outline="#5A4A10", width=2, dash=(2, 5), tags=tag)
        canvas.create_oval(ground[0] - ring * 0.62,
                           ground[1] - ring * 0.15,
                           ground[0] + ring * 0.62,
                           ground[1] + ring * 0.15,
                           outline=YELLOW, width=1, tags=tag)
    return len(polygons)


def draw_ship_reference(canvas, ship, width, height, yaw=0.5, tag="ref"):
    _clear(canvas, tag)
    canvas.create_rectangle(0, 0, width, height, fill=BG, outline="",
                            tags=tag)
    canvas.create_line(width / 2, 6, width / 2, height - 16,
                       fill=visuals.GRID, tags=tag)
    canvas.create_line(6, height / 2, width - 6, height / 2,
                       fill=visuals.GRID, tags=tag)
    camera = engine3d.Camera.orbit(target=ship["target"], yaw=0.55,
                                   pitch=0.14, distance=ship["distance"])
    part = engine3d.Part(ship["mesh"], position=ship["position"],
                         rotation=(0.55, 0.14, 0.0), scale=ship["scale"])
    polygons = engine3d.render([part], width, height, camera,
                               zoom=ship["zoom"] * 0.82,
                               fog_start=20.0, fog_end=40.0)
    _paint(canvas, polygons, tag)
    draw_engine_glows(canvas, camera, part, ship["id"], width, height, tag,
                      ship["zoom"] * 0.82)


def draw_crew_portrait(canvas, kind, width, height, tag="portrait"):
    _clear(canvas, tag)
    canvas.create_rectangle(0, 0, width, height, fill="#04080B",
                            outline="", tags=tag)
    for scale, colour, stipple in ((1.1, "#0A1A24", "gray12"),
                                   (0.6, "#112B38", "gray25")):
        radius = max(width, height) * scale
        canvas.create_oval(width / 2 - radius, height / 2 - radius,
                           width / 2 + radius, height / 2 + radius,
                           fill=colour, outline="", stipple=stipple, tags=tag)
    if kind == "astronaut":
        camera = engine3d.Camera(eye=(0.75, 1.72, 3.55),
                                 target=(0.0, 1.34, 0.0), fov=0.9)
        part = engine3d.Part(fleet3d.ASTRONAUT)
    else:
        camera = engine3d.Camera(eye=(1.05, 1.12, 3.15),
                                 target=(0.0, 0.78, 0.0), fov=0.9)
        part = engine3d.Part(fleet3d.ASTROMECH, rotation=(0.0, 0.55, 0.0))
    polygons = engine3d.render([part], width, height, camera,
                               zoom=1.0, fog_start=20.0, fog_end=40.0)
    _paint(canvas, polygons, tag)
    canvas.create_rectangle(1, 1, width - 2, height - 2,
                            outline=visuals.GRID, tags=tag)


def draw_title(canvas, width, height, tag="art3d", elapsed=0.0):
    _clear(canvas, tag)
    _backdrop(canvas, width, height, tag)
    camera = engine3d.Camera(eye=(0.0, 2.3, 12.0),
                             target=(0.0, 1.4, 0.0), fov=0.95)
    _stars(canvas, camera, width, height, tag, count=140, seed=3)
    planet = engine3d.Part(fleet3d.PLANET_LOW, position=(7.1, 4.5, -19.0),
                           rotation=(0.4, 0.0, 0.0), scale=1.9)
    destroyer = engine3d.Part(fleet3d.MODELS["destroyer"],
                              position=(-5.0, 5.2, -9.6),
                              rotation=(0.35, 0.18, 0.08), scale=1.10)
    fighter = engine3d.Part(fleet3d.MODELS["xwing"],
                            position=(-3.4, 0.9, 1.0),
                            rotation=(0.28, 0.12, 0.10), scale=1.50)
    polygons = engine3d.render([planet, destroyer, fighter], width, height,
                               camera, zoom=1.0, fog_start=18.0, fog_end=40.0)
    _paint(canvas, polygons, tag)
    draw_engine_glows(canvas, camera, fighter, "xwing", width, height, tag)
    draw_engine_glows(canvas, camera, destroyer, "destroyer", width, height,
                      tag)
    center = camera.project((7.1, 4.5, -19.0), width, height)
    if center:
        glow(canvas, center[0], center[1], min(width, height) * 0.22, tag,
             "blue")
    # A soft atmospheric line below the title content.
    canvas.create_line(0, height * 0.88, width, height * 0.86,
                       fill="#0C1922", width=2, tags=tag)


def _shield_part(position, scale):
    return engine3d.Part(fleet3d.SHIELD_GLOBE, position=position,
                         scale=scale)


def draw_mission(canvas, index, width, height, tag="art3d"):
    _clear(canvas, tag)
    _backdrop(canvas, width, height, tag)
    if index == 0:
        camera = engine3d.Camera(eye=(8.8, 6.2, 16.0),
                                 target=(0.0, 4.1, 0.0), fov=0.95)
        _stars(canvas, camera, width, height, tag, count=65, seed=31)
        parts = [
            engine3d.Part(fleet3d.LAUNCH_PAD),
            engine3d.Part(fleet3d.MODELS["falcon9"],
                          position=(0.0, 0.30, 0.0), scale=0.92),
            engine3d.Part(fleet3d.ASTRONAUT, position=(-4.9, 0.0, 4.2),
                          rotation=(-0.2, 0.35, 0.0)),
        ]
        _paint(canvas, engine3d.render(parts, width, height, camera,
                                       fog_start=17.0, fog_end=38.0), tag)
        for x in (-3.4, 3.4):
            top = camera.project((x, 5.7, -1.5), width, height)
            floor = camera.project((x, 0.0, -1.5), width, height)
            if top and floor:
                glow(canvas, top[0], top[1], 18, tag, "yellow")
                canvas.create_line(top[0], top[1], floor[0], floor[1],
                                   fill="#1A1B0B", width=2, tags=tag)
    elif index == 1:
        camera = engine3d.Camera(eye=(7.2, 6.6, 13.6),
                                 target=(0.0, 3.6, 0.0), fov=0.95)
        _stars(canvas, camera, width, height, tag, count=80, seed=32)
        parts = [
            engine3d.Part(fleet3d.DRONE_SHIP),
            engine3d.Part(fleet3d.BOOSTER,
                          position=(0.0, 4.4, 0.0), scale=0.78),
        ]
        _paint(canvas, engine3d.render(parts, width, height, camera,
                                       fog_start=16.0, fog_end=36.0), tag)
        nozzle = camera.project((0.0, 3.9, 0.0), width, height)
        if nozzle:
            glow(canvas, nozzle[0], nozzle[1], 16, tag)
        # Rain streaks, deliberately 2D because they are weather, not vehicle.
        for offset in range(14):
            x = (offset * 97) % max(1, width)
            y = (offset * 53) % max(1, height)
            canvas.create_line(x, y, x - 6, y + 16, fill="#17232B", tags=tag)
    else:
        camera = engine3d.Camera(eye=(0.0, 2.6, 11.0),
                                 target=(0.0, 1.35, 0.0), fov=0.95)
        _stars(canvas, camera, width, height, tag, count=95, seed=33)
        parts = [
            engine3d.Part(fleet3d.PLANET_LOW, position=(8.4, 3.8, -16.0),
                          scale=1.55),
            _shield_part((0.0, 1.35, 0.0), 1.55),
            engine3d.Part(fleet3d.MODELS["xwing"],
                          position=(0.0, 1.35, 0.0),
                          rotation=(0.25, 0.10, 0.08), scale=1.65),
        ]
        for index_rock in range(5):
            angle = index_rock * 1.37
            parts.append(engine3d.Part(
                fleet3d.ASTEROIDS[index_rock],
                position=(math.cos(angle) * 3.6,
                          1.2 + math.sin(angle * 1.4) * 1.8,
                          -1.4 - index_rock * 0.55),
                rotation=(angle, angle * 0.7, 0.0),
                scale=0.32 + index_rock * 0.05))
        _paint(canvas, engine3d.render(parts, width, height, camera,
                                       fog_start=17.0, fog_end=36.0), tag)
        fighter = engine3d.Part(fleet3d.MODELS["xwing"],
                                position=(0.0, 1.35, 0.0),
                                rotation=(0.25, 0.10, 0.08), scale=1.65)
        draw_engine_glows(canvas, camera, fighter, "xwing", width, height, tag)


def draw_flight_load(canvas, load, mix, target, band, strain, width, height,
                     tag="flight3d", elapsed=0.0):
    _clear(canvas, tag)
    _backdrop(canvas, width, height, tag)
    camera = engine3d.Camera(eye=(7.4, 5.8, 15.5),
                             target=(0.0, 4.0, 0.0), fov=0.95)
    _stars(canvas, camera, width, height, tag, count=55, seed=44)
    _paint(canvas, engine3d.render([engine3d.Part(fleet3d.LAUNCH_PAD)],
                                   width, height, camera, fog_start=18.0,
                                   fog_end=42.0), tag)
    base = camera.project((0.0, 0.35, 0.0), width, height)
    if base:
        light_pool(canvas, base[0], base[1], width * 0.105, tag, "#2A2208")
    _paint(canvas, engine3d.render(
        [engine3d.Part(fleet3d.MODELS["falcon9"],
                       position=(0.0, 0.30, 0.0), scale=1.0)],
        width, height, camera, fog_start=18.0, fog_end=42.0), tag)
    if strain > 0.15:
        vent = camera.project((0.55, 6.4, 0.0), width, height)
        if vent:
            for index in range(4):
                offset = (index - 1.5) * 10
                glow(canvas, vent[0] + offset, vent[1] - index * 8,
                     12 + index * 3, tag)
    top = camera.project((0.0, 7.0, 0.0), width, height)
    if top:
        glow(canvas, top[0], top[1], 10, tag, "blue")
    for x in (-3.4, 3.4):
        beacon = camera.project((x, 5.7, -1.5), width, height)
        if beacon:
            glow(canvas, beacon[0], beacon[1], 12, tag, "yellow")
    return camera


def draw_flight_landing(canvas, alt, alt_max, x, burning, fuel, width,
                        height, tag="flight3d", elapsed=0.0):
    _clear(canvas, tag)
    _backdrop(canvas, width, height, tag)
    camera = engine3d.Camera(eye=(7.8, 6.4, 14.2),
                             target=(0.0, 3.0, 0.0), fov=0.95)
    _stars(canvas, camera, width, height, tag, count=70, seed=45)
    fraction = max(0.0, min(1.0, alt / max(1.0, alt_max)))
    height_world = 1.0 + fraction * 4.5
    x_world = max(-3.0, min(3.0, x / 280.0 * 3.0))
    parts = [engine3d.Part(fleet3d.DRONE_SHIP)]
    if burning:
        parts.append(engine3d.Part(fleet3d.FLAME,
                                   position=(x_world, height_world, 0.0),
                                   scale=0.95))
    booster = engine3d.Part(fleet3d.BOOSTER,
                            position=(x_world, height_world, 0.0),
                            rotation=(0.02, 0.12, -max(-0.16, min(0.16,
                                                                    -x_world * 0.03))),
                            scale=0.92)
    parts.append(booster)
    _paint(canvas, engine3d.render(parts, width, height, camera, zoom=1.12,
                                   fog_start=17.0, fog_end=38.0), tag)
    nozzle = camera.project((x_world, height_world - 0.05, 0.0),
                            width, height, 1.12)
    if nozzle:
        glow(canvas, nozzle[0], nozzle[1], 18 if burning else 8, tag)
    # Wind streaks are weather effects, not vehicle art.
    for index in range(5):
        y = 18 + index * 12
        length = 12 + abs(math.sin(elapsed * 0.8 + index)) * 26
        canvas.create_line(width - 24, y, width - 24 - length, y,
                           fill="#2A333A", tags=tag)
    return camera


def draw_flight_debris(canvas, ship_x, rocks, hull, max_hull, width, height,
                       tag="flight3d", elapsed=0.0):
    _clear(canvas, tag)
    _backdrop(canvas, width, height, tag)
    camera = engine3d.Camera(eye=(0.0, 2.8, 11.5),
                             target=(0.0, 1.25, 0.0), fov=0.95)
    _stars(canvas, camera, width, height, tag, count=105, seed=46)
    parts = [
        engine3d.Part(fleet3d.PLANET_LOW, position=(8.0, 3.4, -16.0),
                      scale=1.45),
        engine3d.Part(fleet3d.MODELS["xwing"],
                      position=((ship_x - 0.5) * 5.0, 1.25, 0.0),
                      rotation=(0.10, 0.05, -0.08), scale=1.28),
    ]
    if hull > 0:
        parts.append(engine3d.Part(fleet3d.SHIELD_GLOBE,
                                   position=((ship_x - 0.5) * 5.0, 1.25, 0.0),
                                   scale=1.22))
    for rock in rocks:
        world_x = (rock["x"] - 0.5) * 8.5
        world_y = (0.55 - rock["y"]) * 5.6
        world_z = -0.4 - (rock.get("r", 0.02) * 10.0)
        scale = 0.35 + rock.get("r", 0.02) * 11.0
        parts.append(engine3d.Part(fleet3d.ASTEROIDS[0],
                                   position=(world_x, world_y, world_z),
                                   rotation=(rock.get("rot", 0.0),
                                             rock.get("rot", 0.0) * 0.6, 0.0),
                                   scale=scale))
    _paint(canvas, engine3d.render(parts, width, height, camera,
                                   fog_start=16.0, fog_end=38.0), tag)
    fighter = engine3d.Part(fleet3d.MODELS["xwing"],
                            position=((ship_x - 0.5) * 5.0, 1.25, 0.0),
                            rotation=(0.10, 0.05, -0.08), scale=1.28)
    draw_engine_glows(canvas, camera, fighter, "xwing", width, height, tag)
    if hull <= 1:
        canvas.create_rectangle(2, 2, width - 2, height - 2,
                                outline=YELLOW, width=2, tags=tag)
    return camera
