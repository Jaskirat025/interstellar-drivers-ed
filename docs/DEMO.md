# Three-minute judge route · v1.2.0

A complete pass through the desktop game. No account, API key or network is used.

## Before the clock starts

```bash
python -m pip install -r requirements.txt
python simulator.py
```

The window opens at 900 × 600 or larger. If there is no audio device, the game stays silent and everything else works.

## 0:00–0:25 · Title and pilot

1. Point out the real 3D scene behind the title: X-wing, Star Destroyer and planet, all software-rendered polygons.
2. Leave the callsign as `CADET-X` (or type a name) and press **START MISSION**.
3. The Auth0 sequence is a local simulation. Let the progress bar finish and press **ENTER THE COCKPIT**. The astronaut on the left is a 3D model.

## 0:25–1:15 · Mission 01 and the load trim

1. Read the Falcon 9 briefing and choose **2% TIBANNA ADDITIVE** for the optimal plan.
2. Wait for the countdown. R2-D2 gives the first CAPCOM call.
3. Use `↑` / `↓` to keep the yellow mixture line inside the moving band.
4. Hold the band until the tank reaches 100%. Major Vega warns when injector strain climbs.
5. On the debrief, note the stability and load charts; press continue.

## 1:15–2:05 · Mission 02 and the hoverslam

1. Choose **LET THE LANDING DROID FLY**.
2. The 3D booster hangs over an oblique drone-ship deck. Altitude, vertical speed and fuel are live.
3. Hold `Space` for the landing burn, use `←` / `→` for RCS, and watch R2-D2's calls: altitude, drift, fuel.
4. Touch down below 9.5 m/s and inside the target. The debrief explains the miss, speed and fuel bonus.

## 2:05–2:35 · Mission 03 and the debris run

1. Choose **LET THE DROID FLY** (or the leading-edge shield plan).
2. Steer with `←` / `→`; `M` shows the slow-motion HUD without changing the physics.
3. Dodge the rocks, watch the hull pips and close-call counter, and finish the twenty-second run.

## 2:35–2:55 · Hangar, five ships and the exam

1. Return to the title and open **HANGAR**.
2. Drag the X-wing to orbit, use the wheel to zoom, press `A` to pause auto-orbit and `R` to reset.
3. Switch between **X-WING**, **TIE**, **ISD**, **FALCON** and **STARSHIP**. Each tab changes the dossier and the 3D model.
4. Answer one cadet-exam question with `1`–`3`; the reference card is a separate shaded 3D view. The exam is session-only and does not touch the mission score.
5. Point out `SOUND · ON` in the footer: it persists the preference in the local pilot record.

## 2:55–3:00 · Close

1. Return to the title, then finish the run to show the final score, rank and simulated Tiger Data save.
2. Mention the release: the Windows zip contains `InterstellarDriversEd.exe`; the macOS zip contains `InterstellarDriversEd.app`.
3. Everything is offline. The only file written is `~/.interstellar_drivers_ed/pilot.json`.

## If the judge only has 60 seconds

Title → **PRESENTATION · JUMP TO MISSION** → Mission 01 → choose the optimal load → show the 3D load screen and CAPCOM → title → **HANGAR** → drag the X-wing → switch to **FALCON** → answer one exam question.
