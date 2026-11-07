"""The Interstellar Driver's Ed: Rebel-SpaceX Flight Simulator.

Single-file Tkinter desktop app built for MLH Hack Week.
Auth0 and Tiger Data are simulated on this machine only: no network and
no subprocesses. The app keeps one small pilot record in the user's home
directory; nothing ever leaves the computer.
"""

import hashlib
import json
import math
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

BG = "#000000"
YELLOW = "#FFE81F"
TEXT = "#C9D1D9"
MUTED = "#8B96A3"

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")
SANS = "Helvetica Neue" if IS_MAC else ("Segoe UI" if IS_WIN else "DejaVu Sans")
MONO = "Menlo" if IS_MAC else ("Consolas" if IS_WIN else "DejaVu Sans Mono")

APP_VERSION = "1.1.0"
WINDOW_TITLE = "The Interstellar Driver's Ed · Rebel-SpaceX Flight Simulator"
FOOTER_TEXT = "v{0} · local pilot log · simulated sponsor integrations".format(APP_VERSION)
RECORD_FOLDER = ".interstellar_drivers_ed"


def fnt(size, weight="normal", mono=False):
    return (MONO if mono else SANS, size, weight)


def tracked(text):
    """Wide-spaced uppercase, used for titles and small labels."""
    return " ".join(text.upper())


class PilotStore:
    """One local JSON record. Read and write failures never block the game."""

    def __init__(self, path=None):
        if path is None:
            try:
                path = Path.home() / RECORD_FOLDER / "pilot.json"
            except Exception:
                path = Path("pilot.json")
        self.path = Path(path)
        self.best_score = 0
        self.best_rank = ""
        self.flights = 0
        self.last_callsign = ""
        self.load()

    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(raw, dict):
            return
        try:
            self.best_score = max(0, min(99999, int(raw.get("best_score", 0))))
            self.flights = max(0, min(1000000, int(raw.get("flights", 0))))
        except Exception:
            self.best_score = 0
            self.flights = 0
        callsign = raw.get("last_callsign", "")
        if isinstance(callsign, str):
            self.last_callsign = callsign[:20]
        rank = raw.get("best_rank", "")
        if isinstance(rank, str):
            self.best_rank = rank[:32]

    def record(self, score, callsign, rank):
        """Save a completed flight and return True when the score is a record."""
        self.flights += 1
        improved = score > self.best_score
        if improved:
            self.best_score = score
            self.best_rank = rank
        self.last_callsign = (callsign or "")[:20]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": APP_VERSION,
                "best_score": self.best_score,
                "best_rank": self.best_rank,
                "flights": self.flights,
                "last_callsign": self.last_callsign,
            }
            temporary = self.path.with_name(self.path.name + ".tmp")
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        except Exception:
            pass
        return improved


MISSIONS = [
    {
        "tag": "PROPELLANT LOAD",
        "title": "METHANE, OXYGEN, TIBANNA",
        "prompt": "SELECT A PROPELLANT LOAD",
        "caption": "FIG. 01 · LAUNCH STACK · PAD 39-A",
        "figure": "falcon",
        "briefing": (
            "The pad at Black Spire is clear and the launch window is nine minutes "
            "wide. SpaceX flies Falcon 9 on RP-1 and liquid oxygen; this Rebellion "
            "refit runs on subcooled liquid methane and liquid oxygen, the same choice "
            "SpaceX made for Starship. Your tanks hold both, plus a two percent "
            "Tibanna additive from Bespin. Load the stack correctly and the booster "
            "climbs. Load it wrong and the range safety officer has the final word."
        ),
        "options": [
            {
                "label": "METHANE + OXYGEN ONLY",
                "points": 45,
                "verdict": "PARTIAL",
                "text": (
                    "The nine engines light cleanly and the stack clears the tower, but "
                    "a Tibanna-free mixture sets up an injector resonance at max Q. "
                    "SpaceX trims every propellant load to the kilogram; here the "
                    "missing additive costs you 1.8 tonnes of payload margin. Orbit is "
                    "reached, with a footnote from the customer."
                ),
            },
            {
                "label": "2% TIBANNA ADDITIVE",
                "points": 100,
                "verdict": "OPTIMAL",
                "text": (
                    "A metered two percent Tibanna additive steadies combustion the way "
                    "Raptor's full-flow staged combustion keeps methane and oxygen "
                    "under control at pressure. Max Q is nominal, stage separation "
                    "lands on the second, and the satellite reaches its slot with "
                    "propellant to spare."
                ),
            },
            {
                "label": "TIBANNA-DOMINANT MIX",
                "points": -30,
                "verdict": "FAILURE",
                "text": (
                    "Tibanna is a gas from Bespin, not a bulk propellant. Chamber "
                    "pressure spikes, the engine runs rich and shuts down at T+41. The "
                    "booster falls inside the exclusion zone and the range safety "
                    "officer owns the report."
                ),
            },
        ],
    },
    {
        "tag": "AUTONOMOUS LANDING",
        "title": "KAMINO, DRONE SHIP, ONE DROID",
        "prompt": "DECIDE WHO FLIES THE BOOSTER",
        "caption": "FIG. 02 · X-WING CLASS · APPROACH VECTOR",
        "figure": "starfighter",
        "briefing": (
            "Kamino is a water world, so the landing target is a drone ship: a pitching "
            "deck with no harbour and no second attempt. SpaceX calls the manoeuvre a "
            "hoverslam, because a Falcon booster cannot hover. It lights one engine and "
            "arrives at zero velocity exactly as the legs touch. A landing droid has "
            "flown the descent from orbit and is holding at two kilometres. The deck is "
            "small, the rain is horizontal, and the droid is waiting on your call."
        ),
        "options": [
            {
                "label": "LET THE LANDING DROID FLY",
                "points": 100,
                "verdict": "OPTIMAL",
                "text": (
                    "The droid trims the grid fins through the crosswind, lights a "
                    "single engine for the landing burn and threads the hoverslam: zero "
                    "velocity at the exact moment the legs touch the deck. Four legs, no "
                    "slide. Kamino's weather service logs the cleanest landing of the "
                    "season."
                ),
            },
            {
                "label": "TAKE OVER AT TWO KILOMETRES",
                "points": 35,
                "verdict": "PARTIAL",
                "text": (
                    "You fly it down by hand and catch the deck a metre off centre. One "
                    "leg takes the whole load and the booster lists before the deck crew "
                    "can safe it. Recoverable, after a week in the hangar and a "
                    "conversation with the droid that would have been 0.4 metres "
                    "tighter."
                ),
            },
            {
                "label": "DROID OFFLINE, LAND BY EYE",
                "points": -40,
                "verdict": "FAILURE",
                "text": (
                    "Rain on the lens and no radar. The booster comes down twelve metres "
                    "wide of the deck, clips the edge and tips into the sea. SpaceX's "
                    "autonomous stack has flown this profile dozens of times; the droid, "
                    "for the record, had already filed a dissent."
                ),
            },
        ],
    },
    {
        "tag": "BESKAR SHIELDS",
        "title": "THE DEBRIS FIELD RUN",
        "prompt": "CHOOSE A SHIELD LAYOUT",
        "caption": "FIG. 03 · BESKAR LATTICE · SECTOR 7",
        "figure": "shield",
        "briefing": (
            "A shattered cruiser has seeded the approach lane with debris, and the jump "
            "point closes in ninety seconds. SpaceX solves re-entry with a heat shield, "
            "not armour: Dragon wears PICA-X, and Starship turns its belly into the "
            "plasma. The Rebellion has Beskar, which stops almost anything, on a hull "
            "that can carry almost nothing. The shield shop has enough plates for one "
            "choice, so make it count."
        ),
        "options": [
            {
                "label": "FULL BESKAR HULL",
                "points": 50,
                "verdict": "PARTIAL",
                "text": (
                    "Nothing gets through. Nothing gets through quickly either: the "
                    "extra plating costs you eighteen percent of acceleration, so you "
                    "cross the field twice instead of once and take four hits you could "
                    "have dodged. SpaceX strips every kilogram it can from the upper "
                    "stage for the same reason. Intact, and late."
                ),
            },
            {
                "label": "BESKAR ON THE LEADING EDGES",
                "points": 100,
                "verdict": "OPTIMAL",
                "text": (
                    "Layered Beskar covers the arcs the debris can actually reach, the "
                    "way Starship's tiles cover the windward face and leave the rest of "
                    "the vehicle light. Two strikes, both stopped, and the jump point "
                    "opens on your first pass with the schedule intact."
                ),
            },
            {
                "label": "NO SHIELDS, SPEED IS ARMOUR",
                "points": -20,
                "verdict": "FAILURE",
                "text": (
                    "You thread the first gap beautifully. The second one has a "
                    "fist-sized fragment moving at four kilometres a second, and it "
                    "opens the port bay. Speed is not armour; you limp to the jump point "
                    "with a hull breach and a very short report."
                ),
            },
        ],
    },
]

MAX_SCORE = sum(max(o["points"] for o in m["options"]) + 30 for m in MISSIONS)

RANKS = [
    (350, "JEDI ACE"),
    (270, "SQUADRON LEADER"),
    (190, "SENIOR PILOT"),
    (100, "FLIGHT CADET"),
    (-999, "GROUND CREW"),
]


def rank_for(score):
    for floor, name in RANKS:
        if score >= floor:
            return name
    return "GROUND CREW"


def score_text(score):
    return "SCORE {0:>4}".format(score)


def points_text(points):
    return "{0:+d} PTS".format(points)


def option_rank(mission, option):
    """0 = best decision, 1 = partial, 2 = failure; used for difficulty."""
    best = max(item["points"] for item in mission["options"])
    if option["points"] == best:
        return 0
    if option["points"] > 0:
        return 1
    return 2


def verdict_colour(verdict):
    if verdict == "OPTIMAL":
        return YELLOW
    if verdict == "PARTIAL":
        return TEXT
    return MUTED


def valid_char(ch):
    return (("a" <= ch <= "z") or ("A" <= ch <= "Z")
            or ("0" <= ch <= "9") or ch in " -_")


