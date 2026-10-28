# Live analysis and learning design

Date: 2026-10-28. Scope: focused implementation research for the existing native Python app, BlueStacks, Ryzen5 4600H/GTX1650Ti/16GB RAM. This is a proposed design, not implemented capability or a new performance measurement.

## Decision

Replace the screenshot/model/tool conversation loop with a resident local controller: persistent Android video → continuous decoder → newest decoded frame → local perception → state machine/planner → device inputs. Keep learning and recording off the latency-critical path. Start by learning to predict final destruction; improving the action policy is a separate subsequent step.

More data can help only if it adds useful, correctly labeled experience. Wrong labels, repeated nearly identical frames, changing armies and selection bias can worsen the model. Google recommends a simple first model, reliable serving/training pipelines and monitoring feedback loops; it does not establish that this game's bot will improve automatically. [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml)

## Why the current test was slow

Local evidence is in [live-device-check.md](../docs/live-device-check.md): original screenshot generation/transfer took seconds, and every agent observation/action required another tool/model round trip. Raw low-resolution capture improved transport, but the restored1600x900 capture remained2734ms. `device.capture()` also encodes PNG synchronously, and native recording writes files in the capture worker. Those operations should not delay future inference.

The one guided100% battle is evidence of basic input alignment, not a training corpus. We did not save a complete timestamped action/observation episode; do not reconstruct its missing timings or count it as verified training data.

## Live runtime

