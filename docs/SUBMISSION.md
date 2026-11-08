# MLH Hack Week submission · The Interstellar Driver's Ed

## One line

A complete offline desktop flight simulator that turns SpaceX engineering into three playable Star Wars missions, with a software 3D engine, procedural audio and a five-ship hangar.

## Track

Desktop and games.

## What is playable

- **Mission 01 — propellant load:** keep a Falcon 9 methane/oxygen/Tibanna mixture inside a moving band; injector strain can abort the pad.
- **Mission 02 — hoverslam:** land a booster on a drone ship with one engine, limited fuel, wind, RCS and a narrow deck.
- **Mission 03 — debris run:** steer an X-wing through twenty seconds of wreckage; shield choice sets the hull limit.
- **Hangar:** orbit and zoom five hand-built 3D ships, read dossiers, and take a twenty-question SpaceX cadet exam.
- **Scoring:** decision points plus a flight bonus; the ceiling is **390**. Five ranks from Ground Crew to Jedi Ace.
- **Presentation mode:** jump to any mission from the title without touching the local record.
- **Accessibility:** keyboard-only play, pause/restart/abort, fullscreen, sound toggle, silent fallback.

## What is technically interesting

1. **A software 3D engine in pure Python.** `engine3d.py` implements meshes, orbit cameras, perspective projection, near-plane clipping, key/fill/rim shading, fog and depth sorting. It never imports Tk, so every model and scene is testable headlessly.
2. **Hand-built geometry, no assets.** `fleet3d.py` contains the X-wing, TIE, Star Destroyer, Falcon 9, Starship, booster, drone ship, launch pad, hangar, planets, asteroids, astronaut and astromech. The hangar alone is about 1,500 faces; the X-wing about 800.
3. **The hangar is a real interactive viewer.** The static bay is cached, the ship redraws on orbit/zoom, and the exam reference is a separate 3D view. Drag, wheel, `A` auto-orbit and `R` reset all work; the old overlay bug that swallowed drags is gone.
4. **Procedural audio.** `audio.py` synthesises WAV effects at runtime with pygame. No audio files ship; if the mixer cannot start, the game is silent.
5. **Characters with a job.** Major Vega, K-3PO and R2-D2 give contextual CAPCOM calls based on mixture error, altitude, drift, fuel and the nearest rock.
6. **A real desktop release.** GitHub Actions runs the tests, builds a Windows folder + `.exe` and a macOS `.app` with PyInstaller, and attaches both zips to the release.

## Local-only by design

There are no accounts, API keys or network calls. The pilot check and the flight log write a single local JSON record; every screen that uses it is marked `LOCAL`.

## Run

```bash
python -m pip install -r requirements.txt
python simulator.py
```

Or download the release:

- Windows: `InterstellarDriversEd-Windows.zip` → `InterstellarDriversEd.exe`
- macOS: `InterstellarDriversEd-macOS.zip` → `InterstellarDriversEd.app`

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers the score ceiling, ranks, mission data, corrupt local JSON, chart metrics, the original shipyard and exam, the new 3D engine, fleet meshes and all Canvas scene painters. No display or audio device is required.

## Limitations

- The bundles are not code-signed yet; first launch may require one OS confirmation.
- The archive landing page is separate from the game and is not embedded.
- The Star Wars framing is unofficial fan material; SpaceX engineering is presented as the real reference.
