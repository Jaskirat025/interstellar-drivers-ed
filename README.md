# Rebel-SpaceX Flight Simulator

**The Interstellar Driver's Ed** — a windowed desktop game built for MLH Hack Week. Three branching missions in a restrained Star Wars cockpit, with the engineering decisions borrowed from SpaceX: a methalox propellant load, an autonomous hoverslam onto a drone ship, and a heat-shield-versus-mass trade-off.

The app is a single Tkinter file and uses only the Python standard library. The sponsor integrations are simulated locally; nothing leaves the machine.

## MLH Hack Week

This project was built during MLH Hack Week as a complete, demo-ready desktop game rather than a prototype.

- **Track:** desktop and games.
- **Sponsor integrations:** Auth0 and Tiger Data are represented by clearly labelled simulations, so the demo runs offline on any judge's laptop without API keys or tenants.
- **Judge-friendly:** `python simulator.py` starts the game with the standard library alone; the release zips are built by GitHub Actions on Windows and macOS.
- **Three-minute demo:** title and callsign, simulated Auth0 sign-in, all three missions with one deliberate failure, then the flight log and the simulated hypertable save.

### Why the simulations

A judge should never need a live tenant or an API key to see the flow. The Auth0 sequence keeps the real choreography (progress, scopes, token) but generates the token locally. The Tiger Data save keeps the real vocabulary (hypertable, chunks, coordinate rows) but counts rows in memory. Both screens say SIMULATION on screen, and the source is short enough to read during judging.

## Features

- Native desktop window, resizable from 900 × 600, centred on launch and manually styled in black, Star Wars yellow and cool grey.
- Animated title starfield, callsign entry with validation and the default `CADET-X`.
- Simulated Auth0 sequence with a timed progress bar, local log lines and a fake token generated with `hashlib`.
- Three missions, each with three scored options, an explained outcome and keyboard shortcuts `1`, `2`, `3`.
- SpaceX-inspired engineering (methalox propellant, hoverslam landing, heat-shield mass trade-offs) wrapped in Star Wars fiction.
- Line-art scenes drawn on Canvas (Falcon 9, starfighter, Beskar shield) and redrawn on resize.
- Typewriter mission briefings, HUD with mission number and score, rank calculation and a flight log.
- Simulated Tiger Data Hypertable Cloud save: progress bar and a counter of millions of coordinate rows written.
- In-app error panel with **BACK TO TITLE** instead of a traceback; all `after()` callbacks are cancelled on screen changes and on close.

## SpaceX in the simulator

The fiction is Star Wars. The engineering decisions are borrowed from SpaceX.

| SpaceX engineering | In the game |
| --- | --- |
| Falcon 9 flies on RP-1 and liquid oxygen; Starship moves to subcooled methane and oxygen | Mission 01: load methane, oxygen and a fictional Tibanna additive |
| Raptor's full-flow staged combustion and tight propellant margins | Mission 01 outcomes: mixture, injector resonance, payload margin |
| Drone-ship landings, grid fins and the hoverslam | Mission 02: an autonomous booster landing on a Kamino drone ship |
| Reusability and thermal protection (PICA-X, Starship tiles) | Mission 03: Beskar only where the debris can hit |

The Star Wars side is deliberate: Tibanna comes from Bespin, Beskar from Mandalore, and Kamino is a water world, which is exactly where a drone ship makes sense. The game never presents Tibanna or Beskar as real technology.

## Screenshots

Captures belong in `docs/screenshots/`. Add files with the names below and replace this table with image links when publishing the repository.

| Screen | Expected file |
| --- | --- |
| Title and starfield | `docs/screenshots/01-title.png` |
| Simulated Auth0 login | `docs/screenshots/02-auth.png` |
| Mission 01, propellant load | `docs/screenshots/03-mission-propellant.png` |
| Mission outcome overlay | `docs/screenshots/04-outcome.png` |
| Final score and simulated save | `docs/screenshots/05-flight-log.png` |

## Requirements

- Python 3.8 or newer.
- Tkinter, which ships with the official Python installers for Windows and macOS. No pip packages are required to run the game.

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

Prebuilt bundles are attached to the latest GitHub Release.

- **Windows:** [InterstellarDriversEd-Windows.zip](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest/download/InterstellarDriversEd-Windows.zip) — unzip and run `InterstellarDriversEd.exe` inside the folder.
- **macOS:** [InterstellarDriversEd-macOS.zip](https://github.com/Jaskirat025/interstellar-drivers-ed/releases/latest/download/InterstellarDriversEd-macOS.zip) — unzip and move `InterstellarDriversEd.app` to Applications.

The landing page in `index.html` links to these same assets.

## Build the desktop apps

The workflow in `.github/workflows/build.yml` builds both platforms with PyInstaller on GitHub runners. To build locally, install PyInstaller and run the platform command.

Windows (folder build, no console window, no UPX):

```bash
pyinstaller --noconfirm --clean --onedir --windowed --noupx --name InterstellarDriversEd simulator.py
```

macOS (app bundle, no console window, no UPX):

```bash
pyinstaller --noconfirm --clean --windowed --noupx --name InterstellarDriversEd simulator.py
```

Trigger the workflow manually from **Actions → Build desktop apps → Run workflow**, or push a tag such as `v1.0.0`. Tag builds also attach both zips to the GitHub Release.

## Security notes

- Both bundles are **unsigned**. Windows SmartScreen may show "Windows protected your PC": choose **More info**, then **Run anyway**. macOS Gatekeeper may refuse the first launch: right-click the `.app`, choose **Open**, then confirm **Open**.
- The full source is in this repository. `simulator.py` is readable end to end, and the workflow builds it without hidden steps.
- Auth0 and Tiger Data are **simulated**. The login animation, the token and the hypertable write happen entirely in memory; the app opens no network connections, starts no subprocesses, reads no registry keys and leaves no files behind.
- The desktop app imports only `tkinter`, `random`, `hashlib`, `time`, `sys` and `math`.

## Tech stack

- Python 3.8+ and Tkinter (Canvas, Frame, Label, Entry; no ttk themes).
- HTML, inline CSS and minimal vanilla JavaScript for the landing page; inline SVG starfield; no external assets.
- GitHub Actions with PyInstaller for Windows and macOS builds.

## Repository layout

```text
simulator.py                     Desktop application (single file)
index.html                       Self-contained landing page
README.md                        This document
LICENSE                          MIT license
.gitignore                       Python and build ignores
.github/workflows/build.yml      Windows and macOS build workflow
```

## License

MIT. See [LICENSE](LICENSE).