**Preferred capture candidate:** a pinned scrcpy server with a Python video client/decoder. It documents separate video/control sockets, standalone custom clients and Android input injection. Its internal protocol is version dependent; pin server/client together. Initially retain the proven ADB input backend so capture and input changes are tested separately. [scrcpy developer documentation](https://github.com/Genymobile/scrcpy/blob/master/doc/develop.md)

Preserve source PTS plus host receive/decode timestamps. PTS comes from the encoder; it is not automatically an exact capture timestamp or a host-clock timestamp. Do not set source acquisition time to decode completion and then claim the frame is fresh. Establish a conservative freshness bound through clock-domain investigation and an instrumented visual response test before enabling actions. [Streamer source](https://github.com/Genymobile/scrcpy/blob/master/server/src/main/java/com/genymobile/scrcpy/device/Streamer.java)

Continuously drain/decode packets and replace one pending **decoded** frame. Do not accumulate a frame backlog; do not arbitrarily throw away compressed dependency packets to achieve latest-only processing. scrcpy's own pending buffer replaces decoded frames. [Frame buffer implementation](https://github.com/Genymobile/scrcpy/blob/master/app/src/frame_buffer.c)

`screenrecord` plus a decoder is a smaller fallback experiment, but first bytes after1078ms do not measure steady-state age. PyAV can parse/decode streams, and its documentation warns that FRAME/AUTO threading adds decode delay. No package, decoder or scrcpy server was installed by this research. [PyAV decoding](https://pyav.org/docs/stable/cookbook/basics.html)

Use two observation rates: read/cache army and static opponent layout during preparation; update timer, remaining troops, damage, hero/spell state and relevant battlefield regions during combat. The local controller reacts to those observations. Chat explanations are optional asynchronous summaries, never prerequisites for troop deployment.

Prototype templates and cropped digits with existing PIL/NumPy, then add trained models for demonstrated gaps. ONNX Runtime supplies CPU/CUDA inference, not a trained Clash recognizer. Benchmark CPU first; pin/test an exact GPU wheel/driver/CUDA/cuDNN combination before enabling GPU acceleration. Official installation/CUDA pages currently disagree on the generic newest CUDA default, so an unpinned `latest` command is inappropriate. [ORT Python API](https://onnxruntime.ai/docs/api/python/api_summary.html), [CUDA requirements](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)

Cropped text recognition is a candidate for count/timer/result fields; accuracy on game fonts and effects remains unverified. OCR confidence is a signal to validate, not proof. Unknown fields remain unknown. [PaddleOCR recognition](https://www.paddleocr.ai/main/en/version3.x/module_usage/text_recognition.html)

**Proposed engineering targets, not promises:** benchmark960x540 at15 decoded frames/second for60seconds; p95 decode-to-observation ≤100ms and observation-to-input-submission ≤100ms. Separately measure an on-screen event through visible action effect; initial target p95≤300ms on a controlled diagnostic. Report missed frames, buffering, resource use and source-age uncertainty. Initial policy evaluation rate5Hz, with faster ROI checks where measured need justifies them. Keep the existing750ms stale-action limit; unknown or unbounded freshness blocks actions. Preparation target remains10seconds. If these fail, report failure and adjust architecture rather than fabricate FPS.

## Learning loop

1. Before committing an attack, persist the exact army/base observations, planned entry/deployment, controller version, feature schema, model version, prediction time and predicted final destruction in0–100 units. Include missingness/confidence; do not treat an unseen defence as absent.
2. Record the selected strategy, actual actions/coordinates/durations, relevant observations and source frame IDs. Record skips and reasons, but an unplayed base has **no** observed destruction label.
3. At completion, extract stars/destruction, result evidence and validation status. Re-read consistent result frames and apply range/consistency checks. Contradictory, incomplete or uncertain results are quarantined, not silently converted into training labels. Initial result extraction must be validated against an independently labeled replay set.
4. Join prediction and result by battle ID; calculate error. Only then may that labeled battle enter a future training partition. Never substitute the model's prediction for the actual label. A second model agreeing with the first is not independent ground truth.
5. Retrain a candidate while idle. Freeze the deployed model for an entire battle. The first model predicts expected destruction from structured prebattle state **and the specified plan/controller**, not a universal army-versus-base score.
6. Compare candidate, incumbent and a historical-mean baseline on the same held-out later battles. Preserve a subsequent prospective confirmation window. Promote only through the declared evaluation policy; otherwise retain the incumbent and keep collecting data. Retain the previous artifact for rollback.

River directly supports predict → score → learn with delayed labels. Incremental training is optional: reproducible periodic batch training is the initial choice. A small scikit-learn regression model can be trained offline and exported as numeric parameters for lightweight local inference. Neither package is currently installed. [River delayed evaluation](https://riverml.xyz/latest/api/evaluate/progressive-val-score/), [scikit-learn persistence](https://scikit-learn.org/stable/model_persistence.html)

Evaluate destruction error in percentage points. If a later model predicts three-star probability, add Brier score and reliability bins with sample counts; lower Brier alone does not establish better calibration. Expected98% destruction and98% probability of three stars are separate outputs. Neither gets a trusted98% attack gate from this one demonstration. [Evaluation metrics](https://scikit-learn.org/stable/modules/model_evaluation.html), [calibration](https://scikit-learn.org/stable/modules/calibration.html)

Split whole battles, not frames; isolate duplicate bases when measuring unseen-base generalization, and train on earlier data before testing later data. Fit preprocessing only on training data. Report counts/errors by TH matchup and army family. A TH2 model must abstain on unvalidated TH13 situations. [Leakage](https://scikit-learn.org/stable/common_pitfalls.html), [group/time evaluation](https://scikit-learn.org/stable/modules/cross_validation.html)

Chosen actions supply observed rewards; unchosen strategies do not. Record action-selection probabilities only if actually known. Better outcome forecasts do not automatically create better tactics. Start control with explicit verified rules, then compare bounded parameter/strategy changes; demonstrations can later bootstrap action learning. End-to-end reinforcement learning is deferred because no simulator, representative corpus or reward pipeline exists here. [Bandit feedback](https://vowpalwabbit.org/docs/vowpal_wabbit/python/latest/tutorials/python_Contextual_bandits_and_Vowpal_Wabbit.html), [RL limitations](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html)

## Scope and defaults

- Native Python floating controls remain the product. Start/Stop, current-army extraction, Regular Battles and background Android input remain requirements.
- Local data and models; no cloud training or per-frame API calls. No new game actions, installations or training occurred in this research step.
- Store episode metadata/events in SQLite (standard library); retain diagnostic keyframes/optional video separately. Do not save/encode a PNG for every live inference frame. Unknown fields do not create fake labels.
- First predictor is expected-destruction regression, initially in shadow mode. Automatic training is allowed by the design; a trained candidate does not automatically become the active controller.
- Learning updates model parameters and experience, not application source code. Training runs while idle and yields immediately before gameplay resumes.
- Initial implementation validation uses the observed TH2/Barbarian account; this is a test slice, not a permanent fixed-army requirement. Broader recognition/control must be added and independently validated; unsupported armies pause explicitly.
- No numerical sample count in this research proves adequate training or98% reliability. Promotion evidence requirements are specified conservatively in the implementation plan and remain operational defaults, not statistical guarantees.

## Council evidence check

Five independent participants completed bounded briefs; non-authors inspected the load-bearing sources. Claim statuses below distinguish documented mechanisms from project recommendations.

| Claim | Author → reviewer | Status |
|---|---|---|
| Simple models/serving logs/feedback-loop caution | Partner → First Principles | Supported generally; exact battle pipeline is a proposal. |
| Persistent scrcpy/custom clients/version coupling | First Principles → Film Room | Supported mechanism; BlueStacks latency unverified. |
| PTS is encoder metadata, not host capture time | First Principles → Film Room | Supported; absolute freshness unresolved. |
| Latest pending decoded frame | First Principles → Film Room | Supported; compressed packet-drop warning is codec reasoning. |
| ORT inference/explicit GPU compatibility | Film Room → Empiricist | Supported; no game recognizer or hardware benchmark supplied. |
| Cropped OCR module | Film Room → Empiricist | Supported route; game accuracy unverified. |
| Group/time splits and leakage | Empiricist → Insider | Supported principles; combined game split is a proposal. |
| Brier is not pure calibration | Empiricist → Insider | Supported. |
| Chosen-action feedback lacks unchosen outcomes | Empiricist → Insider | Supported. |
| Delayed evaluation/incremental learning | Insider → Partner | Supported mechanics, not guaranteed improvement. |
| Versioned model metadata | Insider → Partner | Supported persistence guidance; promotion design is a proposal. |
| RL can be sample inefficient | Insider → Partner | Supported generally; no Clash sample requirement established. |

Strongest alternative: a simpler persistent screenrecord decoder may be enough and avoids a custom scrcpy protocol client. Benchmark it as fallback before accepting protocol maintenance. Weakest link: reliable, timely battlefield/army/result observations; fast video alone cannot create strategic understanding. More data will not repair systematically wrong labels.