def validate_callsign(raw):
    """Returns (callsign, error). Empty input falls back to CADET-X."""
    text = (raw or "").strip()
    if not text:
        return "CADET-X", ""
    if len(text) > 20:
        return None, "Use 20 characters or fewer."
    for ch in text:
        if not valid_char(ch):
            return None, "Use letters, digits, spaces, hyphens or underscores only."
    return text, ""


class FlatButton(tk.Frame):
    """Flat 1px-border button. Hover inverts the palette."""

    def __init__(self, parent, app, text, command, variant="outline",
                 size=11, pady=10, padx=14):
        tk.Frame.__init__(self, parent, bg=BG, bd=0,
                          highlightthickness=1, highlightbackground=MUTED,
                          highlightcolor=MUTED)
        self.app = app
        self.variant = variant
        self.command = command
        self.enabled = True
        self.hover = False
        self.last_click = 0.0
        self.label = tk.Label(self, text=text, font=fnt(size, "bold"),
                              bg=BG, fg=YELLOW, justify="center", anchor="center")
        self.label.pack(fill="both", expand=True, padx=padx, pady=pady)
        for widget in (self, self.label):
            widget.bind("<Button-1>", app.guard(self.on_press))
            widget.bind("<Enter>", app.guard(self.on_enter))
            widget.bind("<Leave>", app.guard(self.on_leave))
        self.apply()

    def apply(self):
        if not self.enabled:
            bg, fg, border = BG, MUTED, MUTED
        elif self.variant == "primary":
            bg, fg, border = (BG, YELLOW, YELLOW) if self.hover else (YELLOW, BG, YELLOW)
        else:
            bg, fg, border = (YELLOW, BG, YELLOW) if self.hover else (BG, YELLOW, MUTED)
        self.configure(bg=bg, highlightbackground=border, highlightcolor=border)
        self.label.configure(bg=bg, fg=fg)
        try:
            cursor = "hand2" if self.enabled else "arrow"
            self.configure(cursor=cursor)
            self.label.configure(cursor=cursor)
        except tk.TclError:
            pass

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.hover = False
        self.apply()

    def on_enter(self, _event=None):
        if self.enabled and not self.hover:
            self.hover = True
            self.apply()

    def on_leave(self, event=None):
        inside = False
        if event is not None:
            try:
                under = self.winfo_containing(event.x_root, event.y_root)
            except Exception:
                under = None
            inside = under is self or under is self.label
        if not inside and self.hover:
            self.hover = False
            self.apply()

    def on_press(self, _event=None):
        if not self.enabled:
            return
        now = time.monotonic()
        if now - self.last_click < 0.25:   # ignore rapid double clicks
            return
        self.last_click = now
        if self.command is not None:
            self.command()


class ProgressBar(tk.Frame):
    def __init__(self, parent, app, height=10):
        tk.Frame.__init__(self, parent, bg=BG)
        self.app = app
        self.value = 0.0
        self.canvas = tk.Canvas(self, bg=BG, height=height, bd=0,
                                highlightthickness=1, highlightbackground=MUTED)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", app.guard(self.redraw))

    def set(self, value):
        self.value = max(0.0, min(1.0, value))
        self.redraw()

    def redraw(self, _event=None):
        c = self.canvas
        width = c.winfo_width()
        height = c.winfo_height()
        c.delete("fill")
        if width <= 6 or height <= 6:
            return
        inner = (width - 4) * self.value
        if inner >= 1:
            c.create_rectangle(2, 2, 2 + inner, height - 2,
                               fill=YELLOW, outline="", tags="fill")


class Screen(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent, bg=BG)
        self.app = app

    def g(self, fn):
        return self.app.guard(fn)


