# Live analysis and learning implementation plan

> **For agentic workers:** Use the executing-plans skill to implement this plan task by task; independent tasks may use subagent-driven-development when explicitly authorized. Checkboxes track completed work, not intent.

**Goal:** A native local controller that analyses a continuous game stream and learns a validated outcome predictor from complete battle episodes.

**Architecture:** Separate capture, observation, control and training. Decode continuously into one newest-frame slot; use local perception/control during battle and train immutable candidate models only while idle. Prediction improvement and policy improvement are evaluated separately.

**Tech stack:** Existing Python/Tk/Pillow/NumPy/ADB; proposed pinned scrcpy server and PyAV for video, SQLite for episodes, scikit-learn for initial offline regression. Add ONNX Runtime only when a validated trained detector requires it. No package installation occurred during planning.

**Spec:** [Live learning design](../../../research/live-learning-design.md). This extends, rather than replaces, [the native runtime contract](../../native-runtime-design.md).

## Global constraints

- Native UI; no upload workflow, browser product or remote model in the action loop.
- Local emulator only; no Windows mouse/focus takeover. Regular Battles first; read the current army.
-750ms stale-action ceiling stays. Unknown source freshness blocks actions. Encoder PTS is not a host timestamp.
- No training, PNG encoding or disk writes blocking capture/inference. Model snapshot fixed during each battle.
- Unknown state/inventory/result is explicit; no fabricated labels, counterfactual outcomes or confidence scores.
- Proposed performance targets in the spec are acceptance experiments, not claims about this laptop.
- No commits/worktrees required: this project currently has no Git repository. Preserve historical evidence and the single HANDOVER.md.

## Review focus

1. Decoder/scheduler backlog must not look like a fresh source frame (Task1).
2. Resizing/camera motion/army changes invalidate derived geometry/state (Tasks1–2).
3. App transition, disconnection or Stop during a queued deployment prevents additional inputs (Task3).
4. Partial battles and misread results never become valid training labels (Task4).
5. Related frames, duplicate bases, changed features or model reloads cannot contaminate evaluation or silently change serving semantics (Tasks5–7).

## Task1 — Persistent capture with measurable freshness

**Files:** create `coc_advisor/stream.py`, `tests/test_stream.py`, `scripts/benchmark_live.py`; modify `device.py`, `native.py`, `requirements-native.txt` and launcher dependency check only as necessary.

**Interfaces:** `VideoStream(client: AdbClient, serial: str)` owns pinned server/socket/decoder lifecycle; `start()`, `latest() -> LiveObservationFrame | None`, `stop()`; frame carries sequence, serial, decoded image, encoder PTS, host receive/decode monotonic times and optional conservative acquisition lower bound. `benchmark_live` reports distributions and unknown bounds, not merely an FPS average. Preserve raw capture as explicit fallback; don't silently enable actions on it when stale.

- [ ] Write failing tests: fragmented/truncated protocol records fail cleanly;100 incoming decoded frames leave exactly1pending frame (sequence100); sourcePTS is preserved independently of host timestamps; absent/unverified acquisition bound rejects input; stalled source with recently decoded buffered frames cannot pass freshness.
- [ ] Run `python -m unittest discover -s tests -p test_stream.py -v`; observe expected failures before implementing.
- [ ] Implement persistent draining/decoding and latest decoded slot, bounded stop/cleanup, matching protocol version checks and errors. Preserve decode continuity; remove PNG generation from the live path and encode only on record/export. Reuse existing serial/package/input validation.
- [ ] Benchmark source timing/clock domain first; implement a conservative freshness bound only if justified by that experiment. If absolute source age cannot be bounded, show unknown and keep actions off; instrument a known visual response round trip. Do not weaken the750ms guard.
- [ ] Run60seconds at960x540/target15fps while game is behind another app. Report startup, p50/p95/p99 observation age/queue delay, CPU/GPU, missed frames, source-age uncertainty and stop time. Test resolution changes and reconnect invalidation. If scrcpy fails, compare the smaller persistent screenrecord/PyAV experiment before committing to further protocol code.
- [ ] Run full `python -m unittest discover -s tests -v`; review before proceeding to live actions.

**Deliverable:** Native preview consumes a continuous stream and reports honest age/health. No combat claim.

## Task2 — Automatic observations from the current game

**Files:** create `coc_advisor/perception.py`, `tests/test_perception.py`; add labeled replay fixtures under `tests/fixtures/perception/`; modify `native.py` to display state/unknown fields.

**Interfaces:** `observe(frame, previous_state=None) -> GameObservation`, containing frame identity/time, scene (`home`, `army`, `search`, `scout`, `battle`, `result`, `unknown`), confidence-bearing inventory/layout/HUD fields and coordinate-transform version. No future result is included in preattack features. Slow static recognition is separate from fast combat ROI updates.

