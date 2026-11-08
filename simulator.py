"""The Interstellar Driver's Ed: Rebel-SpaceX Flight Simulator.

Tkinter desktop app built for MLH Hack Week. Everything is local: no
network and no accounts. The app keeps one small pilot record in the user's
home directory; nothing ever leaves the computer.
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

try:
    import customtkinter as ctk
except Exception:  # keeps the core game importable without the optional shell
    ctk = None

import audio as audio_engine
import dataviz
import engine3d
import fleet3d
import shipyard
import visuals
import visuals3d

BG = "#000000"
YELLOW = "#FFE81F"
TEXT = "#C9D1D9"
MUTED = "#8B96A3"

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")
SANS = "Helvetica Neue" if IS_MAC else ("Segoe UI" if IS_WIN else "DejaVu Sans")
MONO = "Menlo" if IS_MAC else ("Consolas" if IS_WIN else "DejaVu Sans Mono")

APP_VERSION = "1.2.1"
WINDOW_TITLE = "The Interstellar Driver's Ed · Rebel-SpaceX Flight Simulator"
FOOTER_TEXT = "v{0} · local pilot log · offline".format(APP_VERSION)
RECORD_FOLDER = ".interstellar_drivers_ed"


def fnt(size, weight="normal", mono=False):
    return (MONO if mono else SANS, size, weight)


def tracked(text):
    """Wide-spaced uppercase, used for titles and small labels."""
    return " ".join(text.upper())


def set_root_bg(root):
    """Apply the archive background to either a Tk or a CustomTk root."""
    try:
        root.configure(bg=BG)
    except Exception:
        try:
            root.configure(fg_color=BG)
        except Exception:
            pass


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
        self.sound_on = True
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
        self.sound_on = bool(raw.get("sound_on", True))

    def record(self, score, callsign, rank):
        """Save a completed flight and return True when the score is a record."""
        self.flights += 1
        improved = score > self.best_score
        if improved:
            self.best_score = score
            self.best_rank = rank
        self.last_callsign = (callsign or "")[:20]
        self._write()
        return improved

    def set_sound(self, enabled):
        """Persist the sound preference without touching flight records."""
        self.sound_on = bool(enabled)
        self._write()

    def _write(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": APP_VERSION,
                "best_score": self.best_score,
                "best_rank": self.best_rank,
                "flights": self.flights,
                "last_callsign": self.last_callsign,
                "sound_on": self.sound_on,
            }
            temporary = self.path.with_name(self.path.name + ".tmp")
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        except Exception:
            pass


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

    def set_text(self, text):
        self.label.configure(text=text)

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
        audio = getattr(self.app, "audio", None)
        if audio is not None:
            audio.play("click", 0.18)
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


class MetricChart(tk.Canvas):
    """A small, dependency-free bar chart used by the flight debrief.

    The chart is deliberately direct: one label, one value and one 0..limit
    track per row, with a target tick where a target is meaningful. It uses the
    same yellow/grey language as the rest of the simulator and redraws on
    resize.
    """

    def __init__(self, parent, metrics=(), height=92, empty_text="NO TELEMETRY"):
        tk.Canvas.__init__(self, parent, bg=BG, height=height, bd=0,
                           highlightthickness=0, takefocus=0)
        self.metrics = tuple(metrics)
        self.empty_text = empty_text
        self.bind("<Configure>", self.redraw)
        self.redraw()

    def redraw(self, _event=None):
        c = self
        c.delete("all")
        width = c.winfo_width()
        height = c.winfo_height()
        if width < 2 or height < 2:
            return
        if not self.metrics:
            c.create_text(width / 2, height / 2, text=self.empty_text,
                          fill=MUTED, font=fnt(8, mono=True))
            return
        top = 2.0
        row_height = (height - 4.0) / len(self.metrics)
        for index, metric in enumerate(self.metrics):
            y = top + index * row_height
            tone = getattr(metric, "tone", "default")
            value_colour = MUTED if tone == "bad" else (TEXT if tone == "warn" else YELLOW)
            fill_colour = MUTED if tone == "bad" else (TEXT if tone == "warn" else YELLOW)
            c.create_text(0, y + 1, anchor="nw", text=metric.label,
                          fill=MUTED, font=fnt(8, mono=True))
            c.create_text(width, y + 1, anchor="ne", text=metric.display,
                          fill=value_colour, font=fnt(9, "bold", mono=True))
            bar_y = y + max(16.0, row_height - 8.0)
            c.create_rectangle(0, bar_y, width, bar_y + 5, outline=MUTED)
            fill_end = max(0.0, min(width, width * metric.fraction))
            if fill_end > 1.0:
                c.create_rectangle(0, bar_y + 1, fill_end, bar_y + 4,
                                   fill=fill_colour, outline="")
            target = metric.target_fraction
            if target is not None:
                target_x = max(0.0, min(width, width * target))
                c.create_line(target_x, bar_y - 2, target_x, bar_y + 7,
                              fill=YELLOW)


if ctk is not None:
    class CtkFlatButton(ctk.CTkButton):
        """CustomTkinter button that keeps the app's square, inverted hover."""

        def __init__(self, parent, app, text, command, variant="outline",
                     size=11, pady=10, padx=14):
            self.app = app
            self.variant = variant
            self.command = command
            self.enabled = True
            self.hover = False
            self.last_click = 0.0
            height = max(32, int(size * 2 + pady * 2))
            width = max(56, int(padx * 2 + len(str(text)) * max(6, size * 0.7)))
            ctk.CTkButton.__init__(
                self, parent, text=text, command=self.on_press,
                width=width, height=height, corner_radius=0,
                border_width=1, border_spacing=0, bg_color=BG,
                fg_color=BG, hover=False, text_color=YELLOW,
                text_color_disabled=MUTED, border_color=MUTED,
                font=ctk.CTkFont(family=SANS, size=size, weight="bold"))
            self.bind("<Enter>", self.on_enter)
            self.bind("<Leave>", self.on_leave)
            self.apply()

        def apply(self):
            if not self.enabled:
                bg, fg, border = BG, MUTED, MUTED
                state = "disabled"
            elif self.variant == "primary":
                bg, fg, border = (BG, YELLOW, YELLOW) if self.hover else (YELLOW, BG, YELLOW)
                state = "normal"
            else:
                bg, fg, border = (YELLOW, BG, YELLOW) if self.hover else (BG, YELLOW, MUTED)
                state = "normal"
            self.configure(fg_color=bg, text_color=fg, border_color=border,
                           state=state)

        def set_enabled(self, enabled):
            self.enabled = bool(enabled)
            self.hover = False
            self.apply()

        def set_text(self, text):
            self.configure(text=text)

        def on_enter(self, _event=None):
            if self.enabled and not self.hover:
                self.hover = True
                self.apply()

        def on_leave(self, _event=None):
            if self.hover:
                self.hover = False
                self.apply()

        def on_press(self):
            if not self.enabled:
                return
            now = time.monotonic()
            if now - self.last_click < 0.25:
                return
            self.last_click = now
            if self.command is not None:
                self.command()

    class CtkProgressBar(ctk.CTkProgressBar):
        def __init__(self, parent, app, height=10):
            ctk.CTkProgressBar.__init__(
                self, parent, height=height, corner_radius=0, border_width=1,
                bg_color=BG, fg_color=BG, border_color=MUTED,
                progress_color=YELLOW)
            self.app = app
            self.set(0.0)

    FlatButton = CtkFlatButton
    ProgressBar = CtkProgressBar


class Screen(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent, bg=BG)
        self.app = app
        self.backdrop = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0,
                                  takefocus=0)
        self.backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        self.backdrop.bind("<Configure>", self.paint_backdrop)

    def paint_backdrop(self, event=None):
        try:
            width = event.width if event is not None else self.backdrop.winfo_width()
            height = event.height if event is not None else self.backdrop.winfo_height()
            if width > 4 and height > 4:
                visuals.draw_backdrop(self.backdrop, width, height)
        except Exception:
            pass

    def g(self, fn):
        return self.app.guard(fn)