class TitleScreen(Screen):
    def __init__(self, parent, app):
        Screen.__init__(self, parent, app)
        self.width = 1
        self.height = 1
        self.fitted_width = -1
        self.stars = []
        self.title_font = tkfont.Font(family=SANS, size=54, weight="bold")

        self.canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.content = tk.Frame(self, bg=BG)
        self.content.place(relx=0.5, rely=0.47, anchor="center")

        tk.Label(self.content, text=tracked("Rebel Aerospace Academy"),
                 font=fnt(8), bg=BG, fg=MUTED).pack()
        self.title_label = tk.Label(self.content,
                                    text=tracked("The Interstellar Driver's Ed"),
                                    font=self.title_font, bg=BG, fg=YELLOW)
        self.title_label.pack(pady=(10, 8))
        tk.Label(self.content, text=tracked("Rebel-SpaceX Flight Simulator"),
                 font=fnt(9), bg=BG, fg=TEXT).pack()
        tk.Frame(self.content, bg=MUTED, height=1).pack(fill="x", pady=22)

        form = tk.Frame(self.content, bg=BG)
        form.pack()
        tk.Label(form, text=tracked("Callsign"), font=fnt(8), bg=BG, fg=MUTED,
                 anchor="w").pack(fill="x")
        self.entry = tk.Entry(form, font=fnt(12, mono=True), bg=BG, fg=YELLOW,
                              insertbackground=YELLOW, relief="flat", bd=0,
                              highlightthickness=1, highlightbackground=MUTED,
                              highlightcolor=YELLOW, width=26, justify="center")
        self.entry.pack(fill="x", pady=(6, 6), ipady=5)
        self.entry.insert(0, app.callsign or app.pilot.last_callsign or "CADET-X")
        self.hint = tk.Label(self.content,
                             text=("Letters, digits, spaces, hyphens, underscores"
                                   " · 1-20 characters"),
                             font=fnt(8), bg=BG, fg=MUTED)
        self.hint.pack()

        actions = tk.Frame(self.content, bg=BG)
        actions.pack(pady=(22, 0))
        FlatButton(actions, app, "START MISSION", self.g(self.start),
                   "primary", size=10, padx=24, pady=10).pack(side="left",
                                                              padx=(0, 10))
        FlatButton(actions, app, "QUIT", self.g(app.close),
                   "outline", size=10, padx=24, pady=10).pack(side="left")

        if app.pilot.flights:
            record = "PILOT RECORD · BEST {0:03d} · {1} FLIGHT{2}".format(
                app.pilot.best_score, app.pilot.flights,
                "" if app.pilot.flights == 1 else "S")
        else:
            record = "NO FLIGHTS LOGGED · YOUR RECORD STARTS HERE"
        tk.Label(self.content, text=record, font=fnt(8, mono=True),
                 bg=BG, fg=MUTED).pack(pady=(18, 0))

        self.canvas.bind("<Configure>", self.g(self.on_resize))
        self.entry.bind("<Return>", self.g(self.start))
        self.entry.bind("<KP_Enter>", self.g(self.start))
        self.app.schedule(60, self.tick)
        self.app.schedule(120, self.entry.focus_set)

    # -- starfield -----------------------------------------------------
    def make_star(self):
        return {
            "x": random.random(),
            "y": random.random(),
            "vx": random.uniform(-0.0005, 0.0005),
            "vy": random.uniform(0.0006, 0.0018),
            "r": random.choice((1, 1, 1, 2)),
            "c": random.choice((MUTED, MUTED, TEXT)),
        }

    def on_resize(self, event):
        self.width = max(event.width, 1)
        self.height = max(event.height, 1)
        target = int(min(150, max(45, (self.width * self.height) // 9500)))
        while len(self.stars) < target:
            self.stars.append(self.make_star())
        while len(self.stars) > target:
            self.stars.pop()
        if abs(self.width - self.fitted_width) > 16:
            self.fitted_width = self.width
            self.fit_title()
        self.draw_stars()

    def fit_title(self):
        text = tracked("The Interstellar Driver's Ed")
        limit = max(260, self.width - 150)
        size = 54
        self.title_font.configure(size=size)
        while size > 14 and self.title_font.measure(text) > limit:
            size -= 1
            self.title_font.configure(size=size)

    def draw_stars(self):
        c = self.canvas
        c.delete("star")
        if self.width < 2 or self.height < 2:
            return
        for star in self.stars:
            x = star["x"] * self.width
            y = star["y"] * self.height
            r = star["r"]
            c.create_oval(x - r, y - r, x + r, y + r,
                          fill=star["c"], outline="", tags="star")

    def tick(self):
        if not self.winfo_exists():
            return
        for star in self.stars:
            star["x"] += star["vx"]
            star["y"] += star["vy"]
            if star["y"] > 1.01:
                star["y"] = -0.01
                star["x"] = random.random()
            if star["x"] < -0.01:
                star["x"] = 1.01
            elif star["x"] > 1.01:
                star["x"] = -0.01
        self.draw_stars()
        self.app.schedule(33, self.tick)

    # -- actions -------------------------------------------------------
    def start(self, _event=None):
        callsign, error = validate_callsign(self.entry.get())
        if callsign is None:
            self.hint.configure(text=error, fg=YELLOW)
            self.entry.focus_set()
            return
        self.app.callsign = callsign
        self.app.show_auth()


class AuthScreen(Screen):
    LOG = (
        "[01] opening simulated authorization window",
        "[02] scope: openid profile flight:read",
        "[03] response_type=token · audience=rebel-academy",
        "[04] signing claims on this device · no network",
        "[05] issuing simulated credential",
        "[06] session established",
    )

    def __init__(self, parent, app):
        Screen.__init__(self, parent, app)
        self.step = 0
        self.total = 26
        self.finished = False
        self.token = ""

        holder = tk.Frame(self, bg=BG)
        holder.pack(fill="both", expand=True)
        self.card = tk.Frame(holder, bg=BG, bd=0, highlightthickness=1,
                             highlightbackground=MUTED)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72)
        inner = tk.Frame(self.card, bg=BG)
        inner.pack(fill="both", expand=True, padx=26, pady=22)

        tk.Label(inner, text=tracked("Secure link · Auth0"), font=fnt(8),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x")
        tk.Label(inner, text=tracked("Crew authentication"), font=fnt(17, "bold"),
                 bg=BG, fg=YELLOW, anchor="w").pack(fill="x", pady=(6, 10))

        self.intro = tk.Label(
            inner,
            text=("This is a simulated Auth0 login sequence. No account is created, "
                  "no data is sent, and no network connection is opened. The token "
                  "below is generated on this computer and is not a real credential."),
            font=fnt(10), bg=BG, fg=TEXT, anchor="w", justify="left", wraplength=520)
        self.intro.pack(fill="x")

        self.bar = ProgressBar(inner, app, 10)
        self.bar.pack(fill="x", pady=(18, 8))

        self.status = tk.Label(inner,
                               text="CONTACTING IDENTITY PROVIDER (SIMULATED)",
                               font=fnt(8, mono=True), bg=BG, fg=MUTED, anchor="w")
        self.status.pack(fill="x")

        self.log = tk.Label(inner, text="", font=fnt(9, mono=True), bg=BG, fg=TEXT,
                            anchor="nw", justify="left", height=6, wraplength=520)
        self.log.pack(fill="x", pady=(10, 0))

        self.token_label = tk.Label(inner, text="SIMULATED TOKEN · pending",
                                    font=fnt(8, mono=True), bg=BG, fg=MUTED,
                                    anchor="w", justify="left", wraplength=520)
        self.token_label.pack(fill="x", pady=(10, 0))

        self.continue_button = FlatButton(inner, app, "ENTER THE COCKPIT",
                                          self.g(self.proceed), "primary",
                                          size=10, padx=18, pady=8)
        self.continue_button.pack(anchor="e", pady=(18, 0))
        self.continue_button.set_enabled(False)

        self.card.bind("<Configure>", self.g(self.on_resize))
        self.app.schedule(280, self.advance)

    def on_resize(self, event):
        width = max(240, event.width - 64)
        self.intro.configure(wraplength=width)
        self.log.configure(wraplength=width)
        self.token_label.configure(wraplength=width)

    def advance(self):
        if not self.winfo_exists() or self.finished:
            return
        if self.step >= self.total:
            self.finish()
            return
        self.step += 1
        fraction = self.step / float(self.total)
        self.bar.set(fraction)
        shown = int(round(len(self.LOG) * fraction))
        if shown > 0:
            self.log.configure(text="\n".join(self.LOG[:shown]))
        if fraction < 0.35:
            self.status.configure(text="CONTACTING IDENTITY PROVIDER (SIMULATED)")
        elif fraction < 0.70:
            self.status.configure(text="EXCHANGING SIMULATED CLAIMS")
        else:
            self.status.configure(text="VERIFYING LOCAL SESSION")
        if self.step >= self.total:
            self.finish()
            return
        self.app.schedule(105, self.advance)

    def finish(self):
        if self.finished:
            return
        self.finished = True
        seed = "{0}|{1}|{2}".format(self.app.callsign, time.time(), random.random())
        self.token = "sim_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:40]
        self.bar.set(1.0)
        self.log.configure(text="\n".join(self.LOG))
        self.token_label.configure(text="SIMULATED TOKEN · " + self.token)
        self.status.configure(text="SESSION ESTABLISHED (SIMULATED)", fg=YELLOW)
        self.continue_button.set_enabled(True)

    def proceed(self):
        if not self.finished:
            return
        self.app.start_missions()


class MissionScreen(Screen):
    def __init__(self, parent, app, index):
        Screen.__init__(self, parent, app)
        self.index = index
        self.mission = MISSIONS[index]
        self.briefing = self.mission["briefing"]
        self.typed = 0
        self.ready = False
        self.locked = False
        self.overlay = None
        self.buttons = []
        self.build()
        self.art.bind("<Configure>", self.g(self.draw_art))
        self.right.bind("<Configure>", self.g(self.on_right_resize))
        self.app.schedule(240, self.type_step)

    def build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=28, pady=(16, 0))
        tk.Label(bar, text="MISSION {0:02d} / 03 · {1}".format(
            self.index + 1, self.mission["tag"]),
            font=fnt(9, "bold", mono=True), bg=BG, fg=MUTED).pack(side="left")
        self.score_label = tk.Label(bar, text=score_text(self.app.score),
                                    font=fnt(9, "bold", mono=True), bg=BG, fg=YELLOW)
        self.score_label.pack(side="right")
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=28, pady=(10, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=16)
        body.columnconfigure(0, weight=5, minsize=240)
        body.columnconfigure(1, weight=7, minsize=320)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 22))
        self.art = tk.Canvas(left, bg=BG, width=320, height=320, bd=0,
                             highlightthickness=1, highlightbackground=MUTED)
        self.art.pack(fill="both", expand=True)
        tk.Label(left, text=self.mission["caption"], font=fnt(8, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x", pady=(8, 0))

        self.right = tk.Frame(body, bg=BG)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.title_label = tk.Label(self.right, text=self.mission["title"],
                                    font=fnt(17, "bold"), bg=BG, fg=YELLOW,
                                    anchor="w", justify="left", wraplength=460)
        self.title_label.pack(fill="x")
        self.text = tk.Label(self.right, text="", font=fnt(11), bg=BG, fg=TEXT,
                             anchor="nw", justify="left", wraplength=460)
        self.text.pack(fill="both", expand=True, pady=(12, 14))
        tk.Label(self.right,
                 text=tracked(self.mission["prompt"])
                 + "\nFLY THE PROFILE · PERFORMANCE ADDS UP TO +30",
                 font=fnt(8), bg=BG, fg=MUTED, anchor="w",
                 justify="left").pack(fill="x", pady=(0, 8))
        for i, option in enumerate(self.mission["options"]):
            button = FlatButton(self.right, self.app,
                                "{0}   {1}".format(i + 1, option["label"]),
                                self.g(self.make_choice(i)), "outline",
                                size=10, pady=9, padx=12)
            button.pack(fill="x", pady=(0, 8))
            self.buttons.append(button)

    def make_choice(self, index):
        return lambda: self.choose(index)

    def on_right_resize(self, event):
        width = max(180, event.width - 2)
        self.title_label.configure(wraplength=width)
        self.text.configure(wraplength=width)

    # -- briefing ------------------------------------------------------
    def type_step(self):
        if not self.winfo_exists():
            return
        if self.typed >= len(self.briefing):
            self.finish_typing()
            return
        self.typed += 1
        self.text.configure(text=self.briefing[:self.typed])
        self.app.schedule(12, self.type_step)

    def finish_typing(self):
        self.text.configure(text=self.briefing)
        if self.ready:
            return
        self.ready = True
        for button in self.buttons:
            button.set_enabled(True)

    def on_digit(self, digit):
        if self.locked:
            return
        self.choose(int(digit) - 1)

    def choose(self, index):
        if self.locked:
            return
        if index < 0 or index >= len(self.mission["options"]):
            return
        self.locked = True
        option = self.mission["options"][index]
        self.score_label.configure(text=score_text(self.app.score))
        self.app.begin_flight(self.index, option)

    # -- line art ------------------------------------------------------
    def draw_art(self, _event=None):
        c = self.art
        c.delete("all")
        width = c.winfo_width()
        height = c.winfo_height()
        if width < 60 or height < 60:
            return
        figure = self.mission["figure"]
        if figure == "falcon":
            self.draw_falcon(c, width, height)
        elif figure == "starfighter":
            self.draw_starfighter(c, width, height)
        else:
            self.draw_shield(c, width, height)

    def draw_falcon(self, c, w, h):
        cx = w * 0.52
        top = h * 0.08
        pad = h * 0.78
        bw = min(w * 0.075, h * 0.042)
        fairing = (pad - top) * 0.22
        c.create_line(cx, h * 0.04, cx, h * 0.90, fill=MUTED, dash=(2, 6))
        c.create_polygon(cx, top,
                         cx + bw * 0.80, top + fairing * 0.55,
                         cx + bw, top + fairing,
                         cx - bw, top + fairing,
                         cx - bw * 0.80, top + fairing * 0.55,
                         fill="", outline=YELLOW, width=1)
        c.create_rectangle(cx - bw, top + fairing, cx + bw, pad,
                           outline=YELLOW, width=1)
        sep = top + fairing + (pad - top - fairing) * 0.60
        c.create_line(cx - bw, sep, cx + bw, sep, fill=YELLOW)
        c.create_line(cx - bw, sep - h * 0.02, cx - bw * 1.9, sep, fill=YELLOW)
        c.create_line(cx + bw, sep - h * 0.02, cx + bw * 1.9, sep, fill=YELLOW)
        c.create_line(cx - bw, pad - h * 0.05, cx - bw * 1.7, pad, fill=MUTED)
        c.create_line(cx + bw, pad - h * 0.05, cx + bw * 1.7, pad, fill=MUTED)
        c.create_polygon(cx - bw * 0.60, pad,
                         cx - bw * 0.45, pad + h * 0.035,
                         cx + bw * 0.45, pad + h * 0.035,
                         cx + bw * 0.60, pad,
                         fill="", outline=YELLOW)
        c.create_line(w * 0.10, pad + h * 0.035, w * 0.90, pad + h * 0.035,
                      fill=MUTED)
        c.create_line(w * 0.10, pad + h * 0.035, w * 0.10, pad + h * 0.055,
                      fill=MUTED)
        c.create_line(w * 0.90, pad + h * 0.035, w * 0.90, pad + h * 0.055,
                      fill=MUTED)
        c.create_line(w * 0.16, top, w * 0.16, pad, fill=MUTED, dash=(2, 4))
        c.create_line(w * 0.14, top, w * 0.18, top, fill=MUTED)
        c.create_line(w * 0.14, pad, w * 0.18, pad, fill=MUTED)
        c.create_text(w * 0.16, (top + pad) / 2, text="70 M", fill=MUTED,
                      font=fnt(8, mono=True), angle=90)
        c.create_text(w * 0.10, pad + h * 0.085, text="LAUNCH STACK · PAD 39-A",
                      fill=MUTED, font=fnt(8, mono=True), anchor="w")

    def draw_starfighter(self, c, w, h):
        cx = w * 0.5
        cy = h * 0.5
        nose = h * 0.14
        tail = h * 0.86
        bw = max(3.0, w * 0.025)
        span = w * 0.36
        c.create_line(cx, h * 0.04, cx, h * 0.96, fill=MUTED, dash=(2, 6))
        c.create_line(w * 0.06, cy, w * 0.94, cy, fill=MUTED, dash=(2, 6))
        c.create_polygon(cx, nose,
                         cx + bw, nose + h * 0.16,
                         cx + bw * 0.8, tail,
                         cx - bw * 0.8, tail,
                         cx - bw, nose + h * 0.16,
                         fill="", outline=YELLOW, width=1)
        for side in (-1, 1):
            c.create_polygon(cx + side * bw * 0.6, cy - h * 0.10,
                             cx + side * span, cy + h * 0.05,
                             cx + side * span * 0.86, cy + h * 0.16,
                             cx + side * bw * 0.9, cy + h * 0.08,
                             fill="", outline=YELLOW, width=1)
            ex = cx + side * span * 0.78
            ey = cy + h * 0.09
            er = max(3.0, w * 0.018)
            c.create_oval(ex - er, ey - er, ex + er, ey + er, outline=YELLOW)
            c.create_line(ex, ey - h * 0.05, ex, ey - er, fill=YELLOW)
        c.create_polygon(cx, nose + h * 0.07,
                         cx + bw * 0.6, nose + h * 0.14,
                         cx, nose + h * 0.20,
                         cx - bw * 0.6, nose + h * 0.14,
                         fill="", outline=YELLOW)
        c.create_oval(cx - bw * 0.45, cy - h * 0.015,
                      cx + bw * 0.45, cy + h * 0.015, outline=YELLOW)
        radius = min(w, h) * 0.13
        c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                      outline=MUTED, dash=(2, 5))
        c.create_text(w * 0.06, h * 0.92, text="APPROACH VECTOR · KAMINO",
                      fill=MUTED, font=fnt(8, mono=True), anchor="w")

    def draw_shield(self, c, w, h):
        cx = w * 0.5
        cy = h * 0.46
        radius = min(w * 0.30, h * 0.30)
        c.create_line(w * 0.06, cy, w * 0.94, cy, fill=MUTED, dash=(2, 6))
        c.create_line(cx, h * 0.06, cx, h * 0.88, fill=MUTED, dash=(2, 6))

        def hexagon(r):
            points = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                points.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
            return points

        c.create_polygon(hexagon(radius), fill="", outline=YELLOW, width=2)
        c.create_polygon(hexagon(radius * 0.70), fill="", outline=MUTED)
        c.create_polygon(hexagon(radius * 0.38), fill="", outline=MUTED, dash=(2, 4))
        for i in range(6):
            angle = math.radians(60 * i - 30)
            c.create_line(cx + radius * 0.70 * math.cos(angle),
                          cy + radius * 0.70 * math.sin(angle),
                          cx + radius * math.cos(angle),
                          cy + radius * math.sin(angle), fill=YELLOW)
        for deg in (15, 140, 250):
            angle = math.radians(deg)
            x0 = cx + (radius + 22) * math.cos(angle)
            y0 = cy + (radius + 22) * math.sin(angle)
            x1 = cx + (radius - 8) * math.cos(angle)
            y1 = cy + (radius - 8) * math.sin(angle)
            c.create_line(x0, y0, x1, y1, fill=YELLOW)
            c.create_line(x1 - 4, y1 - 4, x1 + 4, y1 + 4, fill=YELLOW)
            c.create_line(x1 - 4, y1 + 4, x1 + 4, y1 - 4, fill=YELLOW)
        c.create_text(w * 0.06, h * 0.92, text="BESKAR LATTICE · SECTOR 7",
                      fill=MUTED, font=fnt(8, mono=True), anchor="w")


class FlightScreen(Screen):
    """A playable flight sequence: three profiles, one physics loop."""

    MODES = ("LOAD SEQUENCE", "HOVERSLAM", "DEBRIS RUN")

    def __init__(self, parent, app, index, option):
        Screen.__init__(self, parent, app)
        self.index = index
        self.mission = MISSIONS[index]
        self.option = option
        self.rank = option_rank(self.mission, option)
        self.mode = ("load", "landing", "debris")[index]
        self.phase = "countdown"
        self.countdown = 3.0
        self.elapsed = 0.0
        self.run_time = 0.0
        self.last_tick = None
        self.done = False
        self.delivered = False
        self.paused = False
        self.success = False
        self.bonus = 0
        self.result = None
        self.end_delay = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.particles = []
        self.debris = []
        self.pause_overlay = None
        self.keys = {"up": False, "down": False, "left": False,
                     "right": False, "space": False}
        self.stars = [{"x": random.random(), "y": random.random(),
                       "r": random.choice((1, 1, 2)),
                       "c": random.choice((MUTED, MUTED, TEXT))}
                      for _ in range(72)]
        self.build()
        if self.mode == "load":
            self.setup_load()
        elif self.mode == "landing":
            self.setup_landing()
        else:
            self.setup_debris()
        self.app.schedule(30, self.tick)

    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=26, pady=(12, 0))
        left = tk.Frame(top, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="MISSION {0:02d} / 03 · {1}".format(
            self.index + 1, self.mission["tag"]), font=fnt(8, mono=True),
            bg=BG, fg=MUTED, anchor="w").pack(anchor="w")
        self.phase_label = tk.Label(left, text=tracked("Pre-flight"), font=fnt(8),
                                    bg=BG, fg=MUTED, anchor="w")
        self.phase_label.pack(anchor="w", pady=(2, 0))
        right = tk.Frame(top, bg=BG)
        right.pack(side="right")
        self.clock_label = tk.Label(right, text="T-03.0", font=fnt(10, "bold", mono=True),
                                    bg=BG, fg=YELLOW)
        self.clock_label.pack(side="left", padx=(0, 10))
        FlatButton(right, self.app, "PAUSE", self.g(self.toggle_pause),
                   "outline", size=8, padx=10, pady=5).pack(side="left")
        self.profile_label = tk.Label(
            self, text="PROFILE · " + self.option["label"], font=fnt(8, mono=True),
            bg=BG, fg=MUTED, anchor="w")
        self.profile_label.pack(fill="x", padx=26, pady=(4, 0))
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=26, pady=(8, 0))
        self.canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=26)
        self.canvas.bind("<Configure>", self.g(self.draw))
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=26, pady=(4, 10))
        if self.mode == "load":
            hint = "↑ / ↓  TRIM MIXTURE  ·  HOLD THE BAND  ·  P PAUSE"
        elif self.mode == "landing":
            hint = "SPACE / ↑  LANDING BURN  ·  ← →  RCS  ·  P PAUSE"
        else:
            hint = "← →  STEER  ·  AVOID THE DEBRIS  ·  P PAUSE"
        self.hint = tk.Label(bottom, text=hint, font=fnt(8, mono=True),
                             bg=BG, fg=MUTED, anchor="w")
        self.hint.pack(side="left")
        self.status = tk.Label(bottom, text="", font=fnt(8, mono=True),
                               bg=BG, fg=MUTED, anchor="e")
        self.status.pack(side="right")

    # -- input ---------------------------------------------------------
    def on_key(self, name, pressed):
        if name == "pause":
            if pressed:
                self.toggle_pause()
            return
        if name in self.keys:
            self.keys[name] = bool(pressed)

    def clear_keys(self):
        for name in self.keys:
            self.keys[name] = False

    def toggle_pause(self):
        if self.phase == "ending" or self.delivered:
            return
        self.paused = not self.paused
        self.clear_keys()
        if self.paused:
            self.show_pause()
        else:
            self.hide_pause()

    def show_pause(self):
        self.pause_overlay = tk.Frame(self, bg=BG)
        self.pause_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.pause_overlay.lift()
        card = tk.Frame(self.pause_overlay, bg=BG, highlightthickness=1,
                        highlightbackground=YELLOW)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.5)
        inner = tk.Frame(card, bg=BG)
        inner.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(inner, text=tracked("Simulation held"), font=fnt(16, "bold"),
                 bg=BG, fg=YELLOW).pack()
        tk.Label(inner, text="Flight controls are frozen. Resume when ready.",
                 font=fnt(9), bg=BG, fg=MUTED, wraplength=340,
                 justify="center").pack(pady=(8, 14))
        FlatButton(inner, self.app, "RESUME FLIGHT", self.g(self.toggle_pause),
                   "primary", size=10, padx=16, pady=8).pack(fill="x")
        FlatButton(inner, self.app, "RESTART FLIGHT",
                   self.g(lambda: self.app.begin_flight(self.index, self.option)),
                   "outline", size=9, padx=16, pady=7).pack(fill="x", pady=(8, 0))
        FlatButton(inner, self.app, "ABORT TO TITLE",
                   self.g(self.app.abort_flight), "outline", size=9,
                   padx=16, pady=7).pack(fill="x", pady=(8, 0))

    def hide_pause(self):
        if self.pause_overlay is not None:
            try:
                self.pause_overlay.destroy()
            except Exception:
                pass
            self.pause_overlay = None

    # -- clock ---------------------------------------------------------
    def tick(self):
        if not self.winfo_exists():
            return
        now = time.monotonic()
        dt = 0.03 if self.last_tick is None else min(0.06, max(0.001, now - self.last_tick))
        self.last_tick = now
        if not self.paused:
            if self.phase == "countdown":
                self.countdown -= dt
                if self.countdown <= 0:
                    self.countdown = 0.0
                    self.phase = "flying"
            elif self.phase == "flying":
                self.elapsed += dt
                if self.mode == "load":
                    self.step_load(dt)
                elif self.mode == "landing":
                    self.step_landing(dt)
                else:
                    self.step_debris(dt)
            if self.phase == "ending":
                self.end_delay -= dt
                self.shake = max(0.0, self.shake - dt * 26.0)
                if self.end_delay <= 0 and not self.delivered:
                    self.delivered = True
                    self.app.complete_flight(self.index, self.option, self.result)
                    return
            self.update_particles(dt)
            self.flash = max(0.0, self.flash - dt * 3.0)
        self.update_hud()
        self.draw()
        if not self.delivered:
            self.app.schedule(30 if not self.paused else 120, self.tick)

    def update_hud(self):
        if self.phase == "countdown":
            self.clock_label.configure(text="T-{0:03.1f}".format(max(0.0, self.countdown)))
            label = "PRE-FLIGHT"
        elif self.phase == "ending":
            self.clock_label.configure(text="T+{0:04.1f}".format(self.elapsed))
            label = "DEBRIEF"
        else:
            self.clock_label.configure(text="T+{0:04.1f}".format(self.elapsed))
            label = "FLIGHT ACTIVE · " + self.MODES[self.index]
        self.phase_label.configure(text=tracked(label))
        if self.phase == "countdown":
            self.status.configure(text="READ THE CONTROLS")
        elif self.mode == "load":
            stable = self.in_time / max(0.001, self.run_time) * 100.0
            self.status.configure(text="LOAD {0:03.0f}% · STABILITY {1:03.0f}%".format(
                self.load, stable))
        elif self.mode == "landing":
            self.status.configure(text="V/S {0:+.1f} M/S · FUEL {1:03.0f}%".format(
                self.vy, self.fuel))
        else:
            self.status.configure(text="HULL {0}/{1} · CLOSE {2}".format(
                self.hull, self.max_hull, self.close_calls))

    def finish(self, success, bonus, stats, title):
        if self.phase == "ending":
            return
        self.success = bool(success)
        self.bonus = max(0, min(30, int(bonus)))
        self.result = {"success": self.success, "bonus": self.bonus,
                       "stats": stats, "title": title}
        self.phase = "ending"
        self.end_delay = 1.1 if success else 1.5
        self.flash = 0.45 if success else 0.0
        if not success:
            self.shake = 14.0
            self.spawn_burst(0.5, 0.78, 22)

    def begin_now(self):
        self.countdown = 0.0
        self.phase = "flying"

    # -- particles -----------------------------------------------------
    def spawn_burst(self, x, y, count=14):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.05, 0.32)
            life = random.uniform(0.35, 0.95)
            self.particles.append({"x": x, "y": y,
                                   "vx": math.cos(angle) * speed,
                                   "vy": math.sin(angle) * speed - 0.05,
                                   "life": life, "max": life,
                                   "c": random.choice((YELLOW, TEXT, MUTED))})
        self.particles = self.particles[-180:]

    def update_particles(self, dt):
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 0.2 * dt
            alive.append(p)
        self.particles = alive

    def draw_particles(self, c, w, h):
        for p in self.particles:
            r = 1 + 2 * (p["life"] / p["max"])
            x, y = p["x"] * w, p["y"] * h
            c.create_oval(x - r, y - r, x + r, y + r, fill=p["c"], outline="")

    # -- load profile --------------------------------------------------
    def setup_load(self):
        self.band = (16.0, 12.0, 9.0)[self.rank]
        self.load_rate = (8.0, 6.4, 5.1)[self.rank]
        self.target_speed = (0.52, 0.68, 0.86)[self.rank]
        self.mix = 50.0
        self.target = 50.0
        self.load = 0.0
        self.in_time = 0.0
        self.strain = 0.0

    def step_load(self, dt):
        self.run_time += dt
        t = self.run_time
        self.target = 50.0 + 30.0 * math.sin(t * self.target_speed) + 7.0 * math.sin(t * 2.2 + 0.6)
        self.target = max(6.0, min(94.0, self.target))
        if self.keys["up"]:
            self.mix += 52.0 * dt
        if self.keys["down"]:
            self.mix -= 52.0 * dt
        self.mix = max(0.0, min(100.0, self.mix))
        error = abs(self.mix - self.target)
        stable = error <= self.band
        if stable:
            self.load += self.load_rate * dt
            self.in_time += dt
        else:
            self.load += 1.0 * dt
        self.load = min(100.0, self.load)
        if error > self.band * 2.0:
            self.strain += dt
        else:
            self.strain = max(0.0, self.strain - dt * 0.7)
        if self.strain >= 3.0:
            self.finish(False, 0, {"mode": "load", "stability": 0.0,
                                   "load": self.load}, "PAD ABORT")
        elif self.load >= 100.0:
            ratio = self.in_time / max(0.001, self.run_time)
            self.finish(True, int(round(ratio * 30.0)),
                        {"mode": "load", "stability": ratio * 100.0,
                         "load": self.load}, "LOAD COMPLETE")
        elif self.run_time >= 20.0:
            ratio = self.in_time / max(0.001, self.run_time)
            self.finish(False, 0, {"mode": "load", "stability": ratio * 100.0,
                                   "load": self.load}, "PAD ABORT")

    # -- landing profile -----------------------------------------------
    def setup_landing(self):
        self.alt_max = 850.0
        self.alt = (700.0, 760.0, 820.0)[self.rank]
        self.vy = -(32.0 + 4.0 * self.rank)
        self.x = random.uniform(-80.0, 80.0)
        self.vx = random.uniform(-3.0, 3.0)
        self.fuel = (100.0, 88.0, 76.0)[self.rank]
        self.wind_strength = (1.2, 2.0, 3.0)[self.rank]
        self.target_half = (34.0, 27.0, 21.0)[self.rank]
        self.burning = False

    def step_landing(self, dt):
        self.run_time += dt
        self.burning = (self.keys["space"] or self.keys["up"]) and self.fuel > 0
        if self.burning:
            self.vy += 12.5 * dt
            self.fuel = max(0.0, self.fuel - 7.0 * dt)
        self.vy -= 3.8 * dt
        self.vx += self.wind_strength * 0.45 * dt * math.sin(self.run_time * 0.85 + 0.5)
        if self.keys["left"]:
            self.vx -= 18.0 * dt
        if self.keys["right"]:
            self.vx += 18.0 * dt
        self.vx *= max(0.0, 1.0 - 0.35 * dt)
        self.alt += self.vy * dt
        self.x += self.vx * dt
        if abs(self.x) > 280.0:
            self.x = math.copysign(280.0, self.x)
            self.vx *= -0.25
        if self.alt <= 0.0:
            self.alt = 0.0
            speed = abs(self.vy)
            miss = abs(self.x)
            if speed > 9.5 or miss > self.target_half + 16.0:
                self.finish(False, 0, {"mode": "landing", "speed": speed,
                                       "miss": miss, "fuel": self.fuel},
                            "VEHICLE LOST")
            else:
                points = 10 if miss <= self.target_half * 0.35 else (7 if miss <= self.target_half else 4)
                points += 10 if speed <= 3.0 else (7 if speed <= 5.0 else (4 if speed <= 7.5 else 2))
                points += 10 if self.fuel >= 30.0 else (6 if self.fuel >= 15.0 else (3 if self.fuel > 0 else 0))
                self.finish(True, min(30, points),
                            {"mode": "landing", "speed": speed, "miss": miss,
                             "fuel": self.fuel}, "TOUCHDOWN")
        elif self.run_time > 45.0:
            self.finish(False, 0, {"mode": "landing", "speed": abs(self.vy),
                                   "miss": abs(self.x), "fuel": self.fuel},
                        "VEHICLE LOST")

    # -- debris profile ------------------------------------------------
    def setup_debris(self):
        self.max_hull = (4, 3, 2)[self.rank]
        self.hull = self.max_hull
        self.ship_x = 0.5
        self.ship_vx = 0.0
        self.spawn_timer = 0.5
        self.spawn_interval = (0.72, 0.58, 0.46)[self.rank]
        self.fall_speed = (0.20, 0.26, 0.32)[self.rank]
        self.close_calls = 0
        self.hit_cooldown = 0.0

    def step_debris(self, dt):
        self.run_time += dt
        if self.keys["left"]:
            self.ship_vx -= 1.7 * dt
        if self.keys["right"]:
            self.ship_vx += 1.7 * dt
        self.ship_vx *= max(0.0, 1.0 - 2.0 * dt)
        self.ship_x += self.ship_vx * dt
        if self.ship_x < 0.07:
            self.ship_x = 0.07
            self.ship_vx = 0.0
        elif self.ship_x > 0.93:
            self.ship_x = 0.93
            self.ship_vx = 0.0
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_debris()
            self.spawn_timer = self.spawn_interval * random.uniform(0.78, 1.22)
        self.hit_cooldown = max(0.0, self.hit_cooldown - dt)
        for rock in list(self.debris):
            rock["y"] += rock["vy"] * dt
            rock["rot"] += rock["spin"] * dt
            dx = (rock["x"] - self.ship_x) * 1.6
            dy = rock["y"] - 0.88
            if math.hypot(dx, dy) < rock["r"] + 0.05 and self.hit_cooldown <= 0:
                self.debris.remove(rock)
                self.hull -= 1
                self.hit_cooldown = 0.6
                self.shake = 8.0
                self.flash = 0.25
                self.spawn_burst(self.ship_x, 0.88, 12)
                if self.hull <= 0:
                    self.finish(False, 0, {"mode": "debris", "hull": 0,
                                           "max_hull": self.max_hull,
                                           "close": self.close_calls},
                                "HULL BREACH")
                    return
                continue
            if not rock.get("counted") and rock["y"] > 0.88 and abs(dx) < 0.16:
                rock["counted"] = True
                self.close_calls += 1
            if rock["y"] > 1.1:
                self.debris.remove(rock)
        if self.run_time >= 20.0:
            self.finish(True, min(30, self.hull * 7 + min(6, self.close_calls)),
                        {"mode": "debris", "hull": self.hull,
                         "max_hull": self.max_hull,
                         "close": self.close_calls}, "JUMP POINT CLEARED")

    def spawn_debris(self):
        radius = random.uniform(0.012, 0.026)
        self.debris.append({"x": random.uniform(0.08, 0.92), "y": -0.04,
                            "vy": self.fall_speed * random.uniform(0.85, 1.25),
                            "r": radius, "rot": random.uniform(0, 6.28),
                            "spin": random.uniform(-2.2, 2.2),
                            "c": random.choice((YELLOW, TEXT, MUTED)),
                            "counted": False})

    # -- rendering -----------------------------------------------------
    def draw(self, _event=None):
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        c.delete("all")
        if w < 120 or h < 120:
            return
        c.create_rectangle(0, 0, w, h, fill=BG, outline="")
        drift = (self.elapsed * 0.004) % 1.0
        for star in self.stars:
            x = star["x"] * w
            y = ((star["y"] + drift) % 1.0) * h
            r = star["r"]
            c.create_oval(x - r, y - r, x + r, y + r, fill=star["c"], outline="")
        if self.mode == "load":
            self.draw_load(c, w, h)
        elif self.mode == "landing":
            self.draw_landing(c, w, h)
        else:
            self.draw_debris(c, w, h)
        self.draw_particles(c, w, h)
        if self.phase == "countdown":
            number = max(1, int(math.ceil(self.countdown)))
            c.create_rectangle(w / 2 - 64, h / 2 - 74, w / 2 + 64, h / 2 + 66,
                               fill=BG, outline=YELLOW)
            c.create_text(w / 2, h / 2 - 14, text=str(number),
                          fill=YELLOW, font=fnt(38, "bold", mono=True))
            c.create_text(w / 2, h / 2 + 40, text=tracked("Flight controls"),
                          fill=MUTED, font=fnt(8))
        if self.phase == "ending" and self.result is not None:
            colour = YELLOW if self.success else MUTED
            c.create_rectangle(w * 0.22, h * 0.38, w * 0.78, h * 0.62,
                               fill=BG, outline=colour)
            c.create_text(w / 2, h * 0.45, text=tracked(self.result["title"]),
                          fill=colour, font=fnt(15, "bold"))
            c.create_text(w / 2, h * 0.53,
                          text="PERFORMANCE +{0:02d} · DEBRIEF".format(self.bonus),
                          fill=TEXT, font=fnt(8, mono=True))
        if self.shake > 0.2:
            c.move("all", random.uniform(-self.shake, self.shake),
                   random.uniform(-self.shake, self.shake))
        if self.flash > 0:
            c.create_rectangle(2, 2, w - 2, h - 2, outline=YELLOW, width=2)

    def draw_load(self, c, w, h):
        top, bottom = h * 0.18, h * 0.82
        tank_x = w * 0.14
        tank_w = min(92, w * 0.11)
        c.create_text(tank_x, top - 18, text="METHALOX TANK", anchor="w",
                      fill=MUTED, font=fnt(8, mono=True))
        c.create_rectangle(tank_x, top, tank_x + tank_w, bottom, outline=MUTED)
        fill_y = bottom - (bottom - top) * (self.load / 100.0)
        c.create_rectangle(tank_x + 2, fill_y, tank_x + tank_w - 2, bottom - 2,
                           fill=YELLOW, outline="")
        for i in range(1, 5):
            y = top + (bottom - top) * i / 5.0
            c.create_line(tank_x, y, tank_x + tank_w, y, fill=BG if y >= fill_y else MUTED)
        c.create_text(tank_x + tank_w / 2, bottom - 14,
                      text="{0:03.0f}% LOAD".format(self.load),
                      fill=BG if self.load > 6 else YELLOW,
                      font=fnt(9, "bold", mono=True))
        gx = w * 0.50
        c.create_text(gx, top - 18, text="MIXTURE VALVE", fill=MUTED, font=fnt(8, mono=True))
        c.create_rectangle(gx - 24, top, gx + 24, bottom, outline=MUTED)
        y_target = bottom - (bottom - top) * self.target / 100.0
        y_hi = bottom - (bottom - top) * min(100.0, self.target + self.band) / 100.0
        y_lo = bottom - (bottom - top) * max(0.0, self.target - self.band) / 100.0
        c.create_rectangle(gx - 24, y_hi, gx + 24, y_lo, outline=YELLOW, dash=(2, 3))
        y_mix = bottom - (bottom - top) * self.mix / 100.0
        c.create_line(gx - 34, y_mix, gx + 34, y_mix, fill=YELLOW, width=2)
        c.create_text(gx + 36, y_target, text="TARGET", anchor="w", fill=YELLOW,
                      font=fnt(8, mono=True))
        tx = w * 0.64
        c.create_text(tx, top + 8, anchor="nw", text="MIXTURE  {0:03.0f}%".format(self.mix),
                      fill=TEXT, font=fnt(10, mono=True))
        c.create_text(tx, top + 34, anchor="nw", text="TARGET   {0:03.0f}%".format(self.target),
                      fill=TEXT, font=fnt(10, mono=True))
        stable = self.in_time / max(0.001, self.run_time) * 100.0
        c.create_text(tx, top + 60, anchor="nw", text="STABILITY {0:03.0f}%".format(stable),
                      fill=YELLOW, font=fnt(10, mono=True))
        c.create_text(tx, top + 94, anchor="nw", text="BAND ±{0:.0f}% · {1}".format(
            self.band, "TIBANNA METERED" if self.rank == 0 else "MANUAL TRIM"),
            fill=MUTED, font=fnt(8, mono=True))
        if self.strain > 0.05:
            c.create_text(tx, top + 128, anchor="nw", text="INJECTOR STRAIN · {0:.1f}S".format(self.strain),
                          fill=YELLOW, font=fnt(8, mono=True))
        bar_y = h * 0.90
        c.create_rectangle(w * 0.14, bar_y, w * 0.86, bar_y + 8, outline=MUTED)
        c.create_rectangle(w * 0.14 + 2, bar_y + 2, w * 0.14 + 2 + (w * 0.72 - 4) * self.load / 100.0,
                           bar_y + 6, fill=YELLOW, outline="")
        c.create_text(w * 0.14, bar_y - 14, anchor="w", text="LOAD SEQUENCE",
                      fill=MUTED, font=fnt(8, mono=True))

    def draw_landing(self, c, w, h):
        deck_y = h - 46.0
        max_alt = self.alt_max
        def alt_y(value):
            value = max(0.0, min(max_alt, value))
            return 42.0 + (1.0 - value / max_alt) * (deck_y - 42.0)
        for tick in range(200, 801, 200):
            y = alt_y(tick)
            c.create_line(w * 0.06, y, w * 0.94, y, fill=MUTED, dash=(2, 6))
            c.create_text(w * 0.06, y - 6, text="{0} M".format(tick), anchor="w",
                          fill=MUTED, font=fnt(7, mono=True))
        c.create_rectangle(0, h - 30, w, h, fill=BG, outline="")
        for i in range(7):
            x = w * (0.04 + i * 0.15)
            c.create_line(x, h - 26, x + w * 0.09, h - 26, fill=MUTED)
        deck_w = w * 0.46
        deck_x = w / 2 - deck_w / 2
        c.create_rectangle(deck_x, deck_y, deck_x + deck_w, deck_y + 16,
                           fill=BG, outline=YELLOW)
        c.create_line(deck_x, deck_y + 16, deck_x + 18, h - 12, fill=YELLOW)
        c.create_line(deck_x + deck_w, deck_y + 16, deck_x + deck_w - 18, h - 12, fill=YELLOW)
        half_px = self.target_half / 280.0 * w * 0.36
        c.create_line(w / 2 - half_px, deck_y + 8, w / 2 + half_px, deck_y + 8,
                      fill=YELLOW, width=2)
        c.create_text(w / 2, deck_y - 10, text="TARGET", fill=MUTED, font=fnt(7, mono=True))
        bx = w / 2 + (self.x / 280.0) * (w * 0.36)
        bx = max(32, min(w - 32, bx))
        by = deck_y - 16 if (self.alt <= 0 and self.success) else alt_y(self.alt)
        if not (self.phase == "ending" and not self.success):
            c.create_line(bx, by - 16, bx, by + 8, fill=YELLOW, width=2)
            c.create_polygon(bx - 6, by + 8, bx, by + 22, bx + 6, by + 8,
                             fill="", outline=YELLOW)
            c.create_line(bx - 7, by + 8, bx - 17, by + 18, fill=YELLOW)
            c.create_line(bx + 7, by + 8, bx + 17, by + 18, fill=YELLOW)
        if self.burning and self.phase == "flying":
            length = random.randint(18, 42)
            c.create_polygon(bx - 5, by + 20, bx, by + 20 + length, bx + 5, by + 20,
                             fill=YELLOW, outline="")
        c.create_line(bx, deck_y, bx, h - 12, fill=MUTED, dash=(2, 5))
        wind = self.wind_strength * math.sin(self.run_time * 0.85 + 0.5)
        for i in range(3):
            y = 54 + i * 14
            length = 10 + abs(wind) * 8
            c.create_line(w - 34, y, w - 34 - length, y, fill=MUTED)
            c.create_line(w - 34 - length, y, w - 40 - length, y - 3, fill=MUTED)
        c.create_text(w - 14, 18, anchor="ne", text="WIND {0:+.1f}".format(wind),
                      fill=MUTED, font=fnt(8, mono=True))
        c.create_text(14, 18, anchor="nw", text="ALT {0:04.0f} M".format(self.alt),
                      fill=TEXT, font=fnt(10, "bold", mono=True))
        c.create_text(14, 38, anchor="nw", text="V/S {0:+05.1f} M/S".format(self.vy),
                      fill=YELLOW, font=fnt(9, mono=True))
        c.create_text(14, 56, anchor="nw", text="FUEL {0:03.0f}%".format(self.fuel),
                      fill=MUTED, font=fnt(9, mono=True))
        c.create_rectangle(w * 0.72, h - 22, w * 0.96, h - 16, outline=MUTED)
        c.create_rectangle(w * 0.72 + 1, h - 21, w * 0.72 + 1 + (w * 0.24 - 2) * self.fuel / 100.0,
                           h - 17, fill=YELLOW, outline="")

    def draw_debris(self, c, w, h):
        for i in range(18):
            x = (i * 173 % 997) / 997.0 * w
            y = ((i * 311 + int(self.elapsed * 140)) % 997) / 997.0 * h
            c.create_line(x, y, x, y + 8, fill=MUTED)
        for rock in self.debris:
            x, y = rock["x"] * w, rock["y"] * h
            r = rock["r"] * min(w, h)
            points = []
            for i in range(6):
                angle = rock["rot"] + i * math.pi / 3.0
                points.extend([x + r * math.cos(angle), y + r * math.sin(angle)])
            c.create_polygon(points, outline=rock["c"], fill="")
        sx, sy = self.ship_x * w, h - 62
        c.create_line(sx - 28, sy, sx - 8, sy - 6, fill=YELLOW, width=2)
        c.create_line(sx + 28, sy, sx + 8, sy - 6, fill=YELLOW, width=2)
        c.create_line(sx - 8, sy - 6, sx + 8, sy - 6, fill=YELLOW, width=2)
        c.create_polygon(sx, sy - 16, sx + 5, sy - 4, sx + 5, sy + 8, sx - 5, sy + 8,
                         sx - 5, sy - 4, fill="", outline=YELLOW)
        c.create_line(sx - 4, sy + 8, sx - 8, sy + 18, fill=YELLOW)
        c.create_line(sx + 4, sy + 8, sx + 8, sy + 18, fill=YELLOW)
        if self.hull > 0:
            c.create_arc(sx - 40, sy - 32, sx + 40, sy + 26, start=205, extent=130,
                         style="arc", outline=YELLOW)
            c.create_arc(sx - 52, sy - 42, sx + 52, sy + 36, start=215, extent=110,
                         style="arc", outline=MUTED, dash=(3, 4))
        c.create_text(14, 18, anchor="nw", text="HULL", fill=MUTED, font=fnt(8, mono=True))
        for i in range(self.max_hull):
            x = 54 + i * 15
            c.create_rectangle(x, 18, x + 10, 26,
                               fill=YELLOW if i < self.hull else BG, outline=MUTED)
        c.create_text(w - 14, 18, anchor="ne", text="{0:04.1f}S".format(max(0.0, 20.0 - self.run_time)),
                      fill=YELLOW, font=fnt(10, "bold", mono=True))
        c.create_text(w - 14, 38, anchor="ne", text="CLOSE CALLS {0}".format(self.close_calls),
                      fill=MUTED, font=fnt(8, mono=True))


