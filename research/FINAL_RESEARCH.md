# Clash of Clans attack system: final combined research

27 October 2026 | Consolidated from the Claude and Codex reports | Markdown is authoritative

## Executive Summary

The best combined direction is a TH13-first attack adviser built around pre-match army confirmation, reliable screen-state recognition, a small library of legal candidate plans, and plan-conditioned outcome estimates. It should first be evaluated offline and through human-executed challenges. The original ambition of every Town Hall, every army, every mode, ninety-eight-percent outcomes, and a fifteen-second decision remains a research goal rather than demonstrated capability.

Claude's report is the stronger practical component sketch: scene states, UI layout, reusable detector leads, calibration tools, and operational checks. Codex's report is stronger on evidence boundaries, consumer Google Play Games versus the Developer Emulator, prediction definitions, hidden-state uncertainty, and representative validation. The final design combines those strengths while dropping unsupported hardware timings, guaranteed dataset sizes, fixed development schedules, and assertions that the complete problem is already solved.

For the user's Ryzen 5 4600H, GTX 1650 Ti, and 16 GB RAM laptop, retain Google Play Games for normal play and recording. It is an officially supported CoC platform; consumer debugging or control interfaces must not be inferred from Google's separate Developer Emulator documentation. Actual capture, inference latency, and memory use need measurement on the supplied machine. [5][6][7]

The most useful new reusable asset is an existing CoC detector, subject to a current-image audit. Its model card reports self-reported validation mAP@0.5 of 0.828; that is not attack success. The linked dataset card declares 125 images and a specific `th13` label, which makes it a baseline to inspect rather than evidence of all-Town-Hall coverage. [19][20]

Regular farming and competitive ranking require different selection policies. Do not assume unrestricted target replacement in every mode. Live gameplay automation is prohibited by Supercell's published policy; offline experiments do not establish approval for a live competitive adviser. The recommended next step is a small perception and planning experiment, with expansion controlled by evidence rather than a promised completion date. [1][2][3][4]

## Introduction

This document is the final synthesis, not a concatenation of both reports. It preserves supported facts, useful explicitly labeled design proposals, and open questions that materially affect feasibility. It does not treat agreement between two AI reports as verification. The original files remain preserved: [Codex research](D:/COC_bot/research/clash-of-clans-feasibility.md) and [Claude research](<D:/COC_bot/research/clauderesearch/Clash of Clans Attack-Advisor Bot Feasibility and Architecture.md>).

The user's requirements are retained: inspect the player's own army before matchmaking; assess opponents from the screen; choose troop quantities, locations, clock directions, and timing; eventually support autonomous execution; and aim to decide within fifteen seconds. Current Town Hall is approximately 13. Exact army, installed client version, scouting controls, and hardware behavior have not been inspected. Builder Base and Clan Capital need separate rules and validation rather than inheriting Home Village support.

## Comparison: what survives from each report

| Topic / use case | Stronger contribution | Final decision |
|---|---|---|
| Understanding the first prototype | Claude's concrete component and UI breakdown | Keep, with a smaller initial stack |
| Finding reusable perception assets | Claude's detector and bot references | Keep verified leads, audit coverage and licensing |
| Prediction and the meaning of 98% | Codex's probability/destruction/confidence distinctions | Keep; correct Claude's mixed definition |
| Scorer/planner ordering | Codex diagram and Claude section 5.3 | Generate candidate plans before final outcome scoring |
| Google Play Games compatibility | Codex's consumer/developer distinction | Prefer supported normal-play client; verify interfaces separately |
| Mode-specific target selection | Both identify farming versus ranking | Keep; qualify categorical current no-Next claims |
| Exact levels and hidden information | Codex's explicit unknowns | Do not substitute Town Hall tier for observed levels |
| Verification and recovery | Claude's detailed checks, Codex's duplicate-input caution | Verify actions; remove blind retry-once behavior |
| Reliability and generalization | Codex's frozen-policy and coverage evaluation | Keep, using one initial endpoint and baseline |
| Scope, milestones, and software layers | Both need pruning | Use measured gates; remove arbitrary weeks, data quotas, and early service layers |