class TitleScreen(Screen):
    def __init__(self, parent, app):
        Screen.__init__(self, parent, app)
        self.width = 1
        self.height = 1
        self.fitted_width = -1
        self.stars = []
        self.presentation_panel = None
        self.title_font_a = tkfont.Font(family=SANS, size=42, weight="bold")
        self.title_font_b = tkfont.Font(family=SANS, size=56, weight="bold")

        self.canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.content = tk.Frame(self, bg=BG)
        self.content.place(relx=0.5, rely=0.51, anchor="center", relwidth=0.88)
        self.content.columnconfigure(0, weight=3)
        self.content.columnconfigure(1, weight=2)

        hero = tk.Frame(self.content, bg=BG)
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 32))

        top = tk.Frame(hero, bg=BG)
        top.pack(fill="x")
        tk.Label(top, text=tracked("Rebel Aerospace Academy"),
                 font=fnt(8), bg=BG, fg=MUTED, anchor="w").pack(side="left")
        tk.Label(top, text="SECTOR 07 / KAMINO", font=fnt(8, mono=True),
                 bg=BG, fg=MUTED, anchor="e").pack(side="right")

        index_row = tk.Frame(hero, bg=BG)
        index_row.pack(fill="x", pady=(16, 0))
        tk.Label(index_row, text="01", font=fnt(15, "bold", mono=True),
                 bg=BG, fg=YELLOW).pack(side="left")
        tk.Frame(index_row, bg=MUTED, height=1).pack(side="left", fill="x",
                                                       expand=True, padx=10)
        tk.Label(index_row, text=tracked("Pilot induction"),
                 font=fnt(8), bg=BG, fg=MUTED).pack(side="right")

        title_a = tk.Label(hero, text="THE INTERSTELLAR",
                           font=self.title_font_a, bg=BG, fg=YELLOW, anchor="w")
        title_a.pack(fill="x", pady=(10, 0))
        title_b = tk.Label(hero, text="DRIVER'S ED",
                           font=self.title_font_b, bg=BG, fg=YELLOW, anchor="w")
        title_b.pack(fill="x", pady=(0, 8))
        self.title_labels = (title_a, title_b)

        tk.Label(hero, text="REBEL-SPACEX FLIGHT SIMULATOR",
                 font=fnt(10, "bold", mono=True), bg=BG, fg=TEXT,
                 anchor="w").pack(fill="x")
        tk.Label(hero,
                 text=("Three missions through the edge of the atmosphere. "
                       "Trim the stack, land the booster, cross the debris field."),
                 font=fnt(10), bg=BG, fg=MUTED, anchor="w",
                 justify="left", wraplength=440).pack(fill="x", pady=(10, 0))

        stats = tk.Frame(hero, bg=BG)
        stats.pack(fill="x", pady=(18, 0))
        for value, caption in (("03", "MISSIONS"), ("390", "MAX PTS"),
                               ("LOCAL", "DATA")):
            chip = tk.Frame(stats, bg=BG, highlightthickness=1,
                            highlightbackground=MUTED)
            chip.pack(side="left", padx=(0, 8))
            inner_chip = tk.Frame(chip, bg=BG)
            inner_chip.pack(padx=10, pady=7)
            tk.Label(inner_chip, text=value, font=fnt(12, "bold", mono=True),
                     bg=BG, fg=YELLOW).pack(anchor="w")
            tk.Label(inner_chip, text=caption, font=fnt(7, mono=True),
                     bg=BG, fg=MUTED).pack(anchor="w")

        tk.Label(hero,
                 text="↑↓ TRIM  ·  SPACE BURN  ·  ←→ STEER  ·  F11 FULLSCREEN",
                 font=fnt(8, mono=True), bg=BG, fg=MUTED,
                 anchor="w").pack(fill="x", pady=(20, 0))

        panel = tk.Frame(self.content, bg=BG, highlightthickness=1,
                         highlightbackground=MUTED)
        panel.grid(row=0, column=1, sticky="nsew")
        inner = tk.Frame(panel, bg=BG)
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        head = tk.Frame(inner, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text=tracked("Pilot access"), font=fnt(8, "bold"),
                 bg=BG, fg=TEXT, anchor="w").pack(side="left")
        tk.Label(head, text="READY", font=fnt(8, mono=True),
                 bg=BG, fg=YELLOW, anchor="e").pack(side="right")
        tk.Frame(inner, bg=MUTED, height=1).pack(fill="x", pady=(10, 14))

        tk.Label(inner, text="CALLSIGN", font=fnt(8, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x")
        if ctk is not None:
            self.entry = ctk.CTkEntry(
                inner, width=260, height=40, corner_radius=0, border_width=1,
                bg_color=BG, fg_color=BG, border_color=MUTED,
                text_color=YELLOW, font=ctk.CTkFont(family=MONO, size=13),
                justify="center")
            self.entry.pack(fill="x", pady=(6, 4))
            self.entry.bind("<FocusIn>",
                            lambda _event: self.entry.configure(border_color=YELLOW))
            self.entry.bind("<FocusOut>",
                            lambda _event: self.entry.configure(border_color=MUTED))
        else:
            self.entry = tk.Entry(inner, font=fnt(12, mono=True), bg=BG,
                                  fg=YELLOW, insertbackground=YELLOW,
                                  relief="flat", bd=0, highlightthickness=1,
                                  highlightbackground=MUTED,
                                  highlightcolor=YELLOW, width=26,
                                  justify="center")
            self.entry.pack(fill="x", pady=(6, 4), ipady=5)
        self.entry.insert(0, app.callsign or app.pilot.last_callsign or "CADET-X")
        self.hint = tk.Label(inner, text="LOCAL PROFILE · 1–20 CHARACTERS",
                             font=fnt(7, mono=True), bg=BG, fg=MUTED,
                             anchor="w")
        self.hint.pack(fill="x")

        FlatButton(inner, app, "START MISSION", self.g(self.start),
                   "primary", size=10, padx=18, pady=9).pack(fill="x",
                                                               pady=(14, 7))
        actions = tk.Frame(inner, bg=BG)
        actions.pack(fill="x")
        FlatButton(actions, app, "HANGAR", self.g(app.show_hangar),
                   "outline", size=8, padx=8, pady=7).pack(
                       side="left", fill="x", expand=True, padx=(0, 6))
        FlatButton(actions, app, "QUIT", self.g(app.close), "outline",
                   size=8, padx=8, pady=7).pack(side="left", fill="x",
                                                expand=True)
        FlatButton(inner, app, "PRESENTATION · JUMP TO MISSION",
                   self.g(self.show_presentation), "outline",
                   size=8, padx=8, pady=7).pack(fill="x", pady=(7, 0))

        tk.Frame(inner, bg=MUTED, height=1).pack(fill="x", pady=(16, 12))
        tk.Label(inner, text=tracked("Pilot record"), font=fnt(7, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x")
        record_rows = (
            ("BEST SCORE", "{0:03d}".format(app.pilot.best_score)),
            ("FLIGHTS", "{0:02d}".format(app.pilot.flights)),
            ("BEST RANK", app.pilot.best_rank or "UNRANKED"),
        )
        for caption, value in record_rows:
            row = tk.Frame(inner, bg=BG)
            row.pack(fill="x", pady=(6, 0))
            tk.Label(row, text=caption, font=fnt(8, mono=True), bg=BG,
                     fg=MUTED, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=fnt(9, "bold", mono=True), bg=BG,
                     fg=TEXT, anchor="e").pack(side="right")
        tk.Label(inner, text="LOCAL JSON · NO NETWORK", font=fnt(7, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x", pady=(14, 0))

        self.canvas.bind("<Configure>", self.g(self.on_resize))
        self.entry.bind("<Return>", self.g(self.start))
        self.entry.bind("<KP_Enter>", self.g(self.start))
        self.app.schedule(60, self.tick)
        self.app.schedule(120, self.entry.focus_set)

    # -- starfield and station art ------------------------------------
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
        self.draw_art()
        self.draw_stars()

    def fit_title(self):
        limit = max(280, min(520, int(self.width * 0.42)))
        for font, text, base in ((self.title_font_a, "THE INTERSTELLAR", 42),
                                 (self.title_font_b, "DRIVER'S ED", 56)):
            size = base
            font.configure(size=size)
            while size > 18 and font.measure(text) > limit:
                size -= 1
                font.configure(size=size)

    def draw_art(self):
        c = self.canvas
        c.delete("all")
        if self.width < 40 or self.height < 40:
            return
        w, h = self.width, self.height
        visuals3d.draw_title(c, w, h, tag="art3d")
        visuals.draw_corner_marks(c, 22, 22, w - 22, h - 22, MUTED, 18)
        c.create_text(w - 26, h - 42, anchor="se",
                      text="LOCAL FLIGHT OPERATIONS // 01",
                      fill=MUTED, font=fnt(7, mono=True), tags="art")

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

    # -- presentation mode --------------------------------------------
    def show_presentation(self):
        if self.presentation_panel is not None:
            return
        panel = tk.Frame(self, bg=BG)
        panel.place(x=0, y=0, relwidth=1, relheight=1)
        panel.lift()
        card = tk.Frame(panel, bg=BG, highlightthickness=1,
                        highlightbackground=YELLOW)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.66)
        inner = tk.Frame(card, bg=BG)
        inner.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(inner, text=tracked("Presentation mode"),
                 font=fnt(16, "bold"), bg=BG, fg=YELLOW,
                 anchor="w").pack(fill="x")
        tk.Label(inner,
                 text="JUMP STRAIGHT TO A MISSION · DEMO SCORE IS NOT SAVED",
                 font=fnt(8, mono=True), bg=BG, fg=MUTED,
                 anchor="w", justify="left", wraplength=520).pack(
                     fill="x", pady=(5, 14))
        for index, mission in enumerate(MISSIONS):
            FlatButton(inner, self.app,
                       "MISSION 0{0} · {1}".format(index + 1, mission["tag"]),
                       self.g(lambda choice=index: self.app.begin_presentation(choice)),
                       "primary" if index == 0 else "outline",
                       size=9, padx=12, pady=8).pack(fill="x", pady=(0, 7))
        FlatButton(inner, self.app, "BACK TO TITLE",
                   self.g(self.hide_presentation), "outline",
                   size=8, padx=12, pady=7).pack(anchor="e", pady=(6, 0))
        self.presentation_panel = panel

    def hide_presentation(self):
        if self.presentation_panel is None:
            return
        try:
            self.presentation_panel.destroy()
        except Exception:
            pass
        self.presentation_panel = None

    def on_key(self, name, pressed):
        if name == "pause" and pressed:
            self.hide_presentation()

    # -- actions -------------------------------------------------------
    def start(self, _event=None):
        callsign, error = validate_callsign(self.entry.get())
        if callsign is None:
            self.hint.configure(text=error.upper(), fg=YELLOW)
            self.entry.focus_set()
            return
        self.app.callsign = callsign
        self.app.show_auth()


class AuthScreen(Screen):
    CHECKS = ("LOCAL PROFILE", "PILOT RECORD", "SESSION TOKEN")

    def __init__(self, parent, app):
        Screen.__init__(self, parent, app)
        self.step = 0
        self.total = 26
        self.finished = False
        self.token = ""
        self.progress = 0.0
        self.heading_font = tkfont.Font(family=SANS, size=18, weight="bold")

        holder = tk.Frame(self, bg=BG)
        holder.pack(fill="both", expand=True)
        self.card = tk.Frame(holder, bg=BG, highlightthickness=1,
                             highlightbackground=MUTED)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.84)

        body = tk.Frame(self.card, bg=BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG, width=250)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.art = tk.Canvas(left, bg=BG, height=246, bd=0,
                             highlightthickness=0, takefocus=0)
        self.art.pack(fill="x")
        self.art.bind("<Configure>", self.g(self.draw_art))
        tk.Label(left, text=tracked("Local identity"), font=fnt(8),
                 bg=BG, fg=TEXT, anchor="w").pack(fill="x", padx=18)
        tk.Label(left, text="LOCAL PROFILE // OFFLINE", font=fnt(7, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x", padx=18,
                                                     pady=(4, 0))
        tk.Frame(left, bg=MUTED, height=1).pack(fill="x", padx=18, pady=(12, 8))
        for scope in ("callsign", "local record", "flight log"):
            row = tk.Frame(left, bg=BG)
            row.pack(fill="x", padx=18, pady=2)
            tk.Label(row, text="▪", font=fnt(8, mono=True), bg=BG,
                     fg=YELLOW).pack(side="left")
            tk.Label(row, text=scope, font=fnt(8, mono=True), bg=BG,
                     fg=MUTED).pack(side="left", padx=(7, 0))

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(right, bg=BG)
        inner.pack(fill="both", expand=True, padx=22, pady=20)

        tk.Label(inner, text="LOCAL SESSION // OFFLINE",
                 font=fnt(8, mono=True), bg=BG, fg=MUTED,
                 anchor="w").pack(fill="x")
        self.heading = tk.Label(inner, text=tracked("Pilot check"),
                                font=self.heading_font, bg=BG, fg=YELLOW,
                                anchor="w")
        self.heading.pack(fill="x", pady=(6, 8))
        self.intro = tk.Label(
            inner,
            text=("This is a local pilot check. No account is created, no data "
                  "is sent, and no network connection is opened. The code below "
                  "is generated on this computer."),
            font=fnt(9), bg=BG, fg=TEXT, anchor="w", justify="left",
            wraplength=420)
        self.intro.pack(fill="x")

        progress_row = tk.Frame(inner, bg=BG)
        progress_row.pack(fill="x", pady=(16, 4))
        self.bar = ProgressBar(progress_row, app, 10)
        self.bar.pack(side="left", fill="x", expand=True)
        self.percent = tk.Label(progress_row, text="000%",
                                font=fnt(9, "bold", mono=True), bg=BG,
                                fg=YELLOW, width=5, anchor="e")
        self.percent.pack(side="right", padx=(10, 0))
        self.status = tk.Label(inner,
                               text="PREPARING LOCAL PILOT PROFILE",
                               font=fnt(8, mono=True), bg=BG, fg=MUTED,
                               anchor="w")
        self.status.pack(fill="x")

        check_panel = tk.Frame(inner, bg=BG, highlightthickness=1,
                               highlightbackground=MUTED)
        check_panel.pack(fill="x", pady=(12, 0))
        checks_inner = tk.Frame(check_panel, bg=BG)
        checks_inner.pack(fill="x", padx=12, pady=8)
        self.check_states = []
        for index, name in enumerate(self.CHECKS):
            row = tk.Frame(checks_inner, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text="0{0}".format(index + 1),
                     font=fnt(8, mono=True), bg=BG, fg=MUTED,
                     width=3, anchor="w").pack(side="left")
            tk.Label(row, text=name, font=fnt(8, mono=True), bg=BG,
                     fg=TEXT, anchor="w").pack(side="left")
            state = tk.Label(row, text="WAIT", font=fnt(8, "bold", mono=True),
                             bg=BG, fg=MUTED, anchor="e")
            state.pack(side="right")
            self.check_states.append(state)

        token_panel = tk.Frame(inner, bg=BG, highlightthickness=1,
                               highlightbackground=MUTED)
        token_panel.pack(fill="x", pady=(10, 0))
        token_inner = tk.Frame(token_panel, bg=BG)
        token_inner.pack(fill="x", padx=12, pady=8)
        self.token_head = tk.Label(token_inner,
                                   text="LOCAL SESSION CODE · PENDING",
                                   font=fnt(7, mono=True), bg=BG, fg=MUTED,
                                   anchor="w")
        self.token_head.pack(fill="x")
        self.token_label = tk.Label(token_inner, text="—",
                                    font=fnt(8, mono=True), bg=BG, fg=TEXT,
                                    anchor="w", justify="left", wraplength=400)
        self.token_label.pack(fill="x", pady=(4, 0))

        self.continue_button = FlatButton(inner, app, "ENTER THE COCKPIT",
                                          self.g(self.proceed), "primary",
                                          size=10, padx=18, pady=8)
        self.continue_button.pack(anchor="e", pady=(14, 0))
        self.continue_button.set_enabled(False)

        self.card.bind("<Configure>", self.g(self.on_resize))
        self.app.schedule(280, self.advance)

    def draw_art(self, _event=None):
        w = self.art.winfo_width()
        h = self.art.winfo_height()
        if w < 20 or h < 20:
            return
        visuals3d.draw_crew_portrait(self.art, "astronaut", w, h,
                                     tag="auth3d")
        self.art.create_text(12, 12, anchor="nw", text="LOCAL IDENTITY",
                             fill=YELLOW, font=fnt(7, "bold", mono=True),
                             tags="auth3d")
        self.art.create_text(12, h - 12, anchor="sw", text="LOCAL // OFFLINE",
                             fill=MUTED, font=fnt(7, mono=True),
                             tags="auth3d")

    def on_resize(self, event):
        width = max(240, event.width - 64)
        self.intro.configure(wraplength=min(420, width))
        self.token_label.configure(wraplength=min(420, width))
        # The tracked heading must fit inside the right column at 900px too.
        available = max(220, event.width - 294)
        size = 18
        while size > 12:
            self.heading_font.configure(size=size)
            if self.heading_font.measure(tracked("Pilot check")) <= available:
                break
            size -= 1

    def advance(self):
        if not self.winfo_exists() or self.finished:
            return
        if self.step >= self.total:
            self.finish()
            return
        self.step += 1
        fraction = self.step / float(self.total)
        self.progress = fraction
        self.bar.set(fraction)
        self.percent.configure(text="{0:03d}%".format(int(round(fraction * 100))))
        blocked = 0 if fraction < 0.30 else (1 if fraction < 0.65 else 2)
        for index, state in enumerate(self.check_states):
            if index < blocked:
                state.configure(text="OK", fg=YELLOW)
            elif index == blocked:
                state.configure(text="ACTIVE", fg=TEXT)
            else:
                state.configure(text="WAIT", fg=MUTED)
        if fraction < 0.35:
            self.status.configure(text="PREPARING LOCAL PILOT PROFILE")
        elif fraction < 0.70:
            self.status.configure(text="READING LOCAL RECORD · NO NETWORK")
        else:
            self.status.configure(text="ISSUING LOCAL SESSION CODE")
        self.draw_art()
        if self.step >= self.total:
            self.finish()
            return
        self.app.schedule(105, self.advance)

    def finish(self):
        if self.finished:
            return
        self.finished = True
        seed = "{0}|{1}|{2}".format(self.app.callsign, time.time(), random.random())
        self.token = "pilot_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:40]
        self.progress = 1.0
        self.bar.set(1.0)
        self.percent.configure(text="100%")
        for state in self.check_states:
            state.configure(text="OK", fg=YELLOW)
        self.token_head.configure(
            text="LOCAL SESSION CODE · ISSUED LOCALLY", fg=YELLOW)
        self.token_label.configure(text=self.token)
        self.status.configure(text="LOCAL SESSION READY", fg=YELLOW)
        self.draw_art()
        self.continue_button.set_enabled(True)

    def proceed(self):
        if not self.finished:
            return
        self.app.start_missions()


class ChoiceCard(tk.Frame):
    """A clickable flight-plan card with rank, points and a hover state."""

    def __init__(self, parent, app, number, label, points, rank, command):
        tk.Frame.__init__(self, parent, bg=BG, bd=0,
                          highlightthickness=1, highlightbackground=MUTED,
                          highlightcolor=MUTED)
        self.app = app
        self.command = command
        self.enabled = False
        self.hover = False
        self.last_click = 0.0

        self.inner = tk.Frame(self, bg=BG)
        self.inner.pack(fill="both", expand=True, padx=10, pady=8)

        self.number_box = tk.Frame(self.inner, bg=BG, width=38, height=38,
                                   highlightthickness=1,
                                   highlightbackground=MUTED)
        self.number_box.pack(side="left")
        self.number_box.pack_propagate(False)
        self.number_label = tk.Label(self.number_box, text=str(number),
                                     font=fnt(13, "bold", mono=True),
                                     bg=BG, fg=YELLOW)
        self.number_label.place(relx=0.5, rely=0.5, anchor="center")

        self.copy = tk.Frame(self.inner, bg=BG)
        self.copy.pack(side="left", fill="x", expand=True, padx=(12, 8))
        self.title_label = tk.Label(self.copy, text=label,
                                    font=fnt(10, "bold"), bg=BG, fg=YELLOW,
                                    anchor="w", justify="left")
        self.title_label.pack(fill="x")
        self.meta_label = tk.Label(
            self.copy, text="DECISION {0:+d}  ·  {1}".format(points, rank),
            font=fnt(7, mono=True), bg=BG, fg=MUTED, anchor="w")
        self.meta_label.pack(fill="x", pady=(3, 0))

        self.arrow = tk.Label(self.inner, text="→", font=fnt(15, "bold"),
                              bg=BG, fg=YELLOW)

        self.arrow.pack(side="right")
        self.widgets = (self, self.inner, self.number_box, self.number_label,
                        self.copy, self.title_label, self.meta_label,
                        self.arrow)
        for widget in self.widgets:
            widget.bind("<Button-1>", self.on_press)
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
        self.apply()

    def apply(self):
        if not self.enabled:
            bg, fg, border = BG, MUTED, MUTED
            number_bg, number_fg, meta = BG, MUTED, MUTED
        elif self.hover:
            bg, fg, border = YELLOW, BG, YELLOW
            number_bg, number_fg, meta = BG, YELLOW, BG
        else:
            bg, fg, border = BG, YELLOW, MUTED
            number_bg, number_fg, meta = BG, YELLOW, MUTED
        self.configure(bg=bg, highlightbackground=border, highlightcolor=border)
        self.inner.configure(bg=bg)
        self.copy.configure(bg=bg)
        self.number_box.configure(bg=bg, highlightbackground=border,
                                  highlightcolor=border)
        self.number_label.configure(bg=number_bg, fg=number_fg)
        self.title_label.configure(bg=bg, fg=fg)
        self.meta_label.configure(bg=bg, fg=meta)
        self.arrow.configure(bg=bg, fg=fg)
        try:
            cursor = "hand2" if self.enabled else "arrow"
            for widget in self.widgets:
                widget.configure(cursor=cursor)
        except tk.TclError:
            pass

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.hover = False
        self.apply()

    def _contains(self, widget):
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def on_enter(self, _event=None):
        if self.enabled and not self.hover:
            self.hover = True
            self.apply()

    def on_leave(self, event=None):
        inside = False
        if event is not None:
            try:
                inside = self._contains(self.winfo_containing(event.x_root,
                                                               event.y_root))
            except Exception:
                inside = False
        if not inside and self.hover:
            self.hover = False
            self.apply()

    def on_press(self, _event=None):
        if not self.enabled:
            return
        now = time.monotonic()
        if now - self.last_click < 0.25:
            return
        self.last_click = now
        audio = getattr(self.app, "audio", None)
        if audio is not None:
            audio.play("click", 0.18)
        if self.command is not None:
            self.command()


class MissionScreen(Screen):
    CAPCOM = (
        "Load is a combustion problem, not a plumbing one. Methane, oxygen, "
        "and a metered two percent of Tibanna.",
        "The droid has the descent. Trust the automation, or take it and own "
        "the deck.",
        "Read the rocks before they read you. Keep the shield between the "
        "hull and the field.",
    )

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
        self.app.audio.loop("ambient", 0.08)
        self.build()
        self.art.bind("<Configure>", self.g(self.draw_art))
        self.right.bind("<Configure>", self.g(self.on_right_resize))
        self.app.schedule(120, self.draw_tip_portrait)
        self.app.schedule(240, self.type_step)

    def build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=28, pady=(16, 0))
        tk.Label(bar, text="MISSION {0:02d} / 03 · {1}".format(
            self.index + 1, self.mission["tag"]),
            font=fnt(9, "bold", mono=True), bg=BG, fg=MUTED).pack(side="left")
        if self.app.presentation:
            tk.Label(bar, text="PRESENTATION", font=fnt(8, "bold", mono=True),
                     bg=BG, fg=YELLOW).pack(side="left", padx=(12, 0))
        self.score_label = tk.Label(bar, text=score_text(self.app.score),
                                    font=fnt(9, "bold", mono=True), bg=BG,
                                    fg=YELLOW)
        self.score_label.pack(side="right")
        self.pips = tk.Canvas(bar, width=62, height=8, bg=BG, bd=0,
                              highlightthickness=0, takefocus=0)
        self.pips.pack(side="right", padx=(0, 16))
        for i in range(3):
            fill = YELLOW if i < self.index else (TEXT if i == self.index else BG)
            self.pips.create_rectangle(i * 20 + 1, 1, i * 20 + 17, 7,
                                       fill=fill, outline=MUTED)
        tk.Label(bar, text="BRIEFING", font=fnt(8, "bold", mono=True),
                 bg=BG, fg=TEXT).pack(side="right", padx=(0, 16))
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=28, pady=(10, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=14)
        body.columnconfigure(0, weight=5, minsize=240)
        body.columnconfigure(1, weight=7, minsize=320)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 22))
        art_head = tk.Frame(left, bg=BG)
        art_head.pack(fill="x", pady=(0, 7))
        tk.Label(art_head, text="OPTICAL FEED // 0{0}".format(self.index + 1),
                 font=fnt(7, mono=True), bg=BG, fg=MUTED).pack(side="left")
        tk.Label(art_head, text="LOCAL RENDER", font=fnt(7, mono=True),
                 bg=BG, fg=YELLOW).pack(side="right")
        self.art = tk.Canvas(left, bg=BG, width=320, height=320, bd=0,
                             highlightthickness=1, highlightbackground=MUTED)
        self.art.pack(fill="both", expand=True)
        tk.Label(left, text=self.mission["caption"], font=fnt(8, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x", pady=(8, 0))

        tip_panel = tk.Frame(left, bg=BG, highlightthickness=1,
                             highlightbackground=MUTED)
        tip_panel.pack(fill="x", pady=(8, 0))
        self.tip_canvas = tk.Canvas(tip_panel, width=48, height=48, bg=BG,
                                    bd=0, highlightthickness=0, takefocus=0)
        self.tip_canvas.pack(side="left", padx=(5, 7), pady=3)
        tip_copy = tk.Frame(tip_panel, bg=BG)
        tip_copy.pack(side="left", fill="x", expand=True, pady=3)
        tk.Label(tip_copy, text="K-3PO · MISSION CONTROL",
                 font=fnt(7, "bold", mono=True), bg=BG, fg=YELLOW,
                 anchor="w").pack(fill="x")
        self.tip_label = tk.Label(tip_copy, text=self.CAPCOM[self.index],
                                  font=fnt(8), bg=BG, fg=TEXT, anchor="w",
                                  justify="left", wraplength=300)
        self.tip_label.pack(fill="x")

        self.right = tk.Frame(body, bg=BG)
        self.right.grid(row=0, column=1, sticky="nsew")
        tk.Label(self.right, text="MISSION {0:02d} / 03  ·  FLIGHT PLAN".format(
            self.index + 1), font=fnt(8, mono=True), bg=BG, fg=MUTED,
            anchor="w").pack(fill="x")
        self.title_label = tk.Label(self.right, text=self.mission["title"],
                                    font=fnt(17, "bold"), bg=BG, fg=YELLOW,
                                    anchor="w", justify="left", wraplength=460)
        self.title_label.pack(fill="x", pady=(5, 7))

        meta = tk.Frame(self.right, bg=BG)
        meta.pack(fill="x", pady=(0, 8))
        max_points = max(option["points"] for option in self.mission["options"])
        for caption, value in (("THREAT", ("LOW", "MEDIUM", "HIGH")[self.index]),
                               ("DECISION CAP", "+{0}".format(max_points)),
                               ("FLIGHT BONUS", "+30")):
            chip = tk.Frame(meta, bg=BG, highlightthickness=1,
                            highlightbackground=MUTED)
            chip.pack(side="left", padx=(0, 7))
            chip_inner = tk.Frame(chip, bg=BG)
            chip_inner.pack(padx=8, pady=5)
            tk.Label(chip_inner, text=caption, font=fnt(7, mono=True),
                     bg=BG, fg=MUTED).pack(anchor="w")
            tk.Label(chip_inner, text=value, font=fnt(9, "bold", mono=True),
                     bg=BG, fg=TEXT).pack(anchor="w")

        self.text = tk.Label(self.right, text="", font=fnt(10), bg=BG, fg=TEXT,
                             anchor="nw", justify="left", wraplength=460)
        self.text.pack(fill="x", pady=(0, 8))
        tk.Label(self.right, text=tracked(self.mission["prompt"]),
                 font=fnt(8), bg=BG, fg=MUTED, anchor="w",
                 justify="left").pack(fill="x", pady=(0, 2))
        select_head = tk.Frame(self.right, bg=BG)
        select_head.pack(fill="x", pady=(7, 5))
        tk.Label(select_head, text="SELECT FLIGHT PLAN", font=fnt(7, "bold", mono=True),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(select_head, text="KEYS 1–3", font=fnt(7, mono=True),
                 bg=BG, fg=MUTED).pack(side="right")
        ranks = ("SAFE", "BOLD", "EXTREME")
        for i, option in enumerate(self.mission["options"]):
            card = ChoiceCard(self.right, self.app, i + 1, option["label"],
                              option["points"], ranks[option_rank(self.mission, option)],
                              self.g(self.make_choice(i)))
            card.pack(fill="both", expand=True, pady=(0, 7))
            self.buttons.append(card)

    def make_choice(self, index):
        return lambda: self.choose(index)

    def on_right_resize(self, event):
        width = max(180, event.width - 2)
        self.title_label.configure(wraplength=width)
        self.text.configure(wraplength=width)

    # -- briefing ------------------------------------------------------
    def type_step(self):
        if not self.winfo_exists() or self.ready:
            return
        if self.typed >= len(self.briefing):
            self.finish_typing()
            return
        self.typed += 1
        self.text.configure(text=self.briefing[:self.typed])
        self.app.schedule(12, self.type_step)

    def finish_typing(self):
        self.typed = len(self.briefing)
        self.text.configure(text=self.briefing)
        if self.ready:
            return
        self.ready = True
        for button in self.buttons:
            button.set_enabled(True)

    def on_digit(self, digit):
        if self.locked or not self.ready:
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
        self.app.audio.play("confirm", 0.30)
        self.app.begin_flight(self.index, option)

    # -- line art ------------------------------------------------------
    def draw_art(self, _event=None):
        c = self.art
        c.delete("all")
        width = c.winfo_width()
        height = c.winfo_height()
        if width < 60 or height < 60:
            return
        visuals3d.draw_mission(c, self.index, width, height, tag="art3d")
        c.create_text(14, 14, anchor="nw", text="MISSION 0{0}".format(self.index + 1),
                      fill=YELLOW, font=fnt(8, "bold", mono=True))
        c.create_text(width - 14, 14, anchor="ne", text="{0} / 03".format(self.index + 1),
                      fill=MUTED, font=fnt(7, mono=True))
        visuals.draw_corner_marks(c, 12, 12, width - 12, height - 12, MUTED, 10)
        c.create_text(width - 14, height - 14, anchor="se",
                      text="NO UPLINK", fill=MUTED, font=fnt(7, mono=True))

    def draw_tip_portrait(self, _event=None):
        canvas = self.tip_canvas
        if not canvas.winfo_exists():
            return
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 20 or height < 20:
            self.app.schedule(80, self.draw_tip_portrait)
            return
        visuals3d.draw_crew_portrait(canvas, "astromech", width, height,
                                     tag="tip")
        canvas.create_text(width / 2, height - 4, anchor="s", text="K-3PO",
                           fill=YELLOW, font=fnt(6, "bold", mono=True),
                           tags="tip")

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
    SLOW_FACTOR = 0.35

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
        self.slowmo = False
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
        self.last_beep = None
        self.capcom_text = ""
        self.app.audio.loop("engine", 0.08)
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
        self.score_label = tk.Label(right, text=score_text(self.app.score),
                                    font=fnt(8, mono=True), bg=BG, fg=MUTED)
        self.score_label.pack(side="left", padx=(0, 14))
        self.clock_label = tk.Label(right, text="T-03.0", font=fnt(10, "bold", mono=True),
                                    bg=BG, fg=YELLOW)
        self.clock_label.pack(side="left", padx=(0, 10))
        FlatButton(right, self.app, "PAUSE", self.g(self.toggle_pause),
                   "outline", size=8, padx=10, pady=5).pack(side="left")
        profile_text = "PROFILE · " + self.option["label"]
        if self.app.presentation:
            profile_text += "  ·  PRESENTATION"
        self.profile_label = tk.Label(
            self, text=profile_text, font=fnt(8, mono=True),
            bg=BG, fg=MUTED, anchor="w")
        self.profile_label.pack(fill="x", padx=26, pady=(4, 0))
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=26, pady=(8, 0))
        self.canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=26)
        self.canvas.bind("<Configure>", self.g(self.draw))
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=26, pady=(4, 10))
        self.capcom_canvas = tk.Canvas(bottom, width=38, height=38, bg=BG,
                                      bd=0, highlightthickness=0,
                                      takefocus=0)
        self.capcom_canvas.pack(side="left", padx=(0, 8))
        capcom = tk.Frame(bottom, bg=BG)
        capcom.pack(side="left", fill="x", expand=True)
        director = self.mode == "load"
        self.capcom_name = tk.Label(
            capcom,
            text="FLIGHT DIRECTOR · MAJOR VEGA" if director else "CAPCOM · R2-D2",
            font=fnt(7, "bold", mono=True), bg=BG, fg=YELLOW, anchor="w")
        self.capcom_name.pack(fill="x")
        self.hint = tk.Label(capcom, text="", font=fnt(8), bg=BG, fg=TEXT,
                             anchor="w", justify="left", wraplength=480)
        self.hint.pack(fill="x")
        if self.mode == "load":
            controls = "↑ / ↓  TRIM MIXTURE  ·  P PAUSE  ·  M SLOW-MO"
        elif self.mode == "landing":
            controls = "SPACE / ↑  LANDING BURN  ·  ← →  RCS  ·  P PAUSE"
        else:
            controls = "← →  STEER  ·  AVOID THE DEBRIS  ·  P PAUSE  ·  M SLOW-MO"
        self.controls = tk.Label(capcom, text=controls, font=fnt(6, mono=True),
                                 bg=BG, fg=MUTED, anchor="w")
        self.controls.pack(fill="x")
        self.status = tk.Label(bottom, text="", font=fnt(8, mono=True),
                               bg=BG, fg=MUTED, anchor="e")
        self.status.pack(side="right")
        bottom.bind("<Configure>", self.g(self.on_bottom_resize))
        self.app.schedule(140, self.draw_capcom_portrait)

    def on_bottom_resize(self, event):
        self.hint.configure(wraplength=max(150, event.width - 150))

    def draw_capcom_portrait(self, _event=None):
        canvas = self.capcom_canvas
        if not canvas.winfo_exists():
            return
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 16 or height < 16:
            self.app.schedule(80, self.draw_capcom_portrait)
            return
        kind = "astronaut" if self.mode == "load" else "astromech"
        visuals3d.draw_crew_portrait(canvas, kind, width, height,
                                     tag="capcom")

    def update_capcom(self):
        if self.phase == "countdown":
            text = "Hold for telemetry. Watch the band; I will call the limits."
        elif self.mode == "load":
            error = abs(self.mix - self.target)
            if self.strain > 1.6:
                text = "Injector strain is climbing. Ease back into the band."
            elif error <= self.band:
                text = "Good. Hold that mixture; the stack is happy."
            elif self.mix < self.target:
                text = "Mixture is lean. Bring it up, gently."
            else:
                text = "Mixture is rich. Trim it down, gently."
        elif self.mode == "landing":
            if self.alt > 600:
                text = "You have altitude. Save the burn for the deck."
            elif self.fuel < 20:
                text = "Fuel is critical. One clean burn, no wasted taps."
            elif abs(self.x) > self.target_half * 2:
                text = "You are drifting. RCS toward the centre."
            elif self.alt < 220 and not self.burning:
                text = "Light the engine. Now."
            else:
                text = "Small inputs. Let the deck come to you."
        else:
            nearest = min(self.debris,
                          key=lambda rock: abs(rock["y"] - 0.88),
                          default=None)
            if self.hull <= 1:
                text = "Hull critical. Keep the nose clean."
            elif nearest is not None and nearest["x"] < self.ship_x - 0.08:
                text = "Rock on your left. Ease right."
            elif nearest is not None and nearest["x"] > self.ship_x + 0.08:
                text = "Rock on your right. Ease left."
            else:
                text = "Steady. Thread the gap and keep the shield up."
        if text != self.capcom_text:
            self.capcom_text = text
            self.hint.configure(text=text)

    # -- input ---------------------------------------------------------
    def on_key(self, name, pressed):
        if name == "pause":
            if pressed:
                self.toggle_pause()
            return
        if name == "slow":
            if pressed:
                self.toggle_slowmo()
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
            self.app.audio.stop_loop()
            self.show_pause()
        else:
            self.app.audio.loop("engine", 0.08)
            self.hide_pause()
        self.app.audio.play("click", 0.20)

    def toggle_slowmo(self):
        if self.phase == "ending" or self.delivered:
            return
        self.slowmo = not self.slowmo
        self.app.audio.play("click", 0.18)

    def show_pause(self):
        self.pause_overlay = tk.Frame(self, bg=BG)
        self.pause_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.pause_overlay.lift()
        card = tk.Frame(self.pause_overlay, bg=BG, highlightthickness=1,
                        highlightbackground=YELLOW)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.5)
        inner = tk.Frame(card, bg=BG)
        inner.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(inner, text="MISSION {0:02d} / 03  ·  LOCAL SESSION".format(
            self.index + 1), font=fnt(8, mono=True), bg=BG, fg=MUTED).pack()
        tk.Label(inner, text=tracked("Simulation held"), font=fnt(16, "bold"),
                 bg=BG, fg=YELLOW).pack(pady=(6, 0))
        tk.Label(inner, text="CONTROLS FROZEN · TELEMETRY PAUSED",
                 font=fnt(8, mono=True), bg=BG, fg=TEXT).pack(pady=(5, 0))
        tk.Frame(inner, bg=MUTED, height=1).pack(fill="x", pady=(12, 0))
        tk.Label(inner, text="Flight controls are frozen. Resume when ready.",
                 font=fnt(9), bg=BG, fg=MUTED, wraplength=340,
                 justify="center").pack(pady=(12, 14))
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
            sim_dt = dt * (self.SLOW_FACTOR if self.slowmo else 1.0)
            if self.phase == "countdown":
                self.countdown -= sim_dt
                number = max(1, int(math.ceil(self.countdown)))
                if number != self.last_beep:
                    self.last_beep = number
                    self.app.audio.play("warning", 0.16)
                if self.countdown <= 0:
                    self.countdown = 0.0
                    self.phase = "flying"
                    self.app.audio.play("confirm", 0.22)
            elif self.phase == "flying":
                self.elapsed += sim_dt
                if self.mode == "load":
                    self.step_load(sim_dt)
                elif self.mode == "landing":
                    self.step_landing(sim_dt)
                else:
                    self.step_debris(sim_dt)
            if self.phase == "ending":
                self.end_delay -= sim_dt
                self.shake = max(0.0, self.shake - sim_dt * 26.0)
                if self.end_delay <= 0 and not self.delivered:
                    self.delivered = True
                    self.app.complete_flight(self.index, self.option, self.result)
                    return
            self.update_particles(sim_dt)
            self.flash = max(0.0, self.flash - sim_dt * 3.0)
        self.update_hud()
        self.update_capcom()
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
        self.app.audio.stop_loop()
        self.app.audio.play("success" if success else "impact", 0.32)
        if not success:
            self.shake = 14.0
            self.spawn_burst(0.5, 0.78, 22)

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
                                       "miss": miss, "fuel": self.fuel,
                                       "target_half": self.target_half},
                            "VEHICLE LOST")
            else:
                points = 10 if miss <= self.target_half * 0.35 else (7 if miss <= self.target_half else 4)
                points += 10 if speed <= 3.0 else (7 if speed <= 5.0 else (4 if speed <= 7.5 else 2))
                points += 10 if self.fuel >= 30.0 else (6 if self.fuel >= 15.0 else (3 if self.fuel > 0 else 0))
                self.finish(True, min(30, points),
                            {"mode": "landing", "speed": speed, "miss": miss,
                             "fuel": self.fuel, "target_half": self.target_half},
                            "TOUCHDOWN")
        elif self.run_time > 45.0:
            self.finish(False, 0, {"mode": "landing", "speed": abs(self.vy),
                                   "miss": abs(self.x), "fuel": self.fuel,
                                   "target_half": self.target_half},
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
        if self.mode == "load":
            self.draw_load(c, w, h)
        elif self.mode == "landing":
            self.draw_landing(c, w, h)
        else:
            self.draw_debris(c, w, h)
        self.draw_particles(c, w, h)
        scan_y = 16 + (self.elapsed * 26.0) % max(20.0, h - 32.0)
        c.create_line(10, scan_y, w - 10, scan_y, fill=visuals.GRID)
        visuals.draw_corner_marks(c, 12, 12, w - 12, h - 12, MUTED, 13)
        if self.slowmo:
            self.draw_slowmo(c, w, h)
        if self.phase == "countdown":
            number = max(1, int(math.ceil(self.countdown)))
            cx, cy = w / 2.0, h / 2.0
            radius = min(88.0, min(w, h) * 0.23)
            c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                          fill=BG, outline=MUTED)
            c.create_oval(cx - radius + 8, cy - radius + 8,
                          cx + radius - 8, cy + radius - 8,
                          outline=YELLOW, dash=(2, 4))
            for tick in range(12):
                angle = math.radians(tick * 30.0)
                inner = radius - 14
                outer = radius - 6
                c.create_line(cx + inner * math.cos(angle),
                              cy + inner * math.sin(angle),
                              cx + outer * math.cos(angle),
                              cy + outer * math.sin(angle), fill=MUTED)
            remaining = max(0.0, min(1.0, self.countdown / 3.0))
            c.create_arc(cx - radius + 2, cy - radius + 2,
                         cx + radius - 2, cy + radius - 2,
                         start=90, extent=-359 * remaining,
                         style="arc", outline=YELLOW, width=2)
            c.create_text(cx, cy - 6, text=str(number),
                          fill=YELLOW, font=fnt(38, "bold", mono=True))
            c.create_text(cx, cy + radius - 28, text=tracked("Flight controls"),
                          fill=TEXT, font=fnt(8))
            c.create_text(cx, cy + radius - 12, text="HOLD FOR TELEMETRY",
                          fill=MUTED, font=fnt(7, mono=True))
        if self.phase == "ending" and self.result is not None:
            colour = YELLOW if self.success else MUTED
            c.create_rectangle(w * 0.22, h * 0.38, w * 0.78, h * 0.62,
                               fill=BG, outline=colour)
            visuals.draw_corner_marks(c, w * 0.22, h * 0.38,
                                      w * 0.78, h * 0.62, colour, 12)
            c.create_text(w / 2, h * 0.44, text=tracked(self.result["title"]),
                          fill=colour, font=fnt(15, "bold"))
            c.create_text(w / 2, h * 0.51,
                          text="PERFORMANCE +{0:02d} · DEBRIEF".format(self.bonus),
                          fill=TEXT, font=fnt(8, mono=True))
            c.create_text(w / 2, h * 0.56, text="PRESS CONTINUE TO FILE THE FLIGHT",
                          fill=MUTED, font=fnt(7, mono=True))
        if self.shake > 0.2:
            c.move("all", random.uniform(-self.shake, self.shake),
                   random.uniform(-self.shake, self.shake))
        if self.flash > 0:
            c.create_rectangle(2, 2, w - 2, h - 2, outline=YELLOW, width=2)

    def draw_slowmo(self, c, w, h):
        for y in range(8, int(h) - 8, 10):
            c.create_line(0, y, w, y, fill="#0E161F")
        c.create_rectangle(0, 0, w, 8, fill=BG, outline="")
        c.create_rectangle(0, h - 8, w, h, fill=BG, outline="")
        for inset, colour in ((6, "#1A242E"), (14, "#101820")):
            c.create_rectangle(inset, inset, w - inset, h - inset,
                               outline=colour)
        c.create_rectangle(4, 4, w - 4, h - 4, outline=YELLOW)
        bar_width = min(236, max(170, w * 0.32))
        c.create_rectangle(w / 2 - bar_width / 2, 16,
                           w / 2 + bar_width / 2, 48,
                           fill=BG, outline=YELLOW)
        c.create_text(w / 2, 24, text="SLOW MOTION · {0:.2f}×".format(
            self.SLOW_FACTOR), fill=YELLOW, font=fnt(8, "bold", mono=True))
        c.create_text(w / 2, 37, text="M TO RELEASE · TELEMETRY LIVE",
                      fill=TEXT, font=fnt(7, mono=True))

    def draw_load(self, c, w, h):
        visuals3d.draw_flight_load(c, self.load, self.mix, self.target,
                                   self.band, self.strain, w, h,
                                   tag="scene", elapsed=self.elapsed)
        c.create_rectangle(0, 0, w * 0.20, h, fill=BG, outline="",
                           stipple="gray50")
        c.create_rectangle(w * 0.24, 0, w * 0.40, h, fill=BG, outline="",
                           stipple="gray25")
        c.create_rectangle(w * 0.58, 0, w, h, fill=BG, outline="",
                           stipple="gray50")
        top, bottom = h * 0.18, h * 0.82
        tank_x = w * 0.045
        tank_w = min(72, w * 0.085)
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
        gx = w * 0.31
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
        tx = w * 0.66
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
        visuals3d.draw_flight_landing(c, self.alt, self.alt_max, self.x,
                                      self.burning, self.fuel, w, h,
                                      tag="scene", elapsed=self.elapsed)
        deck_y = h - 46.0
        max_alt = self.alt_max
        def alt_y(value):
            value = max(0.0, min(max_alt, value))
            return 42.0 + (1.0 - value / max_alt) * (deck_y - 42.0)
        for tick in range(200, 801, 200):
            y = alt_y(tick)
            c.create_line(w * 0.30, y, w * 0.94, y, fill=MUTED, dash=(2, 6))
            c.create_text(w * 0.30, y - 6, text="{0} M".format(tick), anchor="w",
                          fill=MUTED, font=fnt(7, mono=True))
        wind = self.wind_strength * math.sin(self.run_time * 0.85 + 0.5)
        for i in range(3):
            y = 54 + i * 14
            length = 10 + abs(wind) * 8
            c.create_line(w - 34, y, w - 34 - length, y, fill=MUTED)
            c.create_line(w - 34 - length, y, w - 40 - length, y - 3, fill=MUTED)
        c.create_text(w - 14, 18, anchor="ne", text="WIND {0:+.1f}".format(wind),
                      fill=MUTED, font=fnt(8, mono=True))
        c.create_rectangle(6, 6, 200, 74, fill=BG, outline=MUTED)
        visuals.draw_corner_marks(c, 6, 6, 200, 74, visuals.GRID, 7)
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
        visuals3d.draw_flight_debris(c, self.ship_x, self.debris, self.hull,
                                     self.max_hull, w, h, tag="scene",
                                     elapsed=self.elapsed)
        c.create_rectangle(6, 6, 172, 34, fill=BG, outline=MUTED)
        c.create_text(14, 18, anchor="nw", text="HULL", fill=MUTED, font=fnt(8, mono=True))
        for i in range(self.max_hull):
            x = 54 + i * 15
            c.create_rectangle(x, 18, x + 10, 26,
                               fill=YELLOW if i < self.hull else BG, outline=MUTED)
        c.create_text(w - 14, 18, anchor="ne", text="{0:04.1f}S".format(max(0.0, 20.0 - self.run_time)),
                      fill=YELLOW, font=fnt(10, "bold", mono=True))
        c.create_text(w - 14, 38, anchor="ne", text="CLOSE CALLS {0}".format(self.close_calls),
                      fill=MUTED, font=fnt(8, mono=True))
        visuals.draw_radar(c, 52, h - 58, min(28.0, h * 0.075), YELLOW, MUTED)
        if self.hull <= 1:
            c.create_text(w - 14, h - 14, anchor="se", text="HULL CRITICAL",
                          fill=YELLOW, font=fnt(8, "bold", mono=True))


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
        head_text = ("PRESENTATION · MISSION {0:02d}".format(index + 1)
                     if app.presentation else
                     "MISSION {0:02d} · DEBRIEF".format(index + 1))
        tk.Label(head, text=head_text,
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
        stats = record["stats"]
        metrics = dataviz.telemetry_metrics(stats, record["success"])
        self.chart = None
        if metrics:
            self.chart = MetricChart(pin, metrics, height=min(96, 30 * len(metrics) + 2))
            self.chart.pack(fill="x", pady=(8, 2))
            note = "TELEMETRY CAPTURED LOCALLY · NOT UPLOADED"
            if any(metric.target is not None for metric in metrics):
                note += " · YELLOW TICK = TARGET"
        else:
            note = self.stats_text(stats, record["success"])
        self.stats = tk.Label(pin, text=note,
                              font=fnt(8, mono=True), bg=BG, fg=MUTED,
                              anchor="w", justify="left", wraplength=600)
        self.stats.pack(fill="x", pady=(2, 0))
        bottom = tk.Frame(inner, bg=BG)
        bottom.pack(fill="x", pady=(16, 0))
        ledger = tk.Frame(bottom, bg=BG)
        ledger.pack(side="left", fill="x", expand=True)
        for caption, value in (("DECISION", "{0:+d}".format(record["option_points"])),
                               ("FLIGHT", "{0:+d}".format(record["bonus"])),
                               ("TOTAL", "{0:+d}".format(record["points"]))):
            cell = tk.Frame(ledger, bg=BG, highlightthickness=1,
                            highlightbackground=MUTED)
            cell.pack(side="left", fill="x", expand=True, padx=(0, 7))
            cell_inner = tk.Frame(cell, bg=BG)
            cell_inner.pack(fill="x", padx=9, pady=6)
            tk.Label(cell_inner, text=caption, font=fnt(7, mono=True),
                     bg=BG, fg=MUTED, anchor="w").pack(fill="x")
            tk.Label(cell_inner, text=value, font=fnt(14, "bold", mono=True),
                     bg=BG, fg=YELLOW if record["points"] > 0 else MUTED,
                     anchor="w").pack(fill="x")
        FlatButton(bottom, app, "BACK TO TITLE" if app.presentation else "CONTINUE",
                   self.g(app.advance), "primary",
                   size=10, padx=18, pady=8).pack(side="right", padx=(10, 0))

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
        self.card = tk.Frame(holder, bg=BG, highlightthickness=1,
                             highlightbackground=MUTED)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.90)

        inner = tk.Frame(self.card, bg=BG)
        inner.pack(fill="both", expand=True, padx=22, pady=16)
        inner.columnconfigure(0, weight=5, minsize=250)
        inner.columnconfigure(1, weight=7, minsize=320)
        inner.rowconfigure(0, weight=1)

        left = tk.Frame(inner, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        right = tk.Frame(inner, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(left, text=tracked("Flight log · Rebel Aerospace"),
                 font=fnt(7), bg=BG, fg=MUTED, anchor="w").pack(fill="x")
        self.headline_font = tkfont.Font(family=SANS, size=17, weight="bold")
        self.headline = tk.Label(left, text=tracked("Mission complete"),
                                 font=self.headline_font, bg=BG, fg=YELLOW,
                                 anchor="w")
        self.headline.pack(fill="x", pady=(5, 2))
        tk.Label(left, text="CALLSIGN · " + app.callsign,
                 font=fnt(9, mono=True), bg=BG, fg=TEXT, anchor="w").pack(fill="x")

        self.badge = tk.Canvas(left, bg=BG, height=176, bd=0,
                               highlightthickness=0, takefocus=0)
        self.badge.pack(fill="x", pady=(8, 0))
        self.badge.bind("<Configure>", self.g(self.draw_badge))

        if app.last_run_improved:
            record_text = "NEW PERSONAL BEST · SAVED LOCALLY"
        else:
            record_text = "PERSONAL BEST · {0:03d}".format(app.pilot.best_score)
        tk.Label(left, text=record_text, font=fnt(8, mono=True), bg=BG,
                 fg=YELLOW if app.last_run_improved else MUTED,
                 anchor="w").pack(fill="x", pady=(2, 0))

        score_row = tk.Frame(left, bg=BG)
        score_row.pack(fill="x", pady=(10, 0))
        tk.Label(score_row, text=str(app.score), font=fnt(30, "bold", mono=True),
                 bg=BG, fg=YELLOW, anchor="w").pack(side="left")
        tk.Label(score_row, text="/ " + str(MAX_SCORE), font=fnt(10, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(side="left", padx=(8, 0),
                                                    pady=(12, 0))
        tk.Label(left, text=tracked("Rank · " + rank_for(app.score)),
                 font=fnt(11, "bold"), bg=BG, fg=TEXT, anchor="w").pack(fill="x",
                                                                        pady=(2, 8))

        meta = tk.Frame(left, bg=BG)
        meta.pack(fill="x")
        for caption, value in (("FLIGHTS", "{0:02d}".format(app.pilot.flights)),
                               ("BEST", "{0:03d}".format(app.pilot.best_score))):
            cell = tk.Frame(meta, bg=BG, highlightthickness=1,
                            highlightbackground=MUTED)
            cell.pack(side="left", fill="x", expand=True, padx=(0, 7))
            cell_inner = tk.Frame(cell, bg=BG)
            cell_inner.pack(fill="x", padx=8, pady=5)
            tk.Label(cell_inner, text=caption, font=fnt(7, mono=True),
                     bg=BG, fg=MUTED, anchor="w").pack(fill="x")
            tk.Label(cell_inner, text=value, font=fnt(11, "bold", mono=True),
                     bg=BG, fg=TEXT, anchor="w").pack(fill="x")

        tk.Label(right, text="FLIGHT LOG // SCORE LEDGER", font=fnt(8, mono=True),
                 bg=BG, fg=MUTED, anchor="w").pack(fill="x")
        tk.Label(right, text="MISSION SCORE · MAX 130 EACH",
                 font=fnt(8, "bold"), bg=BG, fg=TEXT, anchor="w").pack(fill="x",
                                                                       pady=(4, 7))
        log_head = tk.Frame(right, bg=BG)
        log_head.pack(fill="x")
        tk.Label(log_head, text="MISSION", font=fnt(7, mono=True), bg=BG,
                 fg=MUTED, anchor="w").pack(side="left")
        tk.Label(log_head, text="VERDICT", font=fnt(7, mono=True), bg=BG,
                 fg=MUTED, anchor="w").pack(side="left", padx=(12, 0))
        tk.Label(log_head, text="PTS", font=fnt(7, mono=True), bg=BG,
                 fg=MUTED, anchor="e").pack(side="right")
        tk.Frame(right, bg=MUTED, height=1).pack(fill="x", pady=(4, 4))

        log = tk.Frame(right, bg=BG)
        log.pack(fill="x")
        for i, mission in enumerate(MISSIONS):
            result = app.results[i] if i < len(app.results) else None
            row = tk.Frame(log, bg=BG)
            row.pack(fill="x", pady=1)
            tag = "M{0:02d}  {1}".format(i + 1, mission["tag"][:20])
            tk.Label(row, text=tag, font=fnt(8, mono=True), bg=BG,
                     fg=TEXT, anchor="w").pack(side="left")
            if result is None:
                verdict, points, colour = "SKIPPED", "0", MUTED
            else:
                verdict = result["verdict"]
                points = "{0:+d}".format(result["points"])
                colour = verdict_colour(verdict)
            tk.Label(row, text=verdict, font=fnt(8, "bold", mono=True), bg=BG,
                     fg=colour, anchor="w").pack(side="left", padx=(12, 0))
            tk.Label(row, text=points, font=fnt(9, "bold", mono=True), bg=BG,
                     fg=colour, anchor="e").pack(side="right")

        chart_metrics = dataviz.score_metrics(app.results)
        if chart_metrics:
            self.chart = MetricChart(right, chart_metrics, height=70)
            self.chart.pack(fill="x", pady=(9, 0))

        self.panel = tk.Frame(right, bg=BG, bd=0, highlightthickness=1,
                              highlightbackground=MUTED)
        self.panel.pack(fill="x", pady=(12, 0))
        panel_inner = tk.Frame(self.panel, bg=BG)
        panel_inner.pack(fill="both", expand=True, padx=12, pady=9)
        head = tk.Frame(panel_inner, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text=tracked("Local flight log"), font=fnt(7),
                 bg=BG, fg=TEXT, anchor="w").pack(side="left")
        tk.Label(head, text="LOCAL", font=fnt(8, mono=True), bg=BG,
                 fg=YELLOW, anchor="e").pack(side="right")
        self.note = tk.Label(
            panel_inner,
            text=("Telemetry is written to the local flight log on this machine. "
                  "No network request is made and no data is uploaded."),
            font=fnt(8), bg=BG, fg=MUTED, anchor="w", justify="left",
            wraplength=390)
        self.note.pack(fill="x", pady=(5, 7))
        self.bar = ProgressBar(panel_inner, app, 8)
        self.bar.pack(fill="x")
        self.counter = tk.Label(panel_inner, text="0 COORDINATE ROWS WRITTEN",
                                font=fnt(9, mono=True), bg=BG, fg=YELLOW,
                                anchor="w")
        self.counter.pack(fill="x", pady=(6, 1))
        self.status = tk.Label(panel_inner, text="OPENING LOCAL WRITER",
                               font=fnt(7, mono=True), bg=BG, fg=MUTED,
                               anchor="w")
        self.status.pack(fill="x")

        actions = tk.Frame(right, bg=BG)
        actions.pack(fill="x", pady=(12, 0))
        FlatButton(actions, app, "PLAY AGAIN", self.g(app.start_over), "primary",
                   size=10, padx=18, pady=8).pack(side="left", padx=(0, 8))
        FlatButton(actions, app, "QUIT", self.g(app.close), "outline",
                   size=10, padx=18, pady=8).pack(side="left")

        self.panel.bind("<Configure>", self.g(self.on_panel_resize))
        self.card.bind("<Configure>", self.g(self.on_card_resize))
        self.app.schedule(320, self.save_step)

    def draw_badge(self, _event=None):
        w = self.badge.winfo_width()
        h = self.badge.winfo_height()
        if w < 20 or h < 20:
            return
        self.badge.delete("all")
        visuals.draw_rank_badge(self.badge, w / 2.0, h / 2.0 - 4,
                               min(w, h) * 0.37, rank_for(self.app.score),
                               fnt(8, "bold", mono=True))
        self.badge.create_text(w / 2.0, h - 12, text="RAA // RANK CERTIFICATE",
                               fill=MUTED, font=fnt(7, mono=True))

    def on_card_resize(self, event):
        size = max(12, min(18, int(event.width / 58)))
        try:
            self.headline_font.configure(size=size)
        except Exception:
            pass

    def on_panel_resize(self, event):
        self.note.configure(wraplength=max(220, event.width - 40))

    @staticmethod
    def status_for(step):
        if step < 6:
            return "OPENING LOCAL WRITER"
        if step < 13:
            return "CREATING LOCAL FLIGHT LOG"
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
                text="WRITE COMPLETE · SAVED LOCALLY · NOTHING UPLOADED",
                fg=YELLOW)
            return
        self.app.schedule(85, self.save_step)


class ChipButton(tk.Frame):
    """Square selector tab used by the hangar."""

    def __init__(self, parent, text, command, selected=False, compact=False):
        tk.Frame.__init__(self, parent, bg=BG, highlightthickness=1,
                          highlightbackground=MUTED)
        self.command = command
        self.selected = selected
        self.hover = False
        self.compact = bool(compact)
        self.label = tk.Label(self, text=text,
                              font=fnt(7 if compact else 8, "bold", mono=True),
                              bg=BG, fg=TEXT, padx=5 if compact else 8,
                              pady=5 if compact else 6)
        self.label.pack(fill="both", expand=True)
        for widget in (self, self.label):
            widget.bind("<Button-1>", self.on_click)
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
            try:
                widget.configure(cursor="hand2")
            except tk.TclError:
                pass
        self.apply()

    def apply(self):
        if self.selected:
            background, foreground, border = YELLOW, BG, YELLOW
        elif self.hover:
            background, foreground, border = BG, YELLOW, YELLOW
        else:
            background, foreground, border = BG, TEXT, MUTED
        self.configure(bg=background, highlightbackground=border,
                       highlightcolor=border)
        self.label.configure(bg=background, fg=foreground)

    def set_selected(self, selected):
        self.selected = bool(selected)
        self.hover = False
        self.apply()

    def on_click(self, _event=None):
        self.command()

    def on_enter(self, _event=None):
        if not self.hover:
            self.hover = True
            self.apply()

    def on_leave(self, _event=None):
        if self.hover:
            self.hover = False
            self.apply()


class QuizOption(tk.Frame):
    """One answer row in the hangar exam."""

    def __init__(self, parent, number, command):
        tk.Frame.__init__(self, parent, bg=BG, highlightthickness=1,
                          highlightbackground=MUTED)
        self.command = command
        self.state = "idle"
        self.hover = False
        self.inner = tk.Frame(self, bg=BG)
        self.inner.pack(fill="both", expand=True, padx=8, pady=6)
        self.number_box = tk.Frame(self.inner, bg=BG, width=24, height=24,
                                   highlightthickness=1,
                                   highlightbackground=MUTED)
        self.number_box.pack(side="left")
        self.number_box.pack_propagate(False)
        self.number = tk.Label(self.number_box, text=str(number),
                               font=fnt(9, "bold", mono=True), bg=BG,
                               fg=YELLOW)
        self.number.place(relx=0.5, rely=0.5, anchor="center")
        self.label = tk.Label(self.inner, text="", font=fnt(8), bg=BG,
                              fg=TEXT, anchor="w", justify="left",
                              wraplength=280)
        self.label.pack(side="left", fill="x", expand=True, padx=(9, 0))
        self.widgets = (self, self.inner, self.number_box, self.number,
                        self.label)
        for widget in self.widgets:
            widget.bind("<Button-1>", self.on_click)
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
        self.apply()

    def set_text(self, text):
        self.label.configure(text=text)

    def set_wraplength(self, width):
        self.label.configure(wraplength=max(120, int(width)))

    def set_state(self, state):
        self.state = state
        self.hover = False
        self.apply()

    def apply(self):
        if self.state == "correct":
            background, foreground, border = YELLOW, BG, YELLOW
        elif self.state == "wrong":
            background, foreground, border = BG, MUTED, MUTED
        elif self.state == "dim":
            background, foreground, border = BG, MUTED, visuals.GRID
        elif self.hover:
            background, foreground, border = BG, YELLOW, YELLOW
        else:
            background, foreground, border = BG, TEXT, MUTED
        self.configure(bg=background, highlightbackground=border,
                       highlightcolor=border)
        self.inner.configure(bg=background)
        self.number_box.configure(bg=background, highlightbackground=border,
                                  highlightcolor=border)
        self.number.configure(bg=background, fg=foreground)
        self.label.configure(bg=background, fg=foreground)
        try:
            cursor = "hand2" if self.state == "idle" else "arrow"
            for widget in self.widgets:
                widget.configure(cursor=cursor)
        except tk.TclError:
            pass

    def _contains(self, widget):
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def on_enter(self, _event=None):
        if self.state == "idle" and not self.hover:
            self.hover = True
            self.apply()

    def on_leave(self, event=None):
        inside = False
        if event is not None:
            try:
                inside = self._contains(self.winfo_containing(event.x_root,
                                                               event.y_root))
            except Exception:
                inside = False
        if not inside and self.hover:
            self.hover = False
            self.apply()

    def on_click(self, _event=None):
        if self.state == "idle":
            self.command()


class HangarScreen(Screen):
    """Interactive 3D hangar with orbit controls, an instructor and an exam."""

    TAB_NAMES = {"xwing": "X-WING", "tie": "TIE", "destroyer": "ISD",
                 "falcon9": "FALCON", "starship": "STARSHIP"}
    TAB_KEYS = {0: "1", 1: "2", 2: "3", 3: "4", 4: "5"}

    def __init__(self, parent, app):
        Screen.__init__(self, parent, app)
        self.ship_index = 0
        self.yaw = fleet3d.SHIPS[0]["yaw"]
        self.pitch = fleet3d.SHIPS[0]["pitch"]
        self.zoom = fleet3d.SHIPS[0]["zoom"]
        self.auto = True
        self.dragging = False
        self.last_pointer = (0, 0)
        self.resume_at = 0.0
        self.elapsed = 0.0
        self.last_polygons = 0
        self.env_ready = False
        self.last_paint = 0.0
        self.paint_token = 0
        self.quiz_index = 0
        self.quiz_score = 0
        self.answered = None
        self.finished = False
        self.ref_model = None
        self.ref_name = ""

        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=28, pady=(14, 0))
        tk.Label(bar, text="HANGAR / SHIPYARD", font=fnt(9, "bold", mono=True),
                 bg=BG, fg=YELLOW).pack(side="left")
        tk.Label(bar, text="REAL-TIME 3D BAY · NO ASSETS",
                 font=fnt(8, mono=True), bg=BG, fg=MUTED).pack(side="left",
                                                              padx=(14, 0))
        FlatButton(bar, app, "BACK TO TITLE", self.g(app.back_to_title),
                   "outline", size=8, padx=12, pady=6).pack(side="right")
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=28,
                                                pady=(10, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=12)
        body.columnconfigure(0, weight=6, minsize=390)
        body.columnconfigure(1, weight=5, minsize=330)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 22))
        self.viewer = tk.Canvas(left, bg=BG, bd=0, highlightthickness=1,
                                highlightbackground=MUTED, takefocus=0)
        self.viewer.pack(fill="both", expand=True)
        self.viewer.bind("<Configure>", self.g(self.on_viewer_resize))
        self.viewer.bind("<ButtonPress-1>", self.g(self.on_drag_start))
        self.viewer.bind("<B1-Motion>", self.g(self.on_drag))
        self.viewer.bind("<ButtonRelease-1>", self.g(self.on_drag_end))
        self.viewer.bind("<MouseWheel>", self.g(self.on_wheel))
        self.viewer.bind("<Button-4>", self.g(self.on_wheel))
        self.viewer.bind("<Button-5>", self.g(self.on_wheel))

        tabs = tk.Frame(left, bg=BG)
        tabs.pack(fill="x", pady=(8, 0))
        self.tabs = []
        for index, ship in enumerate(fleet3d.SHIPS):
            tab = ChipButton(tabs, self.TAB_NAMES[ship["id"]],
                             self.g(self.pick_ship(index)),
                             compact=True)
            tab.pack(side="left", padx=(0, 6))
            self.tabs.append(tab)
        self.tabs[0].set_selected(True)

        tip_frame = tk.Frame(left, bg=BG, highlightthickness=1,
                             highlightbackground=MUTED)
        tip_frame.pack(fill="x", pady=(8, 0))
        self.tip_canvas = tk.Canvas(tip_frame, width=56, height=56, bg=BG,
                                    bd=0, highlightthickness=0, takefocus=0)
        self.tip_canvas.pack(side="left", padx=(5, 8), pady=4)
        tip_text = tk.Frame(tip_frame, bg=BG)
        tip_text.pack(side="left", fill="x", expand=True, pady=3)
        self.tip_title = tk.Label(
            tip_text, text="MAJOR VEGA · FLIGHT INSTRUCTOR",
            font=fnt(7, "bold", mono=True), bg=BG, fg=YELLOW, anchor="w")
        self.tip_title.pack(fill="x")
        self.tip_label = tk.Label(
            tip_text, text="", font=fnt(8), bg=BG, fg=TEXT, anchor="w",
            justify="left", wraplength=280)
        self.tip_label.pack(fill="x", pady=(2, 0))
        self.tip_canvas.bind("<Configure>", self.g(self.draw_tip_portrait))

        controls = tk.Frame(left, bg=BG)
        controls.pack(fill="x", pady=(6, 0))
        tk.Label(controls, text="DRAG ORBIT · WHEEL ZOOM",
                 font=fnt(7, mono=True), bg=BG, fg=MUTED).pack(side="left")
        self.auto_button = FlatButton(controls, app, "AUTO ON",
                                      self.g(self.toggle_auto), "outline",
                                      size=7, padx=7, pady=4)
        self.auto_button.pack(side="right", padx=(5, 0))
        FlatButton(controls, app, "RESET", self.g(self.reset_view),
                   "outline", size=7, padx=7, pady=4).pack(side="right")

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        dossier = tk.Frame(right, bg=BG, highlightthickness=1,
                           highlightbackground=MUTED)
        dossier.pack(fill="x")
        inner = tk.Frame(dossier, bg=BG)
        inner.pack(fill="x", padx=14, pady=10)
        self.ship_title = tk.Label(inner, text="", font=fnt(14, "bold"),
                                   bg=BG, fg=YELLOW, anchor="w")
        self.ship_title.pack(fill="x")
        self.ship_class = tk.Label(inner, text="", font=fnt(7, mono=True),
                                   bg=BG, fg=MUTED, anchor="w")
        self.ship_class.pack(fill="x", pady=(2, 5))
        self.ship_values = {}
        for caption, key in (("ROLE", "role"), ("CREW", "crew"),
                             ("LENGTH", "length"), ("ARMAMENT", "arms")):
            row = tk.Frame(inner, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=caption, font=fnt(7, mono=True), bg=BG,
                     fg=MUTED, width=9, anchor="w").pack(side="left")
            value = tk.Label(row, text="", font=fnt(8, mono=True), bg=BG,
                             fg=TEXT, anchor="w", justify="left",
                             wraplength=220)
            value.pack(side="left", fill="x", expand=True)
            self.ship_values[key] = value
        self.ship_note = tk.Label(inner, text="", font=fnt(8), bg=BG,
                                  fg=MUTED, anchor="w", justify="left",
                                  wraplength=290)
        self.ship_note.pack(fill="x", pady=(5, 0))

        quiz = tk.Frame(right, bg=BG, highlightthickness=1,
                        highlightbackground=MUTED)
        quiz.pack(fill="both", expand=True, pady=(10, 0))
        self.quiz_panel = quiz
        room = tk.Frame(quiz, bg=BG)
        room.pack(fill="both", expand=True, padx=14, pady=10)

        head = tk.Frame(room, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="CADET EXAM", font=fnt(8, "bold", mono=True),
                 bg=BG, fg=TEXT).pack(side="left")
        self.quiz_progress = tk.Label(head, text="", font=fnt(7, mono=True),
                                      bg=BG, fg=MUTED, anchor="e")
        self.quiz_progress.pack(side="right")

        question_row = tk.Frame(room, bg=BG)
        question_row.pack(fill="x", pady=(7, 5))
        self.ref_canvas = tk.Canvas(question_row, width=94, height=72, bg=BG,
                                    bd=0, highlightthickness=1,
                                    highlightbackground=visuals.GRID,
                                    takefocus=0)
        self.ref_canvas.pack(side="left", padx=(0, 9))
        self.ref_canvas.bind("<Configure>", self.g(self.draw_reference))
        self.question = tk.Label(question_row, text="", font=fnt(9), bg=BG,
                                 fg=TEXT, anchor="w", justify="left",
                                 wraplength=185)
        self.question.pack(side="left", fill="x", expand=True)

        self.options = []
        for number in range(3):
            option = QuizOption(
                room, number + 1,
                self.g(lambda index=number: self.answer(index)))
            option.pack(fill="x", pady=(0, 4))
            self.options.append(option)
        self.feedback = tk.Label(room, text="", font=fnt(8), bg=BG, fg=MUTED,
                                 anchor="w", justify="left", wraplength=300)
        self.feedback.pack(fill="x", pady=(2, 5))
        self.next_button = FlatButton(room, app, "NEXT QUESTION",
                                      self.g(self.next_question), "primary",
                                      size=9, padx=12, pady=6)
        self.next_button.pack(anchor="e")
        self.next_button.set_enabled(False)
        quiz.bind("<Configure>", self.g(self.on_quiz_resize))

        self.set_ship(0, redraw=False)
        self.load_question()
        self.app.schedule(140, self.draw_reference)
        self.app.audio.loop("ambient", 0.10)
        self.app.schedule(90, self.first_paint)
        self.app.schedule(70, self.tick)

    # -- 3D viewer ------------------------------------------------------
    def first_paint(self):
        self.paint_viewer()
        self.draw_tip_portrait()

    def pick_ship(self, index):
        return lambda: self.set_ship(index)

    def set_ship(self, index, redraw=True):
        if index < 0 or index >= len(fleet3d.SHIPS):
            return
        self.ship_index = index
        ship = fleet3d.SHIPS[index]
        self.zoom = ship["zoom"]
        self.yaw = ship["yaw"]
        self.pitch = ship["pitch"]
        for position, tab in enumerate(self.tabs):
            tab.set_selected(position == index)
        self.ship_title.configure(text=ship["name"])
        self.ship_class.configure(text=ship["class"].upper() + " // REFERENCE")
        for key, label in self.ship_values.items():
            label.configure(text=str(ship[key]).upper())
        self.ship_note.configure(text=ship["note"])
        self.env_ready = False
        self.set_tip(ship["note"] + " Drag to orbit the display.")
        if redraw:
            self.paint_viewer()
            self.app.audio.play("servo", 0.25)

    def on_viewer_resize(self, _event=None):
        self.env_ready = False
        self.paint_token += 1
        token = self.paint_token

        def paint():
            if token == self.paint_token and self.winfo_exists():
                self.paint_viewer()
        self.app.schedule(70, paint)

    def paint_viewer(self):
        canvas = self.viewer
        if not canvas.winfo_exists():
            return
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 40 or height < 40:
            return
        ship = fleet3d.SHIPS[self.ship_index]
        visuals3d.draw_hangar_environment(canvas, ship, width, height,
                                          tag="env")
        self.draw_ship()
        self.draw_hud()
        self.env_ready = True
        self.last_paint = time.monotonic()

    def draw_ship(self):
        canvas = self.viewer
        if not canvas.winfo_exists():
            return
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 40 or height < 40:
            return
        ship = fleet3d.SHIPS[self.ship_index]
        self.last_polygons = visuals3d.draw_hangar_ship(
            canvas, ship, self.yaw, self.pitch, self.zoom, width, height,
            tag="ship", elapsed=self.elapsed, auto=self.auto)

    def draw_hud(self):
        canvas = self.viewer
        canvas.delete("hud")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 40 or height < 40:
            return
        ship = fleet3d.SHIPS[self.ship_index]
        canvas.create_text(14, 12, anchor="nw", tags="hud",
                           text="BAY 07 · ORBITAL HANGAR",
                           fill=YELLOW, font=fnt(8, "bold", mono=True))
        canvas.create_text(width - 14, 12, anchor="ne", tags="hud",
                           text="YAW {0:03.0f}° · PITCH {1:+03.0f}°".format(
                               math.degrees(self.yaw) % 360,
                               math.degrees(self.pitch)),
                           fill=MUTED, font=fnt(7, mono=True))
        canvas.create_text(14, height - 12, anchor="sw", tags="hud",
                           text="MODEL 0{0} · {1}".format(
                               self.ship_index + 1, ship["name"]),
                           fill=TEXT, font=fnt(7, mono=True))
        canvas.create_text(width - 14, height - 12, anchor="se", tags="hud",
                           text="{0} POLYGONS · AUTO {1}".format(
                               self.last_polygons,
                               "ON" if self.auto else "OFF"),
                           fill=MUTED, font=fnt(7, mono=True))
        canvas.create_rectangle(5, 5, width - 5, height - 5,
                                outline="#20272E", tags="hud")

    def tick(self):
        if not self.winfo_exists():
            return
        self.elapsed += 0.06
        if not self.env_ready:
            self.paint_viewer()
        if self.auto and not self.dragging and time.monotonic() >= self.resume_at:
            self.yaw += 0.011
        self.draw_ship()
        self.draw_hud()
        self.app.schedule(55, self.tick)

    def on_drag_start(self, event):
        self.dragging = True
        self.last_pointer = (event.x, event.y)

    def on_drag(self, event):
        if not self.dragging:
            return
        dx = event.x - self.last_pointer[0]
        dy = event.y - self.last_pointer[1]
        self.last_pointer = (event.x, event.y)
        self.yaw += dx * 0.011
        self.pitch = max(-1.05, min(1.05, self.pitch + dy * 0.008))
        self.draw_ship()
        self.draw_hud()

    def on_drag_end(self, _event=None):
        if self.dragging:
            self.app.audio.play("servo", 0.18)
        self.dragging = False
        self.resume_at = time.monotonic() + 2.2

    def on_wheel(self, event):
        direction = 0
        if getattr(event, "num", None) == 4:
            direction = 1
        elif getattr(event, "num", None) == 5:
            direction = -1
        else:
            delta = getattr(event, "delta", 0)
            direction = 1 if delta > 0 else -1 if delta < 0 else 0
        if direction:
            self.zoom_by(1.08 if direction > 0 else 1 / 1.08)
        return "break"

    def zoom_by(self, factor):
        self.zoom = max(0.55, min(2.4, self.zoom * factor))
        self.draw_ship()
        self.draw_hud()

    def toggle_auto(self):
        self.auto = not self.auto
        self.auto_button.set_text("AUTO ON" if self.auto else "AUTO OFF")
        self.set_tip("Auto-orbit is {0}. Drag the ship to take over.".format(
            "on" if self.auto else "paused"))
        self.app.audio.play("click", 0.2)

    def reset_view(self):
        ship = fleet3d.SHIPS[self.ship_index]
        self.yaw = ship["yaw"]
        self.pitch = ship["pitch"]
        self.zoom = ship["zoom"]
        self.auto = True
        self.auto_button.set_text("AUTO ON")
        self.resume_at = 0.0
        self.draw_ship()
        self.draw_hud()
        self.set_tip("Display reset. Drag to inspect the hull.")
        self.app.audio.play("confirm", 0.22)

    def on_raw_key(self, name, pressed):
        if not pressed:
            return
        lowered = name.lower()
        if lowered in ("a", "left"):
            self.toggle_auto()
        elif lowered in ("r", "right"):
            self.reset_view()
        elif lowered in ("plus", "equal", "kp_add"):
            self.zoom_by(1.12)
        elif lowered in ("minus", "kp_subtract"):
            self.zoom_by(1 / 1.12)

    # -- instructor -----------------------------------------------------
    def set_tip(self, text):
        self.tip_label.configure(text=text)

    def draw_tip_portrait(self, _event=None):
        canvas = self.tip_canvas
        if not canvas.winfo_exists():
            return
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 24 or height < 24:
            self.app.schedule(80, self.draw_tip_portrait)
            return
        visuals3d.draw_crew_portrait(canvas, "astronaut", width, height,
                                     tag="tip")
        canvas.create_text(width / 2, height - 5, anchor="s", text="VEGA",
                           fill=YELLOW, font=fnt(6, "bold", mono=True),
                           tags="tip")

    # -- exam -----------------------------------------------------------
    def on_quiz_resize(self, event):
        width = max(160, event.width - 46)
        self.question.configure(wraplength=max(110, width - 110))
        self.feedback.configure(wraplength=width)
        for option in self.options:
            option.set_wraplength(width - 64)
        self.draw_reference()

    def load_question(self):
        self.answered = None
        question = shipyard.QUESTIONS[self.quiz_index]
        reference = shipyard.EXAM_MODELS[
            shipyard.QUESTION_MODEL_IDS[self.quiz_index]]
        self.ref_model = reference["mesh"]
        self.ref_name = reference["name"]
        self.quiz_progress.configure(
            text="QUESTION {0} / {1} · {2} CORRECT".format(
                self.quiz_index + 1, len(shipyard.QUESTIONS), self.quiz_score))
        self.question.configure(text=question["question"], fg=TEXT)
        for option, text in zip(self.options, question["answers"]):
            option.set_state("idle")
            option.set_text(text)
        self.feedback.configure(text="", fg=MUTED)
        self.next_button.set_text("NEXT QUESTION")
        self.next_button.set_enabled(False)
        self.draw_reference()
        self.set_tip("Question {0}: read the reference on the scope, then "
                     "pick one.".format(self.quiz_index + 1))

    def draw_reference(self, _event=None):
        canvas = self.ref_canvas
        if not canvas.winfo_exists():
            return
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        canvas.delete("all")
        if width < 30 or height < 30 or self.ref_model is None:
            return
        canvas.create_rectangle(0, 0, width, height, fill=BG, outline="")
        canvas.create_line(width / 2, 5, width / 2, height - 16,
                           fill=visuals.GRID)
        canvas.create_line(5, height / 2, width - 5, height / 2,
                           fill=visuals.GRID)
        widest, tallest = 1.0, 1.0
        for yaw in (0.0, 0.5, 1.0, 1.5, 2.0):
            frame = shipyard.build_frame(self.ref_model, width, height - 22,
                                         yaw, 0.2, 1.0)
            xs = [x for polygon in frame for x, _y in polygon["points"]]
            ys = [y for polygon in frame for _x, y in polygon["points"]]
            if xs and ys:
                widest = max(widest, max(xs) - min(xs))
                tallest = max(tallest, max(ys) - min(ys))
        zoom = min(2.8, 0.82 * min((width - 10) / widest,
                                   (height - 32) / tallest))
        frame = shipyard.build_frame(self.ref_model, width, height - 20,
                                     0.55, 0.2, zoom)
        for polygon in frame:
            points = []
            for x, y in polygon["points"]:
                points.extend((x, y))
            canvas.create_polygon(points, fill=polygon["fill"],
                                  outline=polygon["outline"])
        canvas.create_text(4, 3, anchor="nw", fill=MUTED,
                           text="Q {0:02d} REF".format(self.quiz_index + 1),
                           font=fnt(6, mono=True))
        canvas.create_text(width - 4, height - 3, anchor="se", fill=YELLOW,
                           text=self.ref_name, font=fnt(6, "bold", mono=True))

    def answer(self, index):
        if self.finished or self.answered is not None:
            return
        self.answered = index
        question = shipyard.QUESTIONS[self.quiz_index]
        correct = index == question["correct"]
        if correct:
            self.quiz_score += 1
            self.app.audio.play("confirm", 0.32)
        else:
            self.app.audio.play("deny", 0.28)
        for position, option in enumerate(self.options):
            if position == question["correct"]:
                option.set_state("correct")
            elif position == index:
                option.set_state("wrong")
            else:
                option.set_state("dim")
        prefix = "CORRECT · " if correct else "NOT QUITE · "
        self.feedback.configure(text=prefix + question["explain"],
                                fg=YELLOW if correct else TEXT)
        self.quiz_progress.configure(
            text="QUESTION {0} / {1} · {2} CORRECT".format(
                self.quiz_index + 1, len(shipyard.QUESTIONS), self.quiz_score))
        self.next_button.set_enabled(True)
        self.set_tip(("Good answer. " if correct else "Not quite. ")
                     + question["explain"])

    def next_question(self):
        self.app.audio.play("click", 0.22)
        if self.finished:
            self.reset_quiz()
            return
        if self.answered is None:
            return
        self.quiz_index += 1
        if self.quiz_index >= len(shipyard.QUESTIONS):
            self.finish_quiz()
            return
        self.load_question()

    def finish_quiz(self):
        self.finished = True
        total = len(shipyard.QUESTIONS)
        self.question.configure(
            text="EXAM COMPLETE · {0} / {1} CORRECT".format(self.quiz_score,
                                                             total),
            fg=YELLOW)
        for option in self.options:
            option.pack_forget()
        if self.quiz_score == total:
            note = "Perfect paper. The hangar chief signs it without reading."
        elif self.quiz_score >= round(total * 0.8):
            note = "A solid cadet paper. The launch crew will take you seriously."
        else:
            note = "Read the dossiers, then run the exam again."
        self.feedback.configure(text=note, fg=TEXT)
        self.quiz_progress.configure(text="HANGAR CERTIFICATE · SESSION ONLY")
        self.next_button.set_text("RUN EXAM AGAIN")
        self.next_button.set_enabled(True)
        self.set_tip(note)
        self.app.audio.play("success" if self.quiz_score >= total * 0.8
                            else "deny", 0.30)

    def reset_quiz(self):
        self.finished = False
        self.quiz_index = 0
        self.quiz_score = 0
        for option in self.options:
            option.pack(fill="x", pady=(0, 4), before=self.feedback)
        self.load_question()

    def on_digit(self, digit):
        if self.finished:
            return
        index = int(digit) - 1
        if 0 <= index < len(self.options):
            self.answer(index)

    def on_key(self, name, pressed):
        if name == "pause" and pressed:
            self.app.back_to_title()