class OutcomeScreen(Screen):
    def __init__(self, parent, app, index, option, record):
        Screen.__init__(self, parent, app)
        self.index = index
        self.option = option
        self.record = record
        holder = tk.Frame(self, bg=BG)
        holder.pack(fill="both", expand=True)
        self.card = tk.Frame(holder, bg=BG, highlightthickness=1,
                             highlightbackground=YELLOW)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86)
        inner = tk.Frame(self.card, bg=BG)
        inner.pack(fill="both", expand=True, padx=26, pady=22)
        head = tk.Frame(inner, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="MISSION {0:02d} · DEBRIEF".format(index + 1),
                 font=fnt(8, mono=True), bg=BG, fg=MUTED, anchor="w").pack(side="left")
        tk.Label(head, text="EXECUTION " + ("SUCCESS" if record["success"] else "FAILED"),
                 font=fnt(8, "bold", mono=True), bg=BG,
                 fg=YELLOW if record["success"] else MUTED).pack(side="right")
        tk.Label(inner, text=tracked(option["verdict"]), font=fnt(16, "bold"),
                 bg=BG, fg=verdict_colour(option["verdict"]),
                 anchor="w").pack(fill="x", pady=(8, 2))
        tk.Label(inner, text="DECISION · " + option["label"],
                 font=fnt(8, mono=True), bg=BG, fg=MUTED, anchor="w",
                 justify="left", wraplength=560).pack(fill="x")
        tk.Frame(inner, bg=MUTED, height=1).pack(fill="x", pady=12)
        self.explanation = tk.Label(inner, text=option["text"], font=fnt(10), bg=BG,
                                    fg=TEXT, anchor="w", justify="left", wraplength=620)
        self.explanation.pack(fill="x")
        panel = tk.Frame(inner, bg=BG, highlightthickness=1, highlightbackground=MUTED)
        panel.pack(fill="x", pady=(14, 0))
        pin = tk.Frame(panel, bg=BG)
        pin.pack(fill="x", padx=16, pady=10)
        pin_head = tk.Frame(pin, bg=BG)
        pin_head.pack(fill="x")
        tk.Label(pin_head, text="LIVE FLIGHT · " + record["flight_title"],
                 font=fnt(8, "bold", mono=True), bg=BG, fg=TEXT,
                 anchor="w").pack(side="left")
        tk.Label(pin_head, text="+{0:02d} PERFORMANCE".format(record["bonus"]),
                 font=fnt(8, mono=True), bg=BG, fg=YELLOW,
                 anchor="e").pack(side="right")
        self.stats = tk.Label(pin, text=self.stats_text(record["stats"], record["success"]),
                              font=fnt(8, mono=True), bg=BG, fg=MUTED,
                              anchor="w", justify="left", wraplength=600)
        self.stats.pack(fill="x", pady=(6, 0))
        bottom = tk.Frame(inner, bg=BG)
        bottom.pack(fill="x", pady=(16, 0))
        left = tk.Frame(bottom, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="DECISION {0:+d} · FLIGHT {1:+d}".format(
            record["option_points"], record["bonus"]), font=fnt(8, mono=True),
            bg=BG, fg=MUTED, anchor="w").pack(anchor="w")
        tk.Label(left, text="{0:+d} PTS".format(record["points"]),
                 font=fnt(20, "bold", mono=True), bg=BG,
                 fg=YELLOW if record["points"] > 0 else MUTED).pack(anchor="w")
        FlatButton(bottom, app, "CONTINUE", self.g(app.advance), "primary",
                   size=10, padx=18, pady=8).pack(side="right")

        def wrap(event):
            width = max(260, event.width - 56)
            self.explanation.configure(wraplength=width)
            self.stats.configure(wraplength=width)
        self.card.bind("<Configure>", self.g(wrap))

    @staticmethod
    def stats_text(stats, success=True):
        mode = stats.get("mode")
        if mode == "load":
            return "STABILITY {0:.0f}% · LOAD {1:.0f}% · NO NETWORK".format(
                stats.get("stability", 0), stats.get("load", 0))
        if mode == "landing":
            return "{0} {1:.1f} M/S · MISS {2:.1f} M · FUEL {3:.0f}%".format(
                "TOUCHDOWN" if success else "IMPACT", stats.get("speed", 0),
                stats.get("miss", 0), stats.get("fuel", 0))
        return "HULL {0}/{1} · CLOSE CALLS {2} · BESKAR ONLINE".format(
            stats.get("hull", 0), stats.get("max_hull", 0), stats.get("close", 0))