Claude's assertion that screen reading, matchup scoring, and deployment are all solved overstates the inspected evidence. Codex's initial report, conversely, is too expansive as a first-prototype brief: multiple outcome distributions, many metrics, and several evaluation strata should not all become initial implementation requirements. Neither report provides a measured end-to-end result on the user's machine.

## Main Analysis

### 1. Choose the system by use case

| Use case | Best combined approach | Success measure |
|---|---|---|
| Learning and feasibility research | Saved screenshots, confirmed army, annotated plan preview | Correct visible-state extraction and reproducible plans |
| Improving TH13 attacks | One fixed army, human-executed Friendly Challenges | Planner versus a simple predefined baseline under comparable conditions |
| Regular-Battle farming | Mode-aware target recommendation where Next is available | Outcome or resource value per encounter/time, including rejection cost |
| Ranked / Legend progression | Best supported policy for the available opponent | Actual mode-specific ranking utility across available attacks |
| Every Town Hall and army | Expand tested combinations incrementally | Per-combination coverage, failures, and deadline compliance |
| Autonomous execution research | Separate controller after planning value is demonstrated | Correct action delivery and feedback; policy restrictions remain independent |

The mode split is documented by Supercell. Current Ranked support also prevents beginning a new battle before the current one finishes. The inspected current primary material does not independently settle every tier's pre-attack Next control, so the final document does not turn a secondary-source statement into a universal current rule. Confirm the actual interface before implementing rejection logic. [3][4]

Friendly Challenges provide a useful human-run evaluation setting, but their configured conditions must be recorded and must not be presumed equivalent to every competitive mode. For ranking, a fixed destruction cutoff may select the wrong objective; the utility should reflect the actual mode's rewards and limited opportunities. [4][24]

### 2. Final architecture

```text
Preflight: mode/version + selected army + capture calibration
                            |
Fresh frame -> scene recognition -> visible spatial state + unknowns
                            |
              generate legal, inventory-feasible plans
                            |
           score each plan's outcome and support status
                            |
                select by mode-specific objective
                            |
             annotated advice / explicit abstention
                            |
       later execution research: observe -> act -> verify -> update
                            |
                  outcome and deviation log
```

Read the selected recipe, actual troop quantities and levels, spells, attacking heroes/equipment, and relevant support units before matchmaking. Treat this as a versioned snapshot, not permanent knowledge. Refresh it after a recipe, loadout, availability, mode, or relevant version change. Use the player's village to locate the relevant screens and progression context; defensive wall arrangement does not describe the offensive force.

Recognize explicit scenes such as home, army selection, matchmaking, scouting, active battle, result, and unknown/modal. Unknown scenes should stop new input or return control, not trigger guessed navigation. Stable icons can use template matching; buildings can use a custom detector; counters can use cropped digit recognition or OCR. OpenCV and Ultralytics document these component capabilities, but their documentation does not establish CoC-specific accuracy. [10][12]

Represent visible building type, position, level evidence, walls, deployment space, camera state, and uncertainty separately. An unobserved level stays unknown or becomes a clearly labeled prior/range. A Town Hall tier can constrain possibilities; it is not a verified substitute for every actual building level. Exact present visibility should be checked in each screen/mode rather than declaring all levels or defending units universally invisible.

Clock directions explain the plan to the user. Internally, store a legal point or segment, coordinate-frame version, and positional tolerance. A planar transformation can support calibrated ground geometry, but a sprite's box center does not automatically identify its footprint. Use ground anchors and known footprint information where validated, and recheck calibration after camera or scale changes. Do not hard-code an assumed universal grid size unless it is needed and verified. [11]

Generate a small set of army-compatible entry sectors and attack templates. Each candidate needs troop/spell quantities, legal locations, sequencing, observable triggers, timeouts, and confirmation conditions. Reject candidates that exceed the inventory or require unavailable mechanics. Only then estimate that candidate's outcome. Claude's main Scorer -> Plan Generator diagram is corrected; its later candidate-scoring description already follows this more defensible ordering.

