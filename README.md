# Rebel-SpaceX Flight Simulator

**The Interstellar Driver's Ed** is a playable desktop flight simulator built for MLH Hack Week. The fiction is Star Wars; the engineering trade-offs are borrowed from SpaceX. Choose a mission profile, then fly it: trim a methalox load, land a booster on a Kamino drone ship, or steer an X-wing through a debris field.

The app is a single Tkinter file, uses only the Python standard library, and keeps one small pilot record on the local machine. Auth0 and Tiger Data are clearly labelled simulations; nothing is sent anywhere.

## MLH Hack Week

This project was built during MLH Hack Week as a complete desktop game rather than a click-through prototype.

- **Track:** desktop and games.
- **Playable first:** every mission has a real control loop, a countdown, a HUD, pause and a written debrief.
- **Sponsor integrations:** Auth0 and Tiger Data are represented by local simulations, so the demo runs offline on any judge's laptop without API keys or tenants.
- **Judge-friendly:** `python simulator.py` starts the game with the standard library alone; the release zips are built by GitHub Actions on Windows and macOS.
- **Three-minute demo:** title and callsign, simulated Auth0 sign-in, a propellant trim, a hoverslam, a debris run, then the flight log and the simulated hypertable save.

### Why the simulations

A judge should never need a live tenant or an API key to see the flow. The Auth0 sequence keeps the real choreography (progress, scopes, token) but generates the token locally. The Tiger Data save keeps the real vocabulary (hypertable, chunks, coordinate rows) but counts rows in memory. Both screens say SIMULATION on screen, and the source is short enough to read during judging.

## Features

- Native desktop window, resizable from 900 × 600, centred on launch and manually styled in black, Star Wars yellow and cool grey.
- Animated title starfield, callsign validation, default `CADET-X`, and a local pilot record on the title screen.
- Simulated Auth0 sequence with a timed progress bar, local log lines and a fake token generated with `hashlib`.
- Three missions, each with three scored decisions that set the difficulty of the flight that follows.
- **Mission 01 — load trim:** keep a moving mixture inside its tolerance band; injector strain can abort the pad.
- **Mission 02 — hoverslam:** one engine, limited fuel, wind and RCS translation over a pitching deck. Touch down below 9.5 m/s and inside the target.
- **Mission 03 — debris run:** steer a top-down X-wing through twenty seconds of wreckage; hull, close calls and difficulty depend on the shield decision.
- Performance bonus up to **+30 per mission**, added to the decision score; maximum run score is **390**.
- Pause menu, restart, abort to title, fullscreen (`F11`) and in-app error panel instead of a traceback.
- Local pilot record: best score, best rank, last callsign and completed flights, saved as one JSON file.
- Simulated Tiger Data Hypertable Cloud save: progress bar and a counter of millions of coordinate rows written.
- All `after()` callbacks are cancelled on screen changes and on close.

## Controls

| Action | Keys |
| --- | --- |
| Select a mission decision | `1`, `2`, `3` or click |
| Trim mixture / fire landing engine | `↑` / `↓`, `W` / `S`, `Space` |
| Steer the X-wing / RCS | `←` / `→`, `A` / `D` |
| Pause / resume | `P` or `Esc` |
| Fullscreen | `F11` |

## Scoring and ranks

Each mission adds the option score plus a flight performance bonus capped at 30. The best possible run is 390 points.

| Score | Rank |
| --- | --- |
| 350–390 | Jedi Ace |
| 270–349 | Squadron Leader |
| 190–269 | Senior Pilot |
| 100–189 | Flight Cadet |
| below 100 | Ground Crew |

## SpaceX in the simulator

| SpaceX engineering | In the game |
| --- | --- |
| Falcon 9 flies on RP-1 and liquid oxygen; Starship moves to subcooled methane and oxygen | Mission 01: load methane, oxygen and a fictional Tibanna additive |
| Raptor's full-flow staged combustion and tight propellant margins | Mission 01 mechanics: mixture band, injector strain, load rate |
| Drone-ship landings, grid fins and the hoverslam | Mission 02: flight model with gravity, thrust, fuel, wind and RCS |
| Reusability and thermal protection (PICA-X, Starship tiles) | Mission 03: leading-edge Beskar versus full plating vs no shields |