- [ ] Create independent labeled fixtures across scenes, cloud transitions, troop counts, animation, resolutions and unknown armies. Test exact expected scene/count/result values; low-confidence/contradictory fields remain unknown. Keep whole battles separate between fitting and evaluation.
- [ ] Watch fixture tests fail, then implement the smallest reliable templates/cropped-number pipeline using existing libraries. Add a trained detector/OCR only for a measured recognition gap and record its provenance/version.
- [ ] Test zoom/camera changes invalidate layout coordinates; town-hall/player-level distinction; no camp-occupant counting as selected inventory; final-result consistency and stable re-observation.
- [ ] Benchmark local observation latency and held-out false-positive/missed-event rates. Unknown critical inventory or layout keeps the controller paused; broad army support remains required, with explicit capability limits during development.
- [ ] Run full suite. GPU acceleration, if needed, gets an explicitly pinned compatibility smoke test beside the running game; CPU fallback must be visible rather than silent performance degradation.

**Deliverable:** Automatic structured state/army/result extraction; no manual annotation as the normal runtime flow.

## Task3 — Local controller and feedback on deployment

**Files:** create `coc_advisor/controller.py`, `tests/test_controller.py`; modify `device.py`, `native.py` and `tests/test_native.py`.

**Interfaces:** `Controller.tick(observation) -> list[ActionIntent]`; executor validates each intent's originating frame, transform, target package and stop state; `Controller.stop()` cancels future intents. At most one device command is in flight. A bounded hold records intended duration and cannot be presented as instantly cancellable after submission.

- [ ] Write failing replay tests: home→army→search→scout→battle→result→home; unknown army stops; repeated observations don't duplicate a deployment; inventory decreases confirm actual deployments; Stop/app-switch/disconnect invalidates queued actions.
- [ ] Implement local state machine and explicit initial tactics for validated troop capabilities, checking actual remaining counts after each bounded deployment. Existing manual exposure heuristic is not a strategy model. Log unsupported capabilities clearly and expand coverage from actual selected armies.
- [ ] Add a real native Start/Stop only when the state machine can execute its advertised path; no chat call between ticks. Use5Hz initial policy evaluation, with faster measured ROI events where needed. Do not assume the observed16troops/2.5seconds is a universal rate.
- [ ] Replay a complete episode without contacting a model/API; then conduct one bounded live diagnostic with logs and review. Confirm no Windows mouse commands, no purchases, correct resolution/geometry, bounded preparation and action timing.
- [ ] Run full suite and report actual preparation/reactive latency, unsupported capabilities and outcome separately.

**Deliverable:** First real standalone local control loop; success on TH2 does not certify all armies/THs.

## Task4 — Complete episodes and prediction/result joins

**Files:** create `coc_advisor/experience.py`, `tests/test_experience.py`; modify `recording.py` for asynchronous evidence export, and controller observation/action hooks. SQLite/events remain local under `recordings/experience/`.

**Interfaces:** `ExperienceStore(root)`; `begin_battle(context) -> battle_id`; `append_event(battle_id, kind, payload)`; `record_prediction(battle_id, prediction)`; `finish_battle(battle_id, result_evidence)`. Use schema_version1. Episodes contain original preattack features/plan/controller versions and terminal result status; events contain monotonic time plus session identifier, frame/action/model references and UTC metadata.

- [ ] Write failing tests: prediction/result join is by battle ID; duplicate finalization is idempotent; missing/malformed/out-of-range/contradictory results are quarantined; skipped opponents get no outcome label; interrupted episode remains incomplete; failed disk write becomes visible without blocking control.
- [ ] Implement durable SQLite metadata/event transactions and bounded background evidence export. Keep keyframes/optional video, not every inference frame as PNG. If evidence export falls behind, drop optional frame exports and count drops; never silently drop accepted action/result metadata.
- [ ] Validate feature timestamps precede prediction and preserve the exact feature snapshot. Model guesses never become labels; valid statuses are provisional/accepted/quarantined/incomplete with evidence provenance.
- [ ] Test a full recorded/replayed episode and run full suite. The earlier guided battle lacks complete logs and is not imported as invented training data.

**Deliverable:** A reproducible dataset of what was known, predicted, done and observed.

## Task5 — Outcome predictor and honest evaluation

**Files:** create `coc_advisor/prediction.py`, `coc_advisor/training.py`, `tests/test_prediction.py`, `tests/test_training.py`; add a separate training requirements file if needed.

**Interfaces:** `predict(features, model_snapshot) -> Forecast` with `expected_destruction: float | None`, supported-domain status, model/schema versions and no fabricated probability. `train_candidate(accepted_episodes, destination) -> CandidateReport`. Target is final destruction0–100 conditioned on preattack observations and the planned strategy/controller. Train StandardScaler+Ridge initially; export feature order/scaler/weights/intercept as validated numeric JSON. No arbitrary pickle loading in the controller.