class App:
    KEY_MAP = {"Up": "up", "Down": "down", "Left": "left", "Right": "right",
               "space": "space", "w": "up", "a": "left", "s": "down",
               "d": "right", "p": "pause", "m": "slow",
               "Escape": "pause"}

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
        self.audio = audio_engine.Audio(enabled=self.pilot.sound_on)
        self.pending_index = 0
        self.pending_option = None
        self.recorded = False
        self.last_run_improved = False
        self.presentation = False
        self.fullscreen = False

        set_root_bg(root)
        root.protocol("WM_DELETE_WINDOW", self.guard(self.close))

        footer = tk.Frame(root, bg=BG)
        footer.pack(side="bottom", fill="x")
        tk.Frame(footer, bg=MUTED, height=1).pack(fill="x")
        footer_row = tk.Frame(footer, bg=BG)
        footer_row.pack(fill="x", padx=18)
        tk.Label(footer_row, text=FOOTER_TEXT, font=fnt(8), bg=BG,
                 fg=MUTED).pack(side="left", pady=6)
        self.sound_label = tk.Label(
            footer_row,
            text="SOUND · ON" if self.audio.enabled else "SOUND · OFF",
            font=fnt(8, "bold", mono=True), bg=BG,
            fg=YELLOW if self.audio.enabled else MUTED)
        self.sound_label.pack(side="right", pady=6)
        self.sound_label.configure(cursor="hand2")
        self.sound_label.bind("<Button-1>", self.guard(self.toggle_sound))

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
            self.audio.stop_loop()
        except Exception:
            pass
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

    def show_hangar(self):
        self.show(lambda parent, app: HangarScreen(parent, app))

    def show_mission(self, index):
        self.mission_index = index
        self.show(lambda parent, app: MissionScreen(parent, app, index))

    def start_missions(self):
        self.presentation = False
        self.score = 0
        self.results = []
        self.mission_index = 0
        self.pending_option = None
        self.recorded = False
        self.last_run_improved = False
        self.show_mission(0)

    def begin_presentation(self, index):
        if index < 0 or index >= len(MISSIONS):
            return
        self.presentation = True
        self.score = 0
        self.results = []
        self.mission_index = index
        self.pending_index = index
        self.pending_option = None
        self.recorded = False
        self.last_run_improved = False
        self.show_mission(index)

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
        if self.presentation:
            self.back_to_title()
            return
        if not self.recorded:
            self.recorded = True
            self.last_run_improved = self.pilot.record(
                self.score, self.callsign, rank_for(self.score))
        self.show(lambda parent, app: FinalScreen(parent, app))

    def advance(self):
        if self.presentation:
            self.back_to_title()
            return
        next_index = self.mission_index + 1
        if next_index < len(MISSIONS):
            self.show_mission(next_index)
        else:
            self.finish_run()

    def start_over(self):
        self.back_to_title()

    def back_to_title(self):
        self.presentation = False
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
        raw = getattr(screen, "on_raw_key", None)
        if callable(raw):
            raw(event.keysym, True)
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
        raw = getattr(screen, "on_raw_key", None)
        if callable(raw):
            raw(event.keysym, False)
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

    def toggle_sound(self, _event=None):
        enabled = not self.audio.enabled
        self.audio.set_enabled(enabled)
        self.pilot.set_sound(enabled)
        self.sound_label.configure(
            text="SOUND · ON" if enabled else "SOUND · OFF",
            fg=YELLOW if enabled else MUTED)
        if enabled:
            self.audio.play("confirm", 0.30)

    def close(self):
        try:
            self.audio.stop_all()
        except Exception:
            pass
        try:
            self.cancel_all()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


def create_root():
    if ctk is not None:
        ctk.set_appearance_mode("dark")
        root = ctk.CTk(fg_color=BG)
    else:
        root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.minsize(900, 600)
    set_root_bg(root)
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