During any later execution experiment, reobserve selection, counts, scene, and expected effects. An uncertain acknowledgement is not proof that an input failed. Retry only when nonexecution has been established; otherwise delayed input could be duplicated. A fixed script is a possible experimental baseline, but verified actions and evolving observations are required before calling the controller robust. A Stop control cancels future actions; it does not pause or undo an ongoing game.

### 3. Prediction: define the event before displaying a percentage

Separate the following outputs:

- **Expected destruction:** E[D], an average predicted destruction value.
- **Threshold success:** P(D >= 0.98), probability of reaching at least 98% destruction.
- **Three-star probability:** a different event.
- **Detection confidence:** confidence in a visual classification, not battle success.
- **Statistical confidence:** uncertainty about a measured population rate.

For example, equal chances of 97% and 99% destruction give 98% expected destruction but only a 50% chance of reaching 98%. Claude's definition of a calibrated probability followed by expected destruction needs this correction. A weighted heuristic should be called a heuristic until outcomes support fitting and checking a probability model. Calibration research also warns against assuming numerical confidence remains valid under dataset shift. [14][15]

The initial model should estimate one clearly chosen endpoint for a concrete plan: P(success | observed state, confirmed army, proposed policy, mode, version). Hidden information calls for uncertain-state assumptions and robust plans; it does not prove successful planning impossible. Likewise, a 98% threshold might produce low coverage, but neither report has data establishing that it would reject almost every base.

Start with an explainable rule baseline. A small learned tabular outcome model can be tested once logged cases connect observations, chosen actions, and outcomes. Record which plan was actually executed and deviations from it. A replay observes one sequence/outcome; it does not validate every untried timing or alternative entry. Offline-learning literature supports caution about unsupported actions and distribution shift, not a blanket claim that counterfactual learning is impossible. [17]

Do not claim a public simulator does not exist: the earlier research inspected a toy CoC simulator. Its modeled HP-reduction percentage needs validation before being interpreted as the game's destruction outcome. The useful statement is that no inspected simulator establishes the fidelity required for the proposed forecast. Simulator search or reinforcement learning should earn its place through validated mechanics and useful experiments. [23]

When the policy and threshold are frozen, report success among accepted cases and acceptance coverage together. Under independent representative accepted Bernoulli trials, 149 successes with no failures is the minimum best-case example whose one-sided 95% exact lower bound exceeds 98%: 0.05^(1/149) is approximately 0.980095. This is neither a training-set size nor an individual-battle guarantee. Failures, correlation, threshold tuning, and repeated testing require further analysis. [16]

### 4. Platform, reusable assets, and the smallest useful stack

Keep Google Play Games for supported normal play and initial recording. Test Windows window capture on that actual installation. ADB and scrcpy are useful documented Android laboratory interfaces where legitimately available, but consumer Google Play Games access cannot be inferred from developer-emulator documentation. Do not install an additional emulator solely because another bot used it historically. [5][6][7][8][9]

The public CoC API's accessible material did not establish a live battlefield, selected-army, control, or simulator interface. Its detailed dynamic schema was not fully accessible during the original research. Preserve that retrieval limitation; do not infer complete endpoint absence or that profile units equal the army selected for the current attack. [18]

Claude's detector lead is worth retaining. The keremberke model card reports self-reported validation mAP@0.5 of 0.828. Benchmark it on current screenshots before training a replacement; do not interpret that metric as success probability or transfer it to another image distribution. No model was downloaded or executed during this comparison. [19]

Its linked dataset card declares 88 training, 13 test, and 24 validation images, totaling 125, with 16 labels including `th13`; it describes a March 2022 export. The web viewer's aggregate differs, so these are card-declared figures, not a fresh file audit. The card states CC BY 4.0 for the dataset; this does not establish model-weight/code licensing or settle underlying third-party rights. This asset is useful for an initial TH13-oriented perception audit, not proof of complete defense, level, or Town Hall coverage. [20]

