"""The Interstellar Driver's Ed: Rebel-SpaceX Flight Simulator.

Single-file Tkinter desktop app built for MLH Hack Week.
Auth0 and Tiger Data are simulated on this machine only: no network,
no subprocesses, no persistence.
"""

import hashlib
import math
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont

BG = "#000000"
YELLOW = "#FFE81F"
TEXT = "#C9D1D9"
MUTED = "#8B96A3"

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")
SANS = "Helvetica Neue" if IS_MAC else ("Segoe UI" if IS_WIN else "DejaVu Sans")
MONO = "Menlo" if IS_MAC else ("Consolas" if IS_WIN else "DejaVu Sans Mono")

WINDOW_TITLE = "The Interstellar Driver's Ed · Rebel-SpaceX Flight Simulator"
FOOTER_TEXT = "Hackathon build · simulated sponsor integrations"


def fnt(size, weight="normal", mono=False):
    return (MONO if mono else SANS, size, weight)


def tracked(text):
    """Wide-spaced uppercase, used for titles and small labels."""
    return " ".join(text.upper())


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

MAX_SCORE = sum(max(o["points"] for o in m["options"]) for m in MISSIONS)

RANKS = [
    (280, "JEDI ACE"),
    (210, "SQUADRON LEADER"),
    (140, "SENIOR PILOT"),
    (70, "FLIGHT CADET"),
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
        self.entry.insert(0, app.callsign if app.callsign else "CADET-X")
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
        self.app.schedule(1600, self.app.start_missions)

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
        tk.Label(self.right, text=tracked(self.mission["prompt"]), font=fnt(8),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x", pady=(0, 8))
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
        self.app.score += option["points"]
        self.app.results.append({
            "mission": self.index,
            "label": option["label"],
            "points": option["points"],
            "verdict": option["verdict"],
        })
        self.score_label.configure(text=score_text(self.app.score))
        self.show_outcome(option)

    def show_outcome(self, option):
        backdrop = tk.Frame(self, bg=BG)
        backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        backdrop.lift()
        self.overlay = backdrop

        card = tk.Frame(backdrop, bg=BG, bd=0, highlightthickness=1,
                        highlightbackground=YELLOW)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.84)
        inner = tk.Frame(card, bg=BG)
        inner.pack(fill="both", expand=True, padx=26, pady=22)

        tk.Label(inner, text="MISSION {0:02d} · OUTCOME".format(self.index + 1),
                 font=fnt(8, mono=True), bg=BG, fg=MUTED,
                 anchor="w").pack(fill="x")
        tk.Label(inner, text=tracked(option["verdict"]), font=fnt(16, "bold"),
                 bg=BG, fg=verdict_colour(option["verdict"]),
                 anchor="w").pack(fill="x", pady=(6, 2))
        selected = tk.Label(inner, text="SELECTED · " + option["label"],
                            font=fnt(8, mono=True), bg=BG, fg=MUTED, anchor="w",
                            justify="left", wraplength=560)
        selected.pack(fill="x")
        tk.Frame(inner, bg=MUTED, height=1).pack(fill="x", pady=14)

        explanation = tk.Label(inner, text=option["text"], font=fnt(11), bg=BG,
                               fg=TEXT, anchor="w", justify="left", wraplength=600)
        explanation.pack(fill="x")

        bottom = tk.Frame(inner, bg=BG)
        bottom.pack(fill="x", pady=(18, 0))
        colour = YELLOW if option["points"] > 0 else MUTED
        tk.Label(bottom, text=points_text(option["points"]),
                 font=fnt(20, "bold", mono=True), bg=BG,
                 fg=colour).pack(side="left")
        FlatButton(bottom, self.app, "CONTINUE", self.g(self.app.advance),
                   "primary", size=10, padx=18, pady=8).pack(side="right")

        def on_card(event):
            width = max(220, event.width - 56)
            explanation.configure(wraplength=width)
            selected.configure(wraplength=width)

        card.bind("<Configure>", self.g(on_card))

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
    def __init__(self, root):
        self.root = root
        self.after_ids = set()
        self.error_panel = None
        self.reporting = False
        self.current = None
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.callsign = ""

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
        self.show_mission(0)

    def advance(self):
        next_index = self.mission_index + 1
        if next_index < len(MISSIONS):
            self.show_mission(next_index)
        else:
            self.show(lambda parent, app: FinalScreen(parent, app))

    def start_over(self):
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.show_title()

    def back_to_title(self):
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.show_title()

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
