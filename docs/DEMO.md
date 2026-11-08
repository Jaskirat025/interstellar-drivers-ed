# Three-minute judge route

**The Interstellar Driver's Ed** is a local-only desktop game. No API keys, accounts, tenants or network are needed. Auth0 and Tiger Data are clearly labelled simulations.

## Launch

From the repository root:

```bash
python -m pip install -r requirements.txt
python simulator.py
```

Use `python3` if that is your launcher. The window opens at 1120 × 760 and can be resized down to 900 × 600.

## Live-demo shortcut

Press **PRESENTATION · JUMP TO MISSION** on the title screen and choose mission 01, 02 or 03. This skips the sign-in and earlier missions, marks the briefing and HUD as a presentation, and never writes the demo score to the local pilot record. The picker is shown in [screenshots/11-presentation.png](screenshots/11-presentation.png).

## The route

Times assume you keep the flights short. The full three-mission run can take longer while you learn the controls.

### 0:00 · Title and pilot log (20 s)

- Type a callsign, or keep the default `CADET-X`.
- Point out the local pilot record: best score, flights, best rank. The record is stored as local JSON, not in a cloud tenant.
- Press **START MISSION** to enter the simulated Auth0 flow.
- **HANGAR** opens the 3D hangar and the cadet exam if you want to show it first.

### 0:20 · Simulated Auth0 (15 s)

- The progress bar runs through authorization window, local claims and session token.
- Every row says what it is doing; the token is generated locally with `hashlib`.
- Press **ENTER THE COCKPIT** when the token is issued.

### 0:35 · Mission 01, load trim (40 s)

- Pick a flight plan with `1`, `2`, `3` or a click.
- Keep the mixture inside the moving band with `↑` / `↓` (or `W` / `S`).
- The HUD shows load, drift and strain; an injector-strain abort is a real outcome, not a scripted cutscene.
- The debrief shows real telemetry in a Canvas chart.

### 1:15 · Mission 02, hoverslam (40 s)

- Choose a landing plan, then use **Space** (or `↑`) for the landing engine and `←` / `→` for RCS.
- Touch down under 9.5 m/s and inside the target. Fuel, wind and difficulty all come from the decision.
- Point out the impact wording when a landing fails: the game distinguishes a touchdown from a vehicle loss.

### 1:55 · Mission 03, debris run + slow motion (45 s)

- Choose the shield plan, then steer the X-wing with `←` / `→` (or `A` / `D`).
- Press **M** to toggle the 0.35× slow motion: scanlines, vignette and the HUD badge appear while the simulation clock actually slows.
- Press **M** again to release. The hull and close-call counters are live.

### 2:40 · Debrief and final log (20 s)

- The debrief combines the decision score, flight bonus and a per-mission chart. In presentation mode the button returns to the title and the demo score is discarded.
- After mission 03, the final log shows the 390-point ceiling and simulates the Tiger Data hypertable save.
- The pilot record is updated locally.

### Optional · Hangar and 20-model exam

Open **HANGAR** from the title screen, drag to orbit the X-wing, TIE fighter or Star Destroyer, then answer the SpaceX cadet exam with `1`, `2`, `3` or a click. Each of the twenty questions swaps in a different rotating 3D reference model. The gallery is in [screenshots/09-exam-models.png](screenshots/09-exam-models.png).

## If you only have 60 seconds

1. Open **HANGAR**, drag a model and answer one exam question.
2. Return to the title, start a mission, make one decision and play for a few seconds.
3. Press **M** to show slow motion, then open the debrief.

That is enough to see the custom 3D renderer, the game loop and the telemetry debrief.

## What to look for

- **3D from first principles:** `shipyard.py` builds meshes from vertices and faces, rotates and shades them, projects them and depth-sorts the result for Tk Canvas. No OpenGL, image sprites or 3D library.
- **Twenty unique exam models:** the hangar exam is not a static quiz; every question has its own reference mesh and auto-fit framing.
- **Three different control loops:** propellant trim, a hoverslam and a top-down debris run. The decision at the start of each mission changes the flight that follows.
- **Sponsor flows without a demo tax:** Auth0 and Tiger Data keep their real vocabulary and choreography, but run locally. A judge never needs a tenant, key or network.
- **Finished edges:** pause, restart, abort, fullscreen, in-app error panel, local pilot JSON, real screenshots and tests.
- **Deterministic Canvas art:** starfields, charts and ship viewers are drawn in Python, so the visual language stays consistent without web assets.

## MLH judging map

| Criterion | Where to look |
| --- | --- |
| Technical difficulty | Software 3D renderer in `shipyard.py`; 20 exam meshes; Canvas telemetry charts in `dataviz.py` |
| Game feel | Three real-time missions, countdown, pause, slow motion, debriefs and scoring |
| Theme | SpaceX engineering through a Star Wars lens, with fictional materials clearly labelled |
| Sponsor track | Simulated Auth0 and Tiger Data flows that preserve the real vocabulary and stay offline |
| Polish | 900 × 600 layout, keyboard and mouse controls, error panel, local record, CI-built Windows/macOS bundles |
| Reliability | No runtime network, no secrets, no external image or chart dependencies; 36 tests |

## Verify locally

Full suite, including GUI tests:

```bash
python -m unittest discover -s tests -v
```

Headless data, vector-art and geometry tests:

```bash
python -m unittest tests.test_dataviz tests.test_visuals tests.test_shipyard -v
```

## Before submitting

- [ ] Run the full test suite and the headless suite.
- [ ] Play the title → auth → one mission → debrief path once at 1120 × 760 and once at 900 × 600.
- [ ] Check the README quickstart and the Windows/macOS download links.
- [ ] Create the `v1.1.0` tag when the release assets are ready; the GitHub Actions workflow builds both zips and publishes the release.
- [ ] Open the landing page from a local static server and confirm the eight photos and two films load.
