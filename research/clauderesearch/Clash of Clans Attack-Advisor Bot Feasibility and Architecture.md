# Clash of Clans Attack-Advisor Bot: Feasibility and Architecture

Research brief · 27 October 2026 · Personal research project, nothing is being built yet

## 1. Bottom line

The vision-and-decision pipeline you describe is technically feasible on your laptop. Reading a screen, detecting defensive buildings, reading your army, scoring a matchup and tapping deployment points are all solved problems, and open-source prior art exists: MyBot.run, a YOLOv5 Electro Dragon project, public YOLO models trained on Clash bases, and ClashGO.

Three things stand in the way, and none of them is a coding problem:

1. **Policy.** Supercell lists bots and gameplay-automation scripts as prohibited third-party software, and the stated penalty is a permanent ban on the offending account.
2. **The game has changed.** Since the October 2025 Ranked Battles update, trophies are earned only in Ranked, and Ranked attacks cannot be skipped for a different target. The idea of skipping every base under 98% only works in regular Battles, which give no trophies.
3. **A 98% score cannot be computed honestly.** Traps, Clan Castle troops and exact building levels are hidden, and there is no public simulator. A score can be a calibrated estimate, never a guarantee, and a 98% threshold would skip almost every base.

**Recommendation:** build perception and scoring first as an offline analysis and advisor tool that never sends input to the game. Treat auto-attack as a separate, optional layer, because that layer is where the account risk lives.

## 2. Reality checks that change the design

### 2.1 Supercell’s rules

- The Safe and Fair Play Policy names “bots, or gameplay automation services or scripts” as third-party software, with permanent ban as the consequence.
- Supercell has announced repeated ban waves aimed at bot accounts and at players using third-party software.
- A ban hits the account: progress, purchases, everything. Never run any live automation on an account you care about.
- This document does not cover ways to hide automation from detection, and I would not help with that part.

### 2.2 Matchmaking in the current game

Supercell split multiplayer into two modes on 6 October 2025, and split Legend League into three tiers in April 2026.

| Mode | Skip with Next? | Trophies at stake? | What a bot can decide |
| --- | --- | --- | --- |
| Battles (Town Hall 2+) | Yes | No | Attack or skip, so the 98% gate is possible. Good for loot, useless for Elo. |
| Ranked Battles (Town Hall 7+) | No, limited attacks, no re-roll | Yes, weekly tournament | Only how to attack the base it is given. |
| Legend III / II / I | No | Yes | Same as Ranked. Legend III has 24 battles a week, Legend II 30 a week, Legend I 8 a day. |

If the goal is pushing Elo, the skip feature is largely moot. The value of the system moves entirely to “given this base and this army, what is the best plan?” That is a better problem anyway, because it works in every mode.

Things to verify in your own client before designing around them: the length of the scouting timer (you said 30 seconds), and whether army training times are really gone. Supercell’s September 2025 preview listed removal of army training times and hero healing time, which would make army analysis much simpler.

### 2.3 What “score” should honestly mean

- Define the score as a **calibrated probability** of a concrete outcome, for example P(at least 2 stars) or expected destruction percentage.
- Calibrated means: of all bases scored 70%, about 70% really end in that outcome. You check this with a reliability curve on your own logged attacks.
- Choose the threshold from data, not from a round number. In Battles mode you might pick the threshold that skips about 30% of bases. In Ranked mode the score is used to choose the plan, not to skip.

## 3. System architecture

```
Screen capture ─► Scene classifier ─► Base perception ─┐
                        │                              ├─► Feature builder ─► Scorer ─► Plan generator ─► Executor ─► Verifier + logger
                        └──────────► Army perception ──┘                                                      ▲
                                                                                        Guardrails + kill switch (wrap every stage)
```

Stages, in order:

1. **Capture:** grab frames from the emulator window or phone at a fixed resolution.
2. **Scene classifier:** know which screen the game is on (home, army, matchmaking, scouting, battle, result, popup).
3. **Army perception:** read troops, spells, siege machines, heroes and Clan Castle contents. This can run before matchmaking, so it costs nothing during scouting.
4. **Base perception:** detect and locate defenses, Town Hall, storages and walls on the scouting screen.
5. **Feature builder:** turn detections into numbers (defense counts, distances, compartments, air versus ground coverage).
6. **Scorer:** estimate the outcome of your army against this base.
7. **Plan generator:** choose the attack side (clock angle), funnel, troop order, spell and hero timing.
8. **Executor:** send taps and swipes at computed screen coordinates.
9. **Verifier and logger:** confirm each step happened, save screenshots and results for training.

### Latency budget (my estimates, to be measured)