MyBot's v8.1.2 notes describe support for the October 2023 game update, including 29 changed OCR libraries, over 200 image-template changes, and changes in approximately 100 files. That is concrete historical evidence for maintenance costs. Its emulator compatibility table is not a current recommendation. [21]

ClashGO is useful architectural prior art for calibration, structured strategies, and drawing an attack plan without tapping. The linked author repository is Mac/Apple-Silicon oriented, reports performance in that environment, and requests Windows port/testing work. Treat it as a reference rather than a ready Windows dependency or benchmark for the user's laptop. [22]

| Need | Proposed first choice | Add complexity only when |
|---|---|---|
| Experiment runner | One Python process and local files | Measurements show a real separation is necessary |
| Screens/UI anchors | OpenCV templates plus explicit scenes | Ambiguous scenes justify a classifier |
| Building perception | Audit the existing detector; then adapt/train if needed | Current-image errors establish the gap |
| Army counters | Small cropped digit/icon recognition | A broader OCR engine proves useful |
| Inference | Benchmark an ONNX option against the existing model path | A compatible accelerated backend measurably helps |
| Outcome model | Rule baseline, then a small fitted classifier | Sufficient representative data and held-out improvement exist |
| Logging | Local structured records; SQLite if query needs justify it | Data volume or review tasks require more |
| UI | Annotated saved-frame preview first; one desktop UI later | Perception and planning have earned live presentation |

FastAPI plus a web frontend plus Electron/Tauri is unnecessary for the first experiment. These are future architecture options, not requirements. The user's laptop is the benchmark target: compare CPU and available compatible GPU inference while the client is running. Do not assert a VRAM allocation, free-cloud availability, training sufficiency, or real-time performance without observing it. ONNX Runtime's profiling tools can help identify bottlenecks. [13]

### 5. Latency, interface, and execution boundaries

Keep fifteen seconds as the requested end-to-end target. Discard Claude's 3-6-second total as a feasibility conclusion: it is an estimate, and no inspected result measures the combined system on this laptop. Codex's twelve-second path plus three-second reserve is also a design allocation, not validation. Use timing measurements to allocate the budget after the first offline run rather than present either table as achieved performance.

Start timing at the first usable opponent observation and include frame age, capture, scene detection, perception, geometry, candidate generation, scoring, and final validation. Load models and read the army during preflight where possible. Record median, p95, worst observed duration, and deadline misses; report cold and warm runs separately. A fast detector alone does not establish a fast complete planner.

Keep Claude's annotated view and clear Start/Stop controls. The minimum useful interface shows the captured frame, recognized scene, confirmed army snapshot, supported mode, suggested entry and sequence, a clearly named score, and the reason for abstention. Until calibrated outcome data exists, display a heuristic or insufficient-data status rather than label the number calibrated. Observe and Suggest are useful experimental stages; autonomous input is a separate later decision.

Any later input controller should constrain actions to validated scene/regions, cancel queued actions on Stop, and avoid guessed navigation through unknown or purchase-related screens. Measure stop responsiveness rather than promise a one-frame response. A watchdog can detect stale frames or stalled progress, but cannot pause a battle already running. Coordinate verification and action confirmation belong in the first controller experiment, even if troop tracking and adaptive tactics are added incrementally.

Supercell's Terms and CoC enforcement announcement explicitly address gameplay bots and permanent account bans. Using a secondary account, calling the software research, or sending ordinary mouse events does not supply a documented exemption. Offline analysis removes automated control; permission for a live competitive adviser remains unresolved. The policy question and the technical benchmark are separate decisions. [1][2]

## Synthesis: what was removed or corrected