- [ ] Write failing tests: no model/no supported domain yields unknown;100frames from a battle cannot cross partitions; later battle features cannot enter earlier predictions; preprocessing fits training only; schema mismatch/NaN/non-finite weights rejects an artifact; predictions are bounded0–100.
- [ ] Implement historical-mean baseline and a small regression candidate. Retain whole-battle chronological partitions; separate repeated bases where evaluating unseen-base generalization. Record excluded/missing examples rather than silently coercing unknowns to0.
- [ ] Report destruction MAE in percentage points, baseline comparison, counts and error by TH/army slice. Use training/validation/prospective periods that do not overlap. No95/98% success claim is generated from one battle or regression output.
- [ ] Validate numeric artifact inference equals offline fitted prediction on held-out feature fixtures. Run shadow forecasts prospectively before the model can influence attack selection. No guessed targets for skipped bases or alternate unplayed plans.
- [ ] Run full suite. Delay a probability classifier until its separate target and calibration dataset exist; Brier/reliability metrics then supplement regression metrics.

**Deliverable:** A measured destruction predictor, not learned deployment intelligence.

## Task6 — Idle retraining, candidate gates and rollback

**Files:** extend `training.py`, `prediction.py`, `native.py`; create `tests/test_learning_cycle.py`.

**Interfaces:** `LearningCoordinator.on_completed_battle(battle_id)` schedules a candidate only when idle; `evaluate_candidate(candidate, incumbent, evaluation_ids) -> PromotionDecision`; `activate_between_battles(approved_snapshot)` is atomic. Persist active/previous model IDs and evaluation manifests.

- [ ] Write failing tests: delayed label is scored before it becomes training input; no result means no learning; battle-active state prevents training/model swap; schema/unsupported-TH mismatch rejects candidate; restart retains incumbent; rejected model does not replace it.
- [ ] Initial engineering guardrails: require at least20accepted earlier training battles,20disjoint later evaluation battles and20subsequent prospective confirmations before automatic activation. These are configurable operational minima, not proof of sufficient data or98% reliability. No new model exists until these requirements can be evaluated honestly.
- [ ] Require candidate MAE below incumbent and historical-mean baseline on the same evaluation and prospective sets; paired battle-level bootstrap95% upper bound for candidate-minus-incumbent MAE must be below0. Require no MAE regression on any declared supported TH/army slice; inadequate slice evidence means unsupported/abstain, not a universal model. Store counts/uncertainty and use newly arriving confirmation data for each promotion attempt rather than repeatedly tuning against one frozen test set.
- [ ] Implement training as a separate idle worker/process, immutable serving snapshot, atomic manifest activation and previous-model rollback. A data/schema failure keeps the previous model; a battle starting preempts/defer training without loading an unfinished artifact.
- [ ] Run full suite and replay scheduled failure/restart cases. Show native training status, data counts and candidate metrics; do not label mere new-data volume as improved performance.

**Deliverable:** Automatic candidate training with measured activation, stable live inference and rollback.

## Task7 — Learned strategy experiments, after predictor/control validation

**Files:** extend `controller.py`, `experience.py`, `training.py`; add `tests/test_strategy_evaluation.py`.

**Interfaces:** versioned bounded tactic candidates consumed by the existing controller; evaluation compares actual outcomes under declared comparable conditions. Outcome model estimates are proposals, not counterfactual ground truth.

- [ ] Start with one controlled tactic parameter, such as entry direction or deployment-group timing, keeping other behavior/version fixed. Log alternatives considered, chosen action and genuinely known selection probability.
- [ ] Test that a strategy never receives a success label from an attack that did not use it; predictor improvement alone cannot mark a policy improved. Separate TH/army capability coverage and composition shifts from tactic effects.
- [ ] Compare actual held-out outcomes and practical costs under a declared evaluation design, then expand tactic/army coverage incrementally. Human demonstration/correction data may support imitation; self-generated guesses are not expert labels.
- [ ] Defer end-to-end RL and self-modifying application code. Revisit only after a validated environment/reward/data pipeline exists.

**Deliverable:** Evidence-based action-policy improvement; this stage is dependent on Tasks1–6, not achieved by installing a learning library.

## Order and safe parallel work

Task1 is the immediate blocker. Episode schema/storage tests (Task4) and offline fixture/evaluation work can proceed alongside it once their interfaces are fixed. Task2 then Task3 establish actual observations/control. Tasks4–6 add prediction learning; Task7 depends on reliable data and prospective evaluation. Keep code review at each completed task, plus the full suite before claiming completion. This document marks all work pending; the research/planning step changed no product code.