Tibanna comes from Bespin, Beskar from Mandalore, and Kamino is a water world, which is exactly where a drone ship makes sense. The game never presents Tibanna or Beskar as real technology.

## Screenshots

Captures belong in `docs/screenshots/`. Add files with the names below and replace this table with image links when publishing the repository.

| Screen | Expected file |
| --- | --- |
| Title and pilot record | `docs/screenshots/01-title.png` |
| Simulated Auth0 login | `docs/screenshots/02-auth.png` |
| Mission 01, load trim | `docs/screenshots/03-load-trim.png` |
| Mission 02, hoverslam | `docs/screenshots/04-hoverslam.png` |
| Mission 03, debris run | `docs/screenshots/05-debris-run.png` |
| Debrief | `docs/screenshots/06-debrief.png` |
| Final score and simulated save | `docs/screenshots/07-flight-log.png` |

## Requirements

- Python 3.8 or newer.
- Tkinter, which ships with the official Python installers for Windows and macOS. No pip packages are required to run the game.
- No network connection is used at runtime.

## Run from source

From the repository root:

```bash
python simulator.py
```

On some systems the launcher is `python3`:

```bash
python3 simulator.py
```

## Downloads

Prebuilt v1.1.0 bundles are attached to the latest GitHub Release.

- **Windows:** [InterstellarDriversEd-Windows.zip](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest/download/InterstellarDriversEd-Windows.zip) — unzip and run `InterstellarDriversEd.exe` inside the folder.
- **macOS:** [InterstellarDriversEd-macOS.zip](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest/download/InterstellarDriversEd-macOS.zip) — unzip and move `InterstellarDriversEd.app` to Applications.

The landing page in `index.html` links to these same assets.

## Test

Core tests need no display:

```bash
python -m unittest discover -s tests -v
```

They cover callsign validation, the 390-point score ceiling, rank thresholds, mission difficulty ranks, debrief text and the local pilot record (including corrupt JSON).

## Build the desktop apps

The workflow in `.github/workflows/build.yml` runs the core tests, then builds both platforms with PyInstaller. Windows receives a version-info resource; macOS receives a bundle identifier.

Windows (folder build, no console window, no UPX):

```bash
pyinstaller --noconfirm --clean --onedir --windowed --noupx --name InterstellarDriversEd --version-file packaging/version_info.txt simulator.py
```

macOS (app bundle, no console window, no UPX):

```bash
pyinstaller --noconfirm --clean --windowed --noupx --name InterstellarDriversEd --osx-bundle-identifier com.rebelaerospace.interstellardriversed simulator.py
```

Trigger the workflow manually from **Actions → Build desktop apps → Run workflow**, or push a tag such as `v1.1.0`. Tag builds also attach both zips to the GitHub Release.

## Security and privacy

- Both bundles are **unsigned**. Windows SmartScreen may show "Windows protected your PC": choose **More info**, then **Run anyway**. macOS Gatekeeper may refuse the first launch: right-click the `.app`, choose **Open**, then confirm **Open**.
- The only file the app writes is `~/.interstellar_drivers_ed/pilot.json` (best score, rank, callsign, flight count). Delete that folder to reset the record.
- Auth0 and Tiger Data are **simulated**. The login animation, the token and the hypertable write happen in memory; the app opens no network connections, starts no subprocesses and uploads nothing.
- The desktop app imports only `tkinter`, `random`, `hashlib`, `time`, `sys`, `math`, `json` and `pathlib`.

## Tech stack

- Python 3.8+ and Tkinter (Canvas, Frame, Label, Entry; no ttk themes).
- HTML, inline CSS and vanilla JavaScript for the landing page: scroll reveals, a scroll-snap mission slider, an animated telemetry card and a local Auth0 demo message. No external assets.
- GitHub Actions with PyInstaller for Windows and macOS builds.

## Repository layout

```text
simulator.py                     Desktop application (single file)
index.html                       Self-contained landing page
tests/test_core.py               Core unit tests, no display required
packaging/version_info.txt       Windows version resource for PyInstaller
README.md                        This document
LICENSE                          MIT license
.gitignore                       Python and build ignores
.github/workflows/build.yml      Tests plus Windows and macOS build workflow
```

## License

MIT. See [LICENSE](LICENSE).