| Original claim or choice | Final treatment |
|---|---|
| The whole pipeline is solved on this laptop | Unsupported; component availability does not establish full-system performance |
| A 98% threshold skips almost every base | Unmeasured coverage; remove the numerical implication |
| A reliable detector needs 1,000-3,000 screenshots | No universal sufficiency bound; collect according to class coverage and measured errors |
| Hundreds/thousands of attacks per army guarantee a scorer | No fixed requirement established; labels, selection bias, and action support matter |
| Town Hall gives exact defense levels | Use observed evidence or explicit uncertain priors |
| Bounding-box center automatically gives a building footprint | Calibrate ground anchors and validate geometry |
| No public simulator exists | Toy simulators exist; required fidelity is unvalidated |
| All hidden information makes the problem unsolvable | Exact recovery and robust planning are different problems |
| Retry once after no immediate confirmation | Reobserve; retry only when nonexecution is established |
| Stop is guaranteed within one frame | Measure cancellation; never imply the game itself pauses |
| All current Ranked tiers categorically have identical skip controls | Current per-mode UI verification remains required |
| BlueStacks settings and development-week estimates are settled | Historical/untested suggestions; remove them from the recommended baseline |

The resulting system is an experiment with a clear expansion path: observable state, explicit uncertainty, small candidate policies, measured predictions, and verified actions. It supports the user's ambition without representing every Town Hall or every army as already covered.

## Recommendations: milestones with measurable exits

1. **Perception audit:** use roughly 20-30 diverse current scouting observations and manually confirmed army snapshots. Measure missing key objects, count errors, uncertain levels, geometry errors, and total processing time. This is a proposed diagnostic set, not sufficient training data or a statistical guarantee.
2. **Plan preview:** generate inventory-feasible candidate plans for one TH13 army and mode. Show legal deployment geometry, clock labels, sequence, and uncertainty on saved frames. Fail visibly on unsupported cases.
3. **Planning comparison:** compare a predefined baseline with the planner through human-run challenges. Make the denominator explicit: for example, 20 matched pairs means 40 total attacks, one baseline and one planner attack per pair. Counterbalance order and document conditions. This example is a diagnostic design, not a powered proof of superiority or 98% reliability.
4. **Outcome estimation:** log actual actions, deviations, and results; train only once the data supports a meaningful fit. Freeze the complete candidate-generation/scoring policy before held-out testing. Measure the chosen outcome and acceptance coverage.
5. **Latency validation and expansion:** test the complete pipeline on the actual laptop, then add armies/levels/modes where separate evidence supports them. Investigate live observation and any later controller independently; automation policy remains a deployment constraint.

## Limitations & Caveats

Neither report supplies an implemented or benchmarked system. The comparison did not inspect the installed game, verify the current army, download models, train a detector, or run an attack. New source checks establish what authors document, not whether the software works as advertised. Exact scouting time and target-replacement behavior still require a manual check in the intended mode.

Useful ideas are retained as design proposals rather than promoted to proven facts. The final combined research does not promise a completion date, a minimum sufficient dataset, universal compatibility, or calibrated success from an untrained estimator. A favorable narrow result could justify further work; it would not establish every-match performance.

## Methodology and provenance

This was a requested quick consolidation. It reused the original five-researcher evidence review and added two focused follow-up reviewers: First Principles checked conceptual consistency and corrections in both reports; Partner independently checked the added model, dataset, historical MyBot release, and ClashGO sources. This was not a second five-person independent investigation. The chair checked the reports and primary additions, selected claims, and wrote the merged document.

Both reviewers agreed on the qualified architecture after source inspection; agreement itself was not used as proof. Material unresolved questions remain labeled. The source registry/evidence/claims files from the original study are preserved. New retrieval evidence is in [merge-evidence.jsonl](D:/COC_bot/research/merge-evidence.jsonl). This Markdown file is the final combined research; the earlier PDF and HTML describe the earlier Codex report and are not updated editions of this synthesis.

## Bibliography

