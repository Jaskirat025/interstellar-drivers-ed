# MLH Hack Week submission copy

## One-line pitch

A playable SpaceX × Star Wars desktop flight simulator with a software-rendered 3D hangar, three real-time missions and a twenty-model cadet exam.

## Elevator pitch

The Interstellar Driver's Ed is a native desktop game, not a click-through prototype. You sign in through a local Auth0 simulation, choose a flight plan, then fly three different control loops: trim a propellant load, land a booster on a drone ship, and steer an X-wing through debris. Between missions, orbit hand-built 3D ships in the hangar and take a twenty-question SpaceX cadet exam where every question has its own rotating reference model. The whole experience is offline: no API keys, no tenants, no network calls. Tkinter and CustomTkinter provide the chrome; the ships, starfields, HUD and charts are drawn locally on Tk Canvas.

## Built for MLH Hack Week

- **Track:** desktop and games.
- **Playable first:** three missions with countdowns, HUDs, pause, restart and debriefs.
- **Sponsor stories:** Auth0 and Tiger Data are represented honestly as local simulations, with their real vocabulary and choreography intact.
- **Demo-safe:** a judge can install one dependency and run the game without an account or an internet connection.
- **Presentation-ready:** jump straight to any mission from the title; demo scores are visibly marked and never saved.
- **Finished:** 36 tests, a headless test path, real screenshots, an animated tour and Windows/macOS builds in GitHub Actions.

## How it was built

- `simulator.py`: Tkinter/CustomTkinter shell, title and auth flow, three flight models, debriefs, hangar and exam UI.
- `shipyard.py`: hand-built mesh primitives and twenty distinct exam models, plus a pure-Python projector with rotation, shading and depth sorting.
- `visuals.py`: Canvas vector art, starfields, ships, planets, HUDs and registration marks.
- `dataviz.py`: dependency-free telemetry and score metrics for the debrief charts.
- `index.html`: a separate self-contained archive page for the NASA photography and films; the game is never embedded in it.

## Challenges

- Making a readable 3D viewer without OpenGL, image sprites or a 3D library, then auto-framing twenty different meshes in a small exam panel.
- Keeping the slow-motion effect honest: the visual treatment is cinematic, but the simulation clock, physics and mission timer really run at 0.35×.
- Designing three control loops that feel different while sharing one HUD and one scoring model.
- Keeping the demo reliable offline while still representing Auth0 and Tiger Data in a way judges can recognize.

## Accomplishments

- A presentation mode that jumps straight to any mission without saving a demo score.
- A twenty-question exam where every question swaps in a different 3D model.
- A correct score ceiling of 390 points, with decision scores, flight bonuses and rank thresholds covered by tests.
- A polished 900 × 600-to-fullscreen layout with pause, restart, abort and an in-app error panel.
- A local pilot record written as JSON, with corrupt-file fallback.
- Real screenshots and an animated six-screen tour generated from the running app.

## What we learned

- A small software renderer is a constraint, but it makes the visual language deterministic and easy to test.
- Sponsor integrations do not need live credentials to communicate their shape; they need to be clearly labelled and honest.
- The best hackathon demo removes setup risk. Offline-first is a feature, not a limitation.

## What's next

- More exam sets and ship variants, still using the same renderer.
- A recorded voiceover walkthrough alongside the animated GIF.
- Optional cloud-backed pilot records behind the Tiger Data simulation, kept opt-in.

## Built with

Python · Tkinter · CustomTkinter · Tk Canvas · hashlib · JSON · Pillow (documentation GIF only) · GitHub Actions · PyInstaller · NASA public-domain media

## Links

- [README](../README.md)
- [Three-minute judge route](DEMO.md)
- [Animated demo](demo.gif)
- [Screenshots](screenshots/)
- [Twenty-model gallery](screenshots/09-exam-models.png)

Auth0 and Tiger Data are simulated locally. SpaceX, Star Wars and related marks belong to their respective owners; this is a fan-made hackathon project.