| Stage | Rough time |
| --- | --- |
| Capture | 0.05 to 0.3 s depending on method |
| Scene detection | under 0.1 s |
| Base detection (YOLO nano or small on the GTX 1650 Ti, merged over a few frames) | 0.2 to 1 s |
| Army read | 0.2 to 0.5 s, and can be done earlier |
| Features and score (rules or gradient boosting) | under 0.1 s |
| Plan generation (scoring a dozen candidate plans) | 0.5 to 3 s |
| **Total** | **about 3 to 6 s, well inside a 15 s budget** |

The budget holds only because the score comes from rules or a trained model. A full battle simulation per candidate plan would blow it.

## 4. Perception

### 4.1 Capture and calibration

- **Fix the resolution and DPI.** ClashGO, for example, asks for BlueStacks at 860x732 and 160 DPI. Template matching and detector accuracy both depend on a stable resolution.
- **Capture method:** window capture (mss, DXcam) is fast. ADB screencap works but is slower. scrcpy is a good middle option, especially with a physical phone.
- **Isometric grid calibration:** the village is drawn as a diamond over a 44 by 44 tile grid. Calibrate once per zoom level by finding the diamond’s four corners and fitting a homography between screen pixels and grid tiles. After that, a building’s class plus its centre gives its tile footprint, and any grid tile maps back to a tap coordinate.
- **Camera state:** scouting usually opens at a consistent zoom, but verify. Detect and correct any drift before computing coordinates.

### 4.2 Scene state machine

Use template matching on fixed UI anchors (Attack button, Next button, Start Battle, End Battle, result banner) plus a small image classifier for ambiguous screens. Any unknown scene for more than a few seconds should pause the bot (see guardrails).

### 4.3 Base detection

- **Model:** YOLO (v8 or 11, nano or small) trained to detect Town Hall, Eagle Artillery, Scattershot, Inferno Towers, X-Bows, Air Defenses, Air Sweepers, Archer Towers, Wizard Towers, Bomb Towers, Mortars, Giga structures and the Clan Castle, storages and collectors. Walls are better handled with segmentation or a simple colour and edge heuristic.
- **Existing models:** keremberke published YOLOv5 Clash of Clans models (n, s, m) on Hugging Face. Treat them as a starting point to inspect, not as a finished solution. Their class list, quality and licence need checking, and they were trained on older versions of the game.
- **Dataset:** expect about 1,000 to 3,000 labelled scouting screenshots for a reliable detector. Collect them by playing normally and saving the scouting frame. Label with Roboflow or Label Studio, and use the first trained model to pre-label the next batch.
- **Training on your hardware:** 4 GB of VRAM is fine for inference and for training the nano or small variants at modest batch sizes. If training is slow, use a free cloud GPU for training and run only inference locally.
- **Building levels** are visually subtle. Plan for classes by building type first, and estimate level from the opponent’s Town Hall tier. Level-aware detection is a later improvement.

### 4.4 Army reading

The army and battle bars are fixed UI, so this is the easy half: template matching for troop and spell icons, plus OCR (PaddleOCR, or a small digit classifier trained on cropped counters) for quantities and levels. Read the Clan Castle contents and hero equipment the same way.

### 4.5 What you cannot see

Traps, Clan Castle defending troops, hero levels and exact building levels are hidden or hard to read. Every score is therefore a probability with irreducible noise, which is why calibration matters more than the raw number.

## 5. Decision layer

### 5.1 Three ways to compute the score

| Approach | How it works | Pros | Cons |
| --- | --- | --- | --- |
| A. Rule-based | Hand-written weights: defenses covering each side, Town Hall exposure, air defense spread, compartment count | Works on day one, explainable | Ceiling is low, needs tuning |
| B. Learned outcome model | Gradient boosting (LightGBM) or a small neural net on base features plus army features, trained to predict stars or destruction from your logged attacks | Calibratable, improves with data | Needs hundreds to thousands of logged attacks per army type |
| C. Simulator | Build a simplified battle simulator and run Monte Carlo attacks | Can test plans directly | Large effort, game mechanics are closed, accuracy is hard to verify |
| RL agent | Learn to attack by trial and error | Elegant | No public environment, far too expensive for this project |

**Recommended path:** start with A, log every attack with its outcome, then add B and blend the two. Keep C as a long-term research topic.

### 5.2 Features worth extracting

- Counts and positions of each defense type, and their distance from every possible entry side
- Town Hall position (outside, edge or deep inside) and what protects it
- Air versus ground coverage, and which side has the weakest anti-air
- Compartment structure from walls, and the length of the path from an entry point to the core
- Storage and collector placement (relevant for loot attacks)
- Your army: composition, hero levels, spell mix, Clan Castle contents, total housing space

### 5.3 Plan generator and the “clock angle”