class FinalScreen(Screen):
    def __init__(self, parent, app):
        Screen.__init__(self, parent, app)
        self.step = 0
        self.total = 28
        self.total_rows = 4320000

        holder = tk.Frame(self, bg=BG)
        holder.pack(fill="both", expand=True)
        self.card = tk.Frame(holder, bg=BG)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.76)

        tk.Label(self.card, text=tracked("Flight log · Rebel Aerospace Academy"),
                 font=fnt(8), bg=BG, fg=MUTED).pack()
        tk.Label(self.card, text=tracked("Mission complete"), font=fnt(21, "bold"),
                 bg=BG, fg=YELLOW).pack(pady=(6, 2))
        tk.Label(self.card, text="CALLSIGN · " + app.callsign,
                 font=fnt(9, mono=True), bg=BG, fg=MUTED).pack()
        if app.last_run_improved:
            record_text = "NEW PERSONAL BEST · SAVED LOCALLY"
        else:
            record_text = "PERSONAL BEST · {0:03d}".format(app.pilot.best_score)
        tk.Label(self.card, text=record_text, font=fnt(8, mono=True), bg=BG,
                 fg=YELLOW if app.last_run_improved else MUTED).pack(pady=(4, 0))

        tk.Label(self.card, text=tracked("Total score"), font=fnt(8),
                 bg=BG, fg=MUTED).pack(pady=(12, 0))
        score_row = tk.Frame(self.card, bg=BG)
        score_row.pack()
        tk.Label(score_row, text=str(app.score), font=fnt(28, "bold", mono=True),
                 bg=BG, fg=YELLOW).pack(side="left")
        tk.Label(score_row, text="/ " + str(MAX_SCORE), font=fnt(10, mono=True),
                 bg=BG, fg=MUTED).pack(side="left", padx=(8, 0), pady=(10, 0))
        tk.Label(self.card, text=tracked("Rank · " + rank_for(app.score)),
                 font=fnt(11, "bold"), bg=BG, fg=TEXT).pack(pady=(4, 10))

        log = tk.Frame(self.card, bg=BG)
        log.pack(fill="x")
        for i, mission in enumerate(MISSIONS):
            result = app.results[i] if i < len(app.results) else None
            if result is None:
                line = "M{0:02d}  {1:<18}  {2:>4}  SKIPPED".format(
                    i + 1, mission["tag"][:18], "0")
                colour = MUTED
            else:
                line = "M{0:02d}  {1:<18}  {2:>4}  {3}".format(
                    i + 1, mission["tag"][:18],
                    "{0:+d}".format(result["points"]), result["verdict"])
                colour = verdict_colour(result["verdict"])
            tk.Label(log, text=line, font=fnt(9, mono=True), bg=BG, fg=colour,
                     anchor="w").pack(fill="x")

        self.panel = tk.Frame(self.card, bg=BG, bd=0, highlightthickness=1,
                              highlightbackground=MUTED)
        self.panel.pack(fill="x", pady=(14, 0))
        inner = tk.Frame(self.panel, bg=BG)
        inner.pack(fill="both", expand=True, padx=18, pady=12)
        head = tk.Frame(inner, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text=tracked("Tiger Data Hypertable Cloud"), font=fnt(8),
                 bg=BG, fg=TEXT, anchor="w").pack(side="left")
        tk.Label(head, text="SIMULATION", font=fnt(8, mono=True), bg=BG, fg=YELLOW,
                 anchor="e").pack(side="right")
        self.note = tk.Label(
            inner,
            text=("Telemetry is written to a simulated hypertable on this machine. "
                  "No network request is made and no data is uploaded."),
            font=fnt(9), bg=BG, fg=MUTED, anchor="w", justify="left",
            wraplength=600)
        self.note.pack(fill="x", pady=(6, 10))
        self.bar = ProgressBar(inner, app, 8)
        self.bar.pack(fill="x")
        self.counter = tk.Label(inner, text="0 COORDINATE ROWS WRITTEN",
                                font=fnt(10, mono=True), bg=BG, fg=YELLOW,
                                anchor="w")
        self.counter.pack(fill="x", pady=(8, 2))
        self.status = tk.Label(inner, text="OPENING LOCAL WRITER",
                               font=fnt(8, mono=True), bg=BG, fg=MUTED, anchor="w")
        self.status.pack(fill="x")

        actions = tk.Frame(self.card, bg=BG)
        actions.pack(pady=(16, 0))
        FlatButton(actions, app, "PLAY AGAIN", self.g(app.start_over), "primary",
                   size=10, padx=22, pady=9).pack(side="left", padx=(0, 10))
        FlatButton(actions, app, "QUIT", self.g(app.close), "outline",
                   size=10, padx=22, pady=9).pack(side="left")

        self.panel.bind("<Configure>", self.g(self.on_panel_resize))
        self.app.schedule(320, self.save_step)

    def on_panel_resize(self, event):
        self.note.configure(wraplength=max(220, event.width - 40))

    @staticmethod
    def status_for(step):
        if step < 6:
            return "OPENING LOCAL WRITER"
        if step < 13:
            return "CREATING HYPERTABLE flight_telemetry"
        if step < 20:
            return "WRITING TELEMETRY CHUNKS"
        if step < 26:
            return "COMPRESSING CHUNKS"
        return "VERIFYING ROW COUNT"

    def save_step(self):
        if not self.winfo_exists():
            return
        self.step += 1
        fraction = self.step / float(self.total)
        self.bar.set(fraction)
        rows = int(self.total_rows * fraction) // 1000 * 1000
        self.counter.configure(text="{0:,} COORDINATE ROWS WRITTEN".format(rows))
        self.status.configure(text=self.status_for(self.step))
        if self.step >= self.total:
            self.bar.set(1.0)
            self.counter.configure(
                text="{0:,} COORDINATE ROWS WRITTEN".format(self.total_rows))
            self.status.configure(
                text="WRITE COMPLETE · SAVED LOCALLY · NOTHING UPLOADED", fg=YELLOW)
            return
        self.app.schedule(85, self.save_step)


