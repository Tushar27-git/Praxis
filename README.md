# Praxis

Experimental native Python application for live Clash of Clans observation and Android-emulator control.

**Attacks are currently unreliable. This is an unfinished research prototype, not a working autonomous attack bot.** Development should focus on one small, reproducible fix at a time.

## Current capabilities

- Native Tkinter floating panel: emulator connection, continuous preview, recording and Stop.
- Pinned scrcpy/PyAV video client, latest-frame buffer, timing checks and Android coordinate mapping. A local 60-second benchmark delivered about 30 FPS; other machines may differ.
- Limited English UI recognition and experimental TH2 Barbarian/Archer control. Navigation, Town Hall verification, troop-count feedback and end-to-end attacks still need work.
- Local SQLite experience storage and outcome-prediction/training infrastructure. No useful trained outcome model or learned tactical improvement has been demonstrated.

The earlier three-star demonstration was agent-guided. It does not validate the standalone controller. Passing software tests likewise does not establish attack quality.

## Windows setup

Use Python 3.12 with Tkinter:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Install the game yourself in an Android emulator. BlueStacks 5 is the current development target. Enable Settings > Advanced > Android Debug Bridge and note its local port. Praxis does not need your account credentials.

Download these local tools; they are excluded from Git:

1. [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools): place adb.exe and its companion files in .tools/platform-tools/, or install ADB on PATH.
2. [Official scrcpy 3.3.3 server](https://github.com/Genymobile/scrcpy/releases/tag/v3.3.3): download the scrcpy-server-v3.3.3 asset to .tools/scrcpy/scrcpy-server-v3.3.3. The client requires that exact protocol version.

Launch start.cmd, or:

```powershell
.\.venv\Scripts\python.exe -m coc_advisor
```

## Using the app

1. Leave Clash running in the emulator and enable ADB.
2. Enter its address, typically 127.0.0.1:5555, then select Connect / refresh.
3. Select the emulator and Continuous video, then Start live capture.
4. Record frames saves local diagnostic images. Float / Compact adjusts the panel.
5. Stop cancels future capture/control work. An already submitted input cannot be undone.

The experimental Run one basic-army attack control is incomplete and can pause or fail. It requires verified TH2/10-gold state, supports only the limited basic-army UI, and has input/time caps. There is no trustworthy 98% prediction or general army/hero/spell strategy.

Game automation is subject to [Supercell's fair-play rules](https://supercell.com/en/safe-and-fair-play/). Emulator choice does not remove those restrictions.

## Verification and development

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover transport/parsing, timing guards, scene fixtures, controller decisions, experience storage and training gates. Some use controlled device boundaries. Live-game reliability needs separate validation.

- [Native product contract](docs/native-runtime-design.md)
- [Implementation phases and tasks](docs/superpowers/plans/2026-10-28-live-learning.md)
- [Live-learning design and research](research/live-learning-design.md)
- [Device investigation](docs/live-device-check.md)

Historical browser/planner code remains for reference; the default app is native. Local recordings, diagnostic output, tools, environments and session handovers are excluded from Git. No training data or model weights are bundled.