1. Define angles around the base centre, with 12 o’clock at the top of the screen. Twelve candidate entry points, one per hour, sit just outside the red no-deploy border.
2. For each entry point, and for each attack archetype your army supports (for example a ground funnel, a hybrid, an air attack), build a concrete plan: where the funnel goes, deployment order, spell targets, hero ability timing.
3. Score every candidate with the scorer, pick the best, and keep the runner-up as a fallback.
4. Convert the plan from grid positions to screen coordinates through the homography.

This gives you the “direction on the clock, troop quantities and order” output you described, and it works the same way whether the final executor is a bot or just an on-screen suggestion.

### 5.4 Closed loop during the attack

A first version can follow a fixed script. Later, re-capture every second or so, check which defenses are down, and adapt: trigger hero abilities, drop spells, send the next wave. Tracking where your own troops are is the hardest vision problem in the project, so treat it as stretch scope.

## 6. Execution layer

- **Input method:** ADB input commands are simple but add noticeable latency. Faster options are minitouch, scrcpy’s control channel, or sending events directly to the emulator window.
- **Deployment:** troops are deployed by tapping a card, then tapping or dragging on the map; spreading a group means a swipe along the border. Spell and hero ability taps need precise timing.
- **Verification:** after every action, check the screen changed as expected (troop count dropped, ability icon greyed). If not, retry once, then abort safely.

## 7. Environment: Google Play Games on PC, emulator or phone

| Option | For | Against |
| --- | --- | --- |
| Google Play Games on PC (Beta) | Official PC route for Clash of Clans, closest to what you already know | Not designed for scripting; to my understanding it does not expose ADB or fixed-resolution control easily (please verify before relying on this) |
| Android emulator (BlueStacks, LDPlayer, MuMu, MEmu) | ADB access, resizable, fixed DPI, easy screenshots | Historically not endorsed by Supercell for its games; emulator support in bots changes constantly |
| Physical phone with scrcpy and ADB | Cleanest, no emulator overhead, full-fidelity UI | A second device, USB or wireless setup |

Notes from the research:

- MyBot.run dropped BlueStacks support in v8.1.2 and moved to MEmu and a patched Nox. The ClashGO project uses BlueStacks at a fixed size. Emulator support is a moving target.
- One outlet reports that Supercell historically did not allow emulators and that Google Play Games Beta changed that. Treat the emulator policy as unclear.

**My recommendation for you:** keep playing on Google Play Games for normal play. For development, use an emulator with ADB for capturing and labelling screenshots (BlueStacks 5 or LDPlayer are the easiest starting points), and use a physical phone with scrcpy if you want the cleanest setup. Do not test live automation on your main account.

**Your hardware (GTX 1650 Ti 4 GB, Ryzen 5 4600H, 16 GB RAM):**

- Enough for YOLO nano or small inference at real-time rates, an emulator and a Python process at the same time.
- Enable virtualization (VT-x or SVM) in the BIOS, give the emulator 2 to 3 vCPUs and about 3 GB RAM, and keep the Python side under 3 GB.
- The emulator and the detector both want the GPU. If frame times spike, lower the emulator’s render resolution or run the detector as ONNX or TensorRT.

## 8. Tech stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.11 |
| Capture | mss or DXcam, scrcpy, adbutils |
| Vision | OpenCV (templates, homography), Ultralytics YOLO, ONNX Runtime or TensorRT for inference |
| OCR | PaddleOCR or a small digit CNN |
| Modelling | NumPy, scikit-learn, LightGBM |
| Storage | SQLite for attack logs, local folders for screenshots |
| Backend glue | FastAPI over a local socket, async worker loop |
| UI | Tauri or Electron with React, or PySide6 if you want one language |
| Packaging | PyInstaller or a venv launcher |

## 9. Clean UI

Design principles: one obvious master switch, calm dark theme, a single accent colour, large readable numbers, and a live view that explains every decision. Layout:

```
┌──────────────────────────────────────────────────────────────┐
│  CoC Advisor            ● Idle     Mode: [Observe|Suggest|Auto]│
├──────────────────────────────┬───────────────────────────────┤
│  LIVE VIEW                   │  DECISION                     │
│  annotated scouting frame:   │  Score  ◔ 0.74  (calibrated)  │
│  detected defenses, tile     │  Best entry: 4 o’clock        │
│  grid, suggested entry arc   │  Plan: hybrid, 2 waves        │
│                              │  Runner-up: 7 o’clock (0.69)  │
├──────────────────────────────┼───────────────────────────────┤
│  ARMY                        │  SESSION                      │
│  troops, spells, heroes, CC  │  attacks · avg stars · skips  │
├──────────────────────────────┴───────────────────────────────┤
│  [ START ]   Threshold ▭▭▭▭▭▭○▭  0.70     [ STOP ALL  F12 ]   │
└──────────────────────────────────────────────────────────────┘
```

