# The Interstellar Driver's Ed

**A 3D desktop flight simulator about three SpaceX-inspired missions, a five-ship hangar and the people who keep a launch crew alive.**

**Created and developed by [Jaskirat025](https://github.com/Jaskirat025).**

[![Latest release](https://img.shields.io/github/v/release/Jaskirat025/interstellar-drivers-ed?color=FFE81F&label=release)](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest)
[![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-FFE81F)](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest)
[![Python](https://img.shields.io/badge/source-Python%203.10%2B-3776AB)](requirements.txt)

Fly a Falcon 9 stack through a live propellant load, land a booster on a drone ship, then cross a debris field in an X-wing. Between missions, orbit five hand-built ships in the hangar and take the flight instructor's twenty-question exam. Everything is rendered in real time by a small software 3D engine, with procedural audio and no game asset packs.

![The actual desktop app: title screen, pilot check, hangar, missions and flight log](docs/demo.gif)

*Recorded from the real Tk window, not a mockup or a headless frame.*

## Download

| Platform | Package | Size |
| --- | --- | --- |
| Windows 10/11 · x64 | [InterstellarDriversEd-Windows.zip](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest/download/InterstellarDriversEd-Windows.zip) | 31 MB |
| macOS · Apple Silicon | [InterstellarDriversEd-macOS.zip](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest/download/InterstellarDriversEd-macOS.zip) | 28 MB |

No Python installation is needed for these builds. Extract the **whole archive** and run `InterstellarDriversEd.exe` (Windows) or `InterstellarDriversEd.app` (macOS). The macOS build is for M-series Macs; Intel Macs need to run from source.

<details>
<summary><strong>First launch:</strong> unsigned build, one extra confirmation</summary>

The builds are not code-signed yet. On first launch Windows SmartScreen may ask for **More info → Run anyway**; on macOS, right-click the app and choose **Open**. This is a one-time confirmation, not an installer, account or network check.
</details>

## What it is

- **Three short missions**, each built around a real launch problem: propellant mixture, a hoverslam landing and a debris-field crossing.
- **A five-ship 3D hangar** with orbit, zoom, ship dossiers, an instructor and a cadet exam.
- **A complete arc**: title, pilot check, mission briefings, flight, debrief and a local flight log.
- **Rank and score**: decisions plus a flight bonus, capped at **390 points**; five ranks from Ground Crew to Jedi Ace.
- **Offline by design**: no account, no telemetry, no API keys and no runtime downloads.

## Why it stands out

1. **A software 3D engine in Python.** `engine3d.py` projects, clips, depth-sorts and shades polygon meshes on a Tk canvas. It never imports Tk itself, so every scene is testable headlessly.
2. **The models are original geometry.** `fleet3d.py` contains the X-wing, TIE, Star Destroyer, Falcon 9, Starship, booster, drone ship, launch pad, hangar, planets, astronaut and astromech. No sprite sheets or external model files.
3. **The hangar is a viewer, not a menu.** Drag to orbit, wheel to zoom, `A` to pause auto-orbit, `R` to reset; the ship and the reference model redraw independently.
4. **Procedural sound.** `audio.py` synthesises the clicks, engines, warnings, servo, success and failure cues at runtime with pygame. If audio cannot start, the game falls back to silence.
5. **Characters with a job.** Major Vega, K-3PO and R2-D2 give contextual CAPCOM calls based on mixture error, altitude, drift, fuel and the nearest rock.
6. **A real desktop release.** GitHub Actions runs the tests and packages Windows and macOS builds with PyInstaller.

## The three missions

| Mission | What you fly | What you manage |
| --- | --- | --- |
| **01 · Propellant load** | Falcon 9 stack on Pad 39-A | Methane/oxygen load, a 2% Tibanna additive, a moving mixture band and injector strain |
| **02 · Hoverslam** | Booster over a drone ship | One-engine landing burn, gravity, wind, RCS translation, fuel and a narrow deck |
| **03 · Debris run** | X-wing through a wreck field | Shield layout, steering, hull pips, close calls and a twenty-second run |

Every mission has a decision score plus a flight bonus of up to **+30**. The run ceiling is **390 points**. Rank thresholds: Ground Crew, Flight Cadet, Senior Pilot, Squadron Leader, Jedi Ace.

## The hangar

The hangar is a live 3D scene, not a static illustration:

- The bay is rendered once per camera/ship and cached; the ship is re-rendered as you orbit.
- Drag changes yaw and pitch with clamped limits; the wheel zooms between 0.55× and 2.4×.
- Auto-orbit pauses while dragging and resumes after two seconds.
- The ship dossier, instructor strip and exam reference sit outside the viewer, so they never intercept a drag.
- The exam reference is a separate shaded 3D view of the model in the question.
- The cadet exam is session-only and never changes the mission score.

## Run from source

Source needs Python 3.10+ with Tkinter and two Python packages. The release builds bundle them; a checkout does not.

```bash
python -m pip install -r requirements.txt
python simulator.py
```

If there is no audio device, the game stays silent and everything else works. The only file it writes is `~/.interstellar_drivers_ed/pilot.json`: best score, best rank, callsign, flight count and sound preference.

## Controls

| Action | Input |
| --- | --- |
| Select a mission decision | `1` / `2` / `3` or click |
| Trim mixture | `↑` / `↓`, `W` / `S` |
| Landing burn | `Space` or `↑` |
| Steer / RCS | `←` / `→`, `A` / `D` |
| Pause / resume | `P` or `Esc` |
| Slow motion | `M` |
| Hangar orbit / zoom | Drag / mouse wheel |
| Hangar auto-orbit / reset | `A` / `R` |
| Answer an exam question | `1` / `2` / `3` or click |
| Fullscreen | `F11` |
| Sound on/off | Click `SOUND · ON` in the footer |
| Jump straight to a mission | Title → `PRESENTATION · JUMP TO MISSION` |

## Under the hood

```text
simulator.py       Tk app, screens, missions, scoring and input
engine3d.py        software 3D engine: meshes, camera, clipping, shading, fog
fleet3d.py         hand-built ships, hangar, pad, drone ship, planets, crew
visuals3d.py       scene cameras, lighting pools, glows and Canvas painters
audio.py           procedural WAV synthesis and pygame playback with fallback
shipyard.py        original hangar meshes/projector; exam models and questions
visuals.py         shared palette and HUD primitives
dataviz.py         chart-ready telemetry
tests/             headless core, chart, vector and 3D tests
```

The 3D pipeline is intentionally small and readable: `Mesh` stores vertices and material-tagged faces; `Part` applies scale/rotation/translation; `Camera` projects perspective with near-plane clipping; `render` shades with key/fill/rim lights and fog, depth-sorts, and returns flat polygons for Tk Canvas. The engine never imports Tk, so all geometry and scenes are testable without a display.

## Tests and builds

```bash
python -m unittest discover -s tests -v
```

The suite covers callsign validation, the 390-point ceiling, ranks, mission scoring, corrupt local JSON, chart metrics, the shipyard models and exam, plus the 3D engine, fleet meshes and every scene painter. Tests need no display and no audio device.

The desktop workflow in `.github/workflows/build.yml` runs the tests, then PyInstaller on Windows and macOS. Both builds include `--collect-all customtkinter` and `--collect-all pygame`; macOS also stamps the bundle version.

## Privacy

- No accounts, analytics, telemetry or network requests.
- The pilot check and flight log are local, not a hosted service.
- The only file written is `~/.interstellar_drivers_ed/pilot.json`.
- Delete `~/.interstellar_drivers_ed` to reset the record.

## Credits

Created, designed and developed by [Jaskirat025](https://github.com/Jaskirat025). Built for MLH Hack Week. Spacecraft geometry and code are original; Star Wars names are used as a fan framing, not as official assets. NASA imagery in the companion archive is public domain and credited in `assets/photos/README.md`.

MIT license. See [LICENSE](LICENSE).