[1] Supercell (n.d.). "Terms of Service". [Primary source](https://supercell.com/en/terms-of-service/) (Retrieved: 2026-10-27).

[2] Supercell (2024). "Update to our Fair Play Policy and Next Steps". [Primary source](https://supercell.com/en/games/clashofclans/blog/misc/update-to-our-fair-play-policy-and-next-steps/) (Retrieved: 2026-10-27).

[3] Supercell (2025). "Get Ready for Ranked Update!". [Primary source](https://supercell.com/en/games/clashofclans/blog/release-notes/get-ready-for-ranked-update/) (Retrieved: 2026-10-27).

[4] Supercell Support (n.d.). "Ranked Leagues". [Primary source](https://support.supercell.com/clash-of-clans/en/articles/ranked-leagues-4.html) (Retrieved: 2026-10-27).

[5] Supercell Support (n.d.). "Clash of Clans & Clash Royale Now on PC with Google Play Games". [Primary source](https://support.supercell.com/clash-of-clans/en/articles/clash-of-clans-clash-royale-now-on-pc-with-google-play-games.html) (Retrieved: 2026-10-27).

[6] Google (n.d.). "Google Play Games on PC Developer Emulator". [Primary source](https://developer.android.com/games/playgames/pg-emulator) (Retrieved: 2026-10-27).

[7] Microsoft (n.d.). "Screen capture". [Primary source](https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture) (Retrieved: 2026-10-27).

[8] Google (n.d.). "Android Debug Bridge (adb)". [Primary source](https://developer.android.com/tools/adb) (Retrieved: 2026-10-27).

[9] Genymobile (n.d.). "scrcpy". [Primary source](https://github.com/Genymobile/scrcpy) (Retrieved: 2026-10-27).

[10] OpenCV (n.d.). "Template Matching". [Primary source](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html) (Retrieved: 2026-10-27).

[11] OpenCV (n.d.). "Basic concepts of the homography explained with code". [Primary source](https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html) (Retrieved: 2026-10-27).

[12] Ultralytics (n.d.). "Object Detection with Ultralytics YOLO". [Primary source](https://docs.ultralytics.com/tasks/detect/) (Retrieved: 2026-10-27).

[13] ONNX Runtime (n.d.). "Profiling tools". [Primary source](https://onnxruntime.ai/docs/performance/tune-performance/profiling-tools.html) (Retrieved: 2026-10-27).

[14] Guo et al. (2017). "On Calibration of Modern Neural Networks". [Primary source](https://proceedings.mlr.press/v70/guo17a.html) (Retrieved: 2026-10-27).

[15] Ovadia et al. (2019). "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift". [Primary source](https://proceedings.neurips.cc/paper_files/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html) (Retrieved: 2026-10-27).

[16] NIST (n.d.). "Exact Binomial Confidence Limits". [Primary source](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm) (Retrieved: 2026-10-27).

[17] Kumar et al. (2020). "Conservative Q-Learning for Offline Reinforcement Learning". [Primary source](https://proceedings.neurips.cc/paper/2020/file/0d2b2061826a5df3221116a5085a6052-Paper.pdf) (Retrieved: 2026-10-27).

[18] Supercell (n.d.). "Clash of Clans API". [Primary source](https://developer.clashofclans.com/) (Retrieved: 2026-10-27).

[19] keremberke (n.d.). "YOLOv5s Clash of Clans model card". [Primary source](https://huggingface.co/keremberke/yolov5s-clash-of-clans) (Retrieved: 2026-10-27).

[20] keremberke / Find This Base (n.d.). "Clash of Clans object-detection dataset card". [Primary source](https://huggingface.co/datasets/keremberke/clash-of-clans-object-detection/raw/main/README.md) (Retrieved: 2026-10-27).

[21] MyBotRun (2023). "MBR_v8.1.2 release notes". [Primary source](https://github.com/MyBotRun/MyBot/releases/tag/MBR_v8.1.2) (Retrieved: 2026-10-27).

[22] ClashGo authors (n.d.). "ClashGo repository and README". [Primary source](https://github.com/DSargent21/ClashGo) (Retrieved: 2026-10-27).

[23] Royz2123 (n.d.). "Clash-of-Clans-AI simulator.py". [Primary source](https://github.com/Royz2123/Clash-of-Clans-AI/blob/master/simulator.py) (Retrieved: 2026-10-27).

[24] Supercell Support (n.d.). "Friendly Challenges". [Primary source](https://support.supercell.com/clash-of-clans/en/articles/friendly-challenges-3.html) (Retrieved: 2026-10-27).