- **Modes:** Observe (analysis only), Suggest (shows the plan, you tap), Auto (executes). Ship Observe and Suggest first.
- **Calibration wizard:** guides the user through resolution, grid corners and a test frame.
- **Settings:** emulator path, capture method, threshold, attack caps.
- **Logs tab:** every decision with its screenshot, so wrong calls can be reviewed and added to training data.

## 10. Guardrails

1. **Global kill switch:** a hotkey and an on-screen button that stop all input within one frame.
2. **Dry-run by default:** draw the plan on screen, send nothing, until explicitly switched.
3. **Tap whitelist:** the executor may only tap inside known regions (map, troop cards, spell cards, ability buttons, Attack, Next, End Battle). The shop, gem and purchase screens are blocked outright.
4. **Confidence gates:** if the Town Hall is not detected, detector confidence is low, or the scene is unknown, abort or pause instead of guessing.
5. **Watchdog:** no recognised scene for N seconds, or no progress for N seconds, stops the bot.
6. **Session caps:** maximum attacks, maximum runtime, and a cool-down between sessions.
7. **Credentials:** never ask for or store Supercell ID, Google or Apple credentials, and never use any third-party service that asks for them.
8. **Version pinning:** the bot disables itself when the game version changes. MyBot’s v8.1.2 release needed more than 200 template changes after a single game update, which shows how fragile this is.
9. **Account hygiene:** do not test on a main account.
10. **Audit log:** every decision, screenshot and tap is saved locally.

## 11. Feasibility assessment

| Component | Difficulty | Risk | Notes |
| --- | --- | --- | --- |
| Capture and input | Easy | Low | Mature tooling |
| Scene recognition | Easy to medium | Low | Template matching and a small classifier |
| Army reading | Easy | Low | Fixed UI |
| Base detection | Medium | Medium | Labelled data is the main cost |
| Hidden information | Not solvable | High | Traps, Clan Castle, levels |
| Calibrated score | Hard | Medium | Needs your own attack logs |
| Plan generation | Hard | Medium | Archetypes first, then search |
| Closed-loop deployment | Hard | Medium | Troop tracking is difficult |
| Maintenance | Ongoing | High | Every game update can break templates |
| Policy | Blocker for auto mode | Very high | Permanent ban on the account |

Overall: perception and scoring as an advisor are realistic for a solo developer. Fully automatic Elo pushing is possible in principle, but is limited by Ranked rules, hidden information and policy risk.

## 12. Roadmap (rough estimates for one developer)

- **Phase 0, data (1 to 2 weeks):** capture 1,000 or more scouting screenshots and army screens during normal play.
- **Phase 1, perception (2 to 4 weeks):** scene classifier, army reader, building detector, grid calibration, all offline on saved images.
- **Phase 2, scoring (3 to 6 weeks):** rule-based score, attack logger, then a learned model and a calibration curve once a few hundred logged attacks exist.
- **Phase 3, advisor UI (about 2 weeks):** Observe and Suggest modes with the annotated live view and the clock-angle plan.
- **Phase 4, auto-execution (open-ended, optional):** only after weighing the policy risk, and never on an account you value.

Phases 0 to 3 can all be done without sending any input to the game.

## 13. Prior art and sources

- Supercell Safe and Fair Play Policy: supercell.com/en/safe-and-fair-play/
- Supercell, Battle and Ranked Modes announcement (2 Sept 2025): supercell.com/en/games/clashofclans/blog/news/battle-and-ranked-modes-are-coming-to-clash-
- Supercell, Get Ready for Ranked update notes (6 Oct 2025): supercell.com/en/games/clashofclans/blog/release-notes/get-ready-for-ranked-update
- Supercell, The Sound of Clash update notes (April 2026, Legend tiers): supercell.com/en/games/clashofclans/blog/release-notes/the-sound-of-clash-update
- Clash Ninja, Battle and Ranked modes (no skipping in Ranked): clash.ninja/blog/battle-and-ranked-modes
- MyBot.run v8.1.2 release notes: github.com/MyBotRun/MyBot/releases/tag/MBR\_v8.1.2
- ClashGO (Go, template matching): pkg.go.dev/github.com/Ducky705/ClashGO
- auto-coc (SikuliX): github.com/atomhax/auto-coc
- YOLOv5 Electro Dragon write-up: alexxiang.substack.com/p/automating-clash-of-clans-attacks
- keremberke YOLOv5 Clash of Clans models: mixpeek.com/model/keremberke/yolov5s-clash-of-clans

## 14. Open questions

- Your exact Town Hall level (12 versus 13 changes the detector’s class list)
- Whether you mainly play Ranked or regular Battles
- Your usual army composition
- Whether the goal is learning and research, or eventually running this on your main account