class App:
    KEY_MAP = {"Up": "up", "Down": "down", "Left": "left", "Right": "right",
               "space": "space", "w": "up", "a": "left", "s": "down",
               "d": "right", "p": "pause", "Escape": "pause"}

    def __init__(self, root, pilot=None):
        self.root = root
        self.after_ids = set()
        self.error_panel = None
        self.reporting = False
        self.current = None
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.callsign = ""
        self.pilot = pilot or PilotStore()
        self.pending_index = 0
        self.pending_option = None
        self.recorded = False
        self.last_run_improved = False
        self.fullscreen = False

        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.guard(self.close))

        footer = tk.Frame(root, bg=BG)
        footer.pack(side="bottom", fill="x")
        tk.Frame(footer, bg=MUTED, height=1).pack(fill="x")
        tk.Label(footer, text=FOOTER_TEXT, font=fnt(8), bg=BG,
                 fg=MUTED).pack(pady=6)

        self.container = tk.Frame(root, bg=BG)
        self.container.pack(side="top", fill="both", expand=True)

        for digit in ("1", "2", "3"):
            root.bind("<KeyPress-{0}>".format(digit),
                      self.guard(lambda event, d=digit: self.dispatch_digit(d)))
        root.bind("<KeyPress>", self.guard(self.on_key_press), add="+")
        root.bind("<KeyRelease>", self.guard(self.on_key_release), add="+")
        root.bind("<F11>", self.guard(self.toggle_fullscreen), add="+")

        self.show_title()

    # -- scheduling ----------------------------------------------------
    def schedule(self, delay, fn):
        def run():
            self.after_ids.discard(handle)
            try:
                fn()
            except Exception as error:
                self.report_error(error)

        try:
            handle = self.root.after(int(delay), run)
        except Exception:
            return None
        self.after_ids.add(handle)
        return handle

    def cancel_all(self):
        for handle in list(self.after_ids):
            try:
                self.root.after_cancel(handle)
            except Exception:
                pass
        self.after_ids.clear()

    def guard(self, fn):
        def guarded(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as error:
                self.report_error(error)
        return guarded

    # -- screens -------------------------------------------------------
    def show(self, factory):
        try:
            self.cancel_all()
            self.clear_error()
            if self.current is not None:
                try:
                    self.current.destroy()
                except Exception:
                    pass
                self.current = None
            frame = factory(self.container, self)
            frame.pack(side="top", fill="both", expand=True)
            self.current = frame
        except Exception as error:
            self.report_error(error)

    def show_title(self):
        self.show(lambda parent, app: TitleScreen(parent, app))

    def show_auth(self):
        self.show(lambda parent, app: AuthScreen(parent, app))

    def show_mission(self, index):
        self.mission_index = index
        self.show(lambda parent, app: MissionScreen(parent, app, index))

    def start_missions(self):
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.pending_option = None
        self.recorded = False
        self.last_run_improved = False
        self.show_mission(0)

    def begin_flight(self, index, option):
        self.pending_index = index
        self.pending_option = option
        self.mission_index = index
        self.show(lambda parent, app: FlightScreen(parent, app, index, option))

    def complete_flight(self, index, option, result):
        if option is None or result is None:
            return
        record = {"mission": index, "label": option["label"],
                  "option_points": option["points"], "bonus": result["bonus"],
                  "points": option["points"] + result["bonus"],
                  "verdict": option["verdict"], "success": result["success"],
                  "flight_title": result["title"], "stats": result["stats"]}
        self.score += record["points"]
        self.results.append(record)
        self.pending_option = None
        self.pending_index = index
        self.show(lambda parent, app: OutcomeScreen(parent, app, index, option, record))

    def finish_run(self):
        if not self.recorded:
            self.recorded = True
            self.last_run_improved = self.pilot.record(
                self.score, self.callsign, rank_for(self.score))
        self.show(lambda parent, app: FinalScreen(parent, app))

    def advance(self):
        next_index = self.mission_index + 1
        if next_index < len(MISSIONS):
            self.show_mission(next_index)
        else:
            self.finish_run()

    def start_over(self):
        self.back_to_title()

    def back_to_title(self):
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.pending_option = None
        self.recorded = False
        self.last_run_improved = False
        self.show_title()

    def abort_flight(self):
        self.back_to_title()

    def on_key_press(self, event):
        if self.error_panel is not None:
            return
        screen = self.current
        if screen is None:
            return
        handler = getattr(screen, "on_key", None)
        if not callable(handler):
            return
        key = self.KEY_MAP.get(event.keysym)
        if key is None:
            key = self.KEY_MAP.get(event.keysym.lower())
        if key is not None:
            handler(key, True)

    def on_key_release(self, event):
        if self.error_panel is not None:
            return
        screen = self.current
        if screen is None:
            return
        handler = getattr(screen, "on_key", None)
        if not callable(handler):
            return
        key = self.KEY_MAP.get(event.keysym)
        if key is None:
            key = self.KEY_MAP.get(event.keysym.lower())
        if key is not None and key != "pause":
            handler(key, False)

    def toggle_fullscreen(self, _event=None):
        try:
            self.fullscreen = not self.fullscreen
            self.root.attributes("-fullscreen", self.fullscreen)
        except Exception:
            self.fullscreen = False

    def dispatch_digit(self, digit):
        if self.error_panel is not None:
            return
        screen = self.current
        if screen is None:
            return
        handler = getattr(screen, "on_digit", None)
        if callable(handler):
            handler(digit)

    # -- errors --------------------------------------------------------
    def clear_error(self):
        panel = self.error_panel
        self.error_panel = None
        if panel is not None:
            try:
                panel.destroy()
            except Exception:
                pass

    def report_error(self, error):
        if self.reporting:
            return
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        self.reporting = True
        try:
            self.cancel_all()
            self.clear_error()
            panel = tk.Frame(self.root, bg=BG)
            panel.place(x=0, y=0, relwidth=1, relheight=1)
            panel.lift()
            card = tk.Frame(panel, bg=BG, bd=0, highlightthickness=1,
                            highlightbackground=YELLOW)
            card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.62)
            inner = tk.Frame(card, bg=BG)
            inner.pack(fill="both", expand=True, padx=28, pady=24)
            tk.Label(inner, text=tracked("System fault"), font=fnt(16, "bold"),
                     bg=BG, fg=YELLOW).pack()
            tk.Label(inner, text=("The simulator caught an unexpected error and "
                                  "stopped the current screen. Nothing was sent "
                                  "anywhere."),
                     font=fnt(10), bg=BG, fg=TEXT, justify="center",
                     wraplength=420).pack(pady=(10, 0))
            tk.Label(inner, text="REFERENCE · " + type(error).__name__,
                     font=fnt(8, mono=True), bg=BG, fg=MUTED).pack(pady=(12, 0))
            FlatButton(inner, self, "BACK TO TITLE",
                       self.guard(self.back_to_title), "primary",
                       size=10, padx=20, pady=9).pack(pady=(20, 0))
            self.error_panel = panel
        except Exception:
            pass
        finally:
            self.reporting = False

    def close(self):
        try:
            self.cancel_all()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


def create_root():
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.minsize(900, 600)
    root.configure(bg=BG)
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    width = min(1120, max(900, screen_w - 120))
    height = min(760, max(600, screen_h - 160))
    left = max(0, (screen_w - width) // 2)
    top = max(0, (screen_h - height) // 3)
    root.geometry("{0}x{1}+{2}+{3}".format(width, height, left, top))
    return root


def main():
    try:
        root = create_root()
    except Exception:
        return 1
    try:
        app = App(root)
    except Exception:
        try:
            root.destroy()
        except Exception:
            pass
        return 1
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
