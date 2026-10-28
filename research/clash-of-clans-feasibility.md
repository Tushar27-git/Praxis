# Clash of Clans visual attack system: feasibility and research design

Research date: 27 October 2026. Status: research only; no bot, emulator configuration, account access, or live attacks performed.

## Executive Summary

The proposed system can be decomposed into practical engineering components: read the player's army before matchmaking, capture an opponent's village, identify visible defenses and deployment space, generate candidate attack policies, estimate outcomes, and present or execute the selected policy. The research does not establish that these components together can achieve a calibrated 98% success rate across arbitrary bases, armies, Town Halls, and battle modes within fifteen seconds. Recognizing a base and predicting an entire battle are different problems. General visual-game-agent research supports investigating the approach, while game-specific reliability remains an empirical question. [17][21][22][26]

For the supplied Ryzen 5 4600H, GTX 1650 Ti, and 16 GB RAM laptop, the recommended first experiment uses saved screenshots and normal Google Play Games PC recordings, a small custom detector, structured attack templates, and a human executing the suggested plans. Google Play Games is an officially documented platform for Clash of Clans. Its consumer client should not be assumed to expose the ADB facilities documented for Google's separate Developer Emulator. No end-to-end latency benchmark was performed on this laptop. [9][10][11]

Two constraints change the original proposal. Supercell prohibits gameplay bots and has announced permanent bans for bot accounts. Separately, current regular Battles and Ranked Battles have different ranking and attack-allocation rules; unlimited rejection of opponents cannot be assumed to support competitive progression. The current precise skip behavior needs direct confirmation in each requested mode. [1][2][3][5][7]

The useful next deliverable would be an offline, TH13-first experiment that tests perception, plan quality, prediction calibration, and deadline performance separately. Expanding to every Town Hall is a later coverage and validation programme. A displayed score of 98% would remain a hypothesis until a frozen policy succeeds on independent, representative trials at useful acceptance coverage. [21][22][23][24]

## Introduction

The requested experience is a separate Start/Stop menu that initiates scouting, reads the opponent, assesses the available army, chooses troop quantities and clock directions, and automatically attacks or moves to another opponent. The user clarified that the player's own base, camp, army, and levels should be read before matchmaking. The current village is approximately Town Hall 13, and the eventual ambition includes every Town Hall and every match. The laptop has a Ryzen 5 4600H CPU, GTX 1650 Ti GPU, and 16 GB RAM; Google Play Games is preferred over an unfamiliar emulator. These are user-supplied facts, not independently inspected device specifications.

This assessment covers Home Village regular Battles, Ranked/Legend, Clan Wars, and Friendly Challenges. The proposed architecture records the mode explicitly. Builder Base and Clan Capital would require separate game-state definitions, policies, and evidence; this research does not establish compatibility for those systems. Likewise, the user's thirty-second scout window is treated as a requirement to verify, rather than a universal current rule. A fifteen-second decision deadline is a proposed engineering target, not a measured result.

The report distinguishes documented platform or game behavior from engineering proposals. All architecture, latency allocations, dataset sizes, and milestone gates below are recommendations unless explicitly attributed to a source. There is no permission claim for a live competitive adviser, and no recommendation to deploy unattended gameplay on a real account. Research on screenshots and controlled models can proceed without claiming that its eventual application is approved by Supercell. [1][2]

Five independent researchers examined game/product constraints, first-principles prediction, platform interfaces, empirical prior art, and domain policy. They ran in waves under the session's concurrency limit, then non-authors checked material source claims. The bibliography contains primary policies, official documentation, original papers, and explicitly labeled author repository claims. Detailed API schemas, actual device performance, and current per-mode scouting behavior remain evidence gaps.

## Main Analysis

### Finding 1: mode rules and policy constrain the original attack-or-skip loop

Regular matchmaking and competitive progression must be treated as different objectives. The October 2025 update separated regular Battles, intended for repeated attacking and resource collection, from limited Ranked Battles. Current support continues that distinction. Consequently, a farming system that rejects many opponents is not automatically a ranking system. This matters even if perception and attack planning are perfect: selecting an objective that the mode does not reward cannot produce the desired progression. [3][5]

The April 2026 announcement divided Legend League into three tiers. Legend III has twenty-four attacks per week, Legend II thirty per week, and Legend I eight per day. The announcement distinguishes weekly competition in III/II from the four-week structure in I. Some support-page overview wording generalizes across Legend tiers, so the more specific announcement and allocation table should guide interpretation rather than importing old Legend assumptions. [4][5]

The inspected current Ranked support explicitly requires finishing the present battle before starting another and says leaving or closing it does not permit immediate rematching. A historical 2019 official Legend FAQ explicitly prohibited exchanging its assigned opponents with Next. That historical rule is useful evidence of the design, but it is not sufficient to certify every 2026 Ranked tier's pre-attack controls. The report therefore does not promise unlimited Next in competitive play, or declare the exact present behavior verified. A small manual recording in the actual mode is the decisive next check. [5][7]

| Mode | Research objective | Proposed treatment of rejection |
|---|---|---|
| Regular Home Village Battles | Loot, practice, or destruction | Assess whether the current UI offers Next and its actual cost |
| Ranked, including Legend tiers | Expected trophies across available attacks | Optimize the assigned opportunity; do not assume replacement opponents |
| Clan Wars | Stars and destruction under war constraints | Plan against the chosen target and war state; verify remaining attacks |
| Friendly Challenges | Repeatable evaluation and learning | Use human-run experiments with documented conditions |
| Builder Base / Clan Capital | Different battle systems | Separate research and validation; no support claim here |

Current Ranked scoring gives three stars forty trophies and lower star outcomes a destruction-dependent award. That makes expected trophy yield a more relevant ranking target than a single destruction cutoff. A policy that produces slightly lower expected destruction but a safer star outcome could be preferable; that is an optimization implication, not an observed result from a tested bot. Friendly Challenges permit configurable conditions, which makes them useful for human-run comparison experiments, provided those conditions are logged rather than assumed equivalent to competitive matches. [6][27]

Policy is an independent constraint. Supercell's Terms list automation software and bots among prohibited categories, and its April 2024 CoC announcement describes permanent bans for identified bot accounts. Screen-only observation followed by mouse clicks still constitutes the gameplay automation described by those sources. Calling a project research does not create an account-use exemption. These documents establish game and account restrictions; this report does not characterize the proposed program as criminal. [1][2]

Offline screenshot studies and retrospective coaching remove the automated-control component, which makes them useful research starting points. They are not evidence that Supercell has approved a live competitive AI adviser. Likewise, officially supported Google Play Games gameplay does not authorize an adjacent bot. The research recommendation is to establish perception and planning value before deciding whether any live product has an acceptable deployment path. [1][9]

The original objective should therefore become two explicit research questions: can a system generate better attack policies from visible information, and can its intended operating mode legitimately support the proposed selection and execution workflow? Neither question is settled by a fast screenshot model. The first falsification step is deliberately simple: record scout timing, available controls, final army selection, and the effect of leaving in each mode, using ordinary manual gameplay.

### Finding 2: use Google Play Games for normal play and benchmark observation separately

Google Play Games PC is the recommended normal-play platform for this user because it matches the user's preference and Supercell expressly documents Clash of Clans on that platform. This recommendation is about a supported client and an economical research starting point. It does not establish that the client supplies a convenient automation API, nor that a bot would be approved. Third-party emulator compatibility was not tested, so choosing BlueStacks, LDPlayer, or another emulator merely to make input injection easier would add an unverified dependency. [9][1]

Google's documentation describes a separate Play Games Developer Emulator with installation/debugging facilities and an ADB connection. It explicitly distinguishes that environment from the consumer player client. The defensible conclusion is that consumer ADB availability must be tested rather than presumed. It would also be unsafe to infer that the Developer Emulator can run the user's retail CoC account merely because it accepts developer packages. No such compatibility experiment was performed. [10]

For observation on the supported consumer client, Windows.Graphics.Capture is a reasonable candidate. Microsoft documents acquiring frames from an application window or display, with support detection, selection, a frame pool, and a capture session. Those are the required capture primitives, but Microsoft's documentation is not a CoC-specific compatibility test. An initial measurement should check nonblank frames, timestamp freshness, resolution, DPI changes, window movement, and behavior during normal gameplay transitions. [11]

On an authorized Android research device or emulator that exposes debugging, ADB supplies screenshot primitives. scrcpy supplies mirroring and input control, subject to its documented prerequisites. Its advertised 35-70 ms mirroring latency does not include recognition, plan search, action delivery, or game response, and does not establish consumer Google Play Games compatibility. These are alternative interfaces to investigate after the offline model works, rather than evidence that a complete attack system meets the deadline. [12][13]

| Research component | Proposed first choice | Evidence boundary |
|---|---|---|
| Normal PC gameplay / recordings | Google Play Games PC | Official CoC support; user's actual installation not inspected |
| Reproducible perception evaluation | Saved frames and complete recordings | Avoids coupling model tests to live navigation |
| Live observation experiment | Windows window capture | General Windows capability; test actual GPG window |
| Android laboratory interface | ADB or scrcpy where legitimately available | No assumption of consumer GPG ADB access |
| Custom detector deployment | Small model exported to ONNX | Export supported; actual accuracy and latency unmeasured |
| Results storage | Local files and a small structured dataset | Design proposal; no cloud service required |

The public CoC API portal advertises clans, leaderboards, player/clan profiles, and leagues. The accessible material did not establish an interface for live opponent coordinates, hidden defenses, troop deployment, or battle simulation. The detailed official schema did not render reliably through the research tools, so this is an access-bounded finding, not an exhaustive endpoint audit. In particular, do not assume that a player's profile lists the army currently selected for the next battle. The proposed army inventory should be read and confirmed from the relevant game screen. [14]

For the supplied laptop, a small local vision model and bounded candidate search are the proportionate starting hypothesis. Ultralytics documents custom detection and ONNX export; ONNX Runtime provides profiling tools. These sources justify testing that deployment path, not claiming a particular frame rate on the GTX 1650 Ti. Run inference at batch one on real screenshots, compare CPU and an available compatible GPU backend, and measure memory while Google Play Games is also running. No new hardware purchase is justified by this desk research. [17][18][19]

A large vision-language model could help produce annotations, interpret unusual offline examples, or explain a structured plan. It should not be the sole unvalidated source of troop counts, pixel coordinates, or outcome percentages. The proposed runtime instead uses explicit state fields, checks, and bounded plan scoring. Cloud reasoning can be compared experimentally, but no cloud round-trip or model-generation time is assumed to fit the deadline. The simplest initial project is one local research pipeline, rather than a collection of services whose additional overhead has not yet earned its place.

### Finding 3: turn screen pixels into a versioned army inventory and spatial belief

The user's clarification improves the proposed pipeline: read the player's information before searching for an opponent. The inventory should record the selected army recipe, actual deployable troop counts and levels, spells, attacking heroes and their selected equipment, siege/support options where relevant, and any mode-specific modifiers or availability. These are proposed input fields; their exact screen locations and visibility must be established on the current client. Record the observation time and supporting image crop for each uncertain value. A saved profile of unlocked units must never be silently substituted for the force actually selected for this battle.

Analyzing the player's own village has a focused purpose here: find the current Town Hall/progression context and the screens needed to confirm the offensive inventory. The player's wall arrangement and defensive building placement do not, by themselves, describe the next offensive army. If a value is not visible from camps or the army screen, the research workflow should obtain a manual confirmation rather than infer a maximum level from Town Hall alone. This prevents the requested own-base analysis from becoming an unrelated base-building project.

Treat the inventory as a snapshot that expires when an army recipe, hero loadout, relevant availability, mode, or game version changes. Confirm the final selected army immediately before its use. In the proposed scheduling, own-state work occurs outside the opponent's short scouting deadline; the short window handles freshness checks and opponent-specific reasoning. This is a design improvement, not evidence that the resulting forecast will be correct.

For the opponent, identify visible building classes, level cues where actually distinguishable, wall segments and compartments, major approach constraints, and the visible deployment boundary. OpenCV template matching is a documented way to locate a familiar patch inside an image; it is a plausible baseline for stable UI symbols. A trained detector supplies boxes and class scores for more variable objects. Neither capability makes an off-the-shelf model knowledgeable about CoC buildings: custom annotated examples and game-specific evaluation are still required. [15][17]

Use a layered recognition experiment. First identify the screen and crop the battlefield separately from the troop bar and menu. Next normalize the view, detect strategically important objects, and reconcile overlapping or inconsistent detections across several nearby frames. Finally construct a compact spatial representation with observed values, confidence, and explicit unknowns. A useful error report distinguishes a missing Town Hall, a wrong defense class, an uncertain level, an unread troop count, and a camera-calibration failure. A single average detection score would hide these different planning risks.

Spatial reasoning should use ground footprints or tile anchors rather than uncalibrated sprite centers. OpenCV's homography documentation provides a mathematical mapping between planes, which can support a calibrated image-to-ground transformation. Applying that mapping to the game's ground plane is an engineering proposal; it does not prove that elevated artwork, scenery, or bounding-box centers locate building footprints correctly. Validate the mapping against manually marked landmarks and reject views with excessive error. [16]

Clock directions belong to the user-facing plan. Define twelve o'clock as screen-up, three as right, six as down, and nine as left, relative to a declared base center. Internally retain a legal deployment region, a point or short line within it, and a positional tolerance. A clock label alone is too coarse to distinguish a funneling troop, a main deployment line, and an inaccessible position. Recalculate the image mapping when zoom, pan, resolution, or window scale changes; do not carry stale pixel coordinates into another view.

The state must also represent information that scouting has not established. A historical Supercell release note explicitly discusses hidden Teslas and traps; it does not define complete visibility rules for every current mode. Current support documents defender activation and ordering, including random selection among equal-housing-space troops. Those facts justify investigating uncertainty and reaction policies, but do not quantify their impact on success. The next data collection must record exactly what can be inspected before each attack. [20][35]

Supporting all Town Halls expands both the visual label space and the combat-data coverage. A detector may recognize a building while the outcome model has no validated experience with that level, army, or modifier. The proposed support matrix therefore separates recognition coverage from planning coverage. An unfamiliar combination should produce an explicit unsupported-state result, rather than a confident number fabricated by a general model. Start near the user's TH13 context, then broaden the matrix only after held-out evidence supports each extension.

### Finding 4: a 98% number requires a plan, a defined outcome, and calibration

The interface should never display an unlabeled percentage. Expected destruction, probability of reaching ninety-eight percent destruction, probability of three stars, detector confidence, and statistical confidence in a tested success rate are distinct quantities. Let D be final destruction between zero and one. An average E[D] of 0.98 does not imply P(D >= 0.98) is 0.98. For example, an equally likely 97% or 99% result has expected destruction of 98%, but only a 50% chance of reaching the stated threshold. This is a mathematical counterexample, not a CoC measurement.

The outcome estimator must be conditioned on the proposed policy. The question is not simply whether an army is stronger than a village: it is how the specific army, selected approach, sequencing, reaction rules, and execution capability perform against the observed state in the relevant mode and version. The proposed estimate is P(success | observed base, confirmed army, policy, mode, version). Changing the plan changes the event being predicted. A useful output would include predicted destruction distribution, star probabilities, a mode-specific utility estimate, and whether the state lies within validated coverage.

Unknown information should be represented rather than filled with invented facts. Conceptually, average outcome predictions over plausible unobserved states and execution errors. This can be implemented only as well as the underlying data or simulator permits; assigning a distribution is not the same as validating it. Hidden information does not prove high reliability impossible: a robust attack against a weak enough opponent may succeed across many plausible states. The unresolved research question is how often that favorable situation can be recognized correctly, and whether important surprises arrive early enough for adaptation.

A weighted score based on army strength, defense density, entry geometry, and similar features is a useful baseline for ranking candidates. It should be labeled a heuristic score. It becomes an empirical probability only after fitting and validating an outcome model against appropriately collected results. Guo and colleagues demonstrated calibration failures in tested neural networks, while Ovadia and colleagues found limitations in uncertainty estimation under dataset shift. Neither paper evaluates CoC; together they support requiring calibration measurements rather than trusting a model's numerical confidence. [21][22]

For a learned model, evaluate mean absolute destruction error, star prediction, proper probability scores, and calibration in the high-score region. A model could appear reasonably calibrated overall while its claimed 98%-plus cases fail much more often. Changing the Town Hall distribution, army, balance version, or screenshot presentation should trigger renewed checks. Selecting the best-looking plan from many noisy predictions also creates selection bias: the whole candidate-generation, scoring, and acceptance policy must be frozen and evaluated together.

Selective prediction offers a formal way to abstain on difficult cases, trading coverage for lower error. Its research guarantees do not automatically carry over to a game controller, but the measurement distinction is essential. Report both the fraction of encountered opponents accepted and success among accepted opponents. A system that accepts one in a hundred bases and succeeds frequently has different value from one that handles most bases. If the mode cannot exchange opponents, abstention must not be presented as a free replacement opportunity. [23]

An exact statistical calculation illustrates the evidence needed for the strongest reading of 98%. Suppose the policy and acceptance rule are fixed in advance and the accepted test attacks are independent, representative Bernoulli trials. With n successes and no failures, the one-sided 95% exact-binomial lower confidence bound is L = 0.05^(1/n). Requiring L >= 0.98 gives n >= ceil(log(0.05)/log(0.98)) = 149. At 149 successes it is approximately 0.980095; at 100 successes it is only approximately 0.970487. This calculation was reproduced by the chair and a non-author reviewer, using NIST's exact-binomial framework. [24]

Those 149 attacks are a best-case validation requirement, not a training-set estimate or a guarantee about each individual base. Failures increase the required evidence. Repeated familiar layouts, tuning the threshold after seeing test outcomes, optional stopping, or a changing policy undermine the simple interpretation. At low acceptance coverage, far more than 149 scouting encounters may be needed to obtain 149 accepted trials. Calibration and utility must also be checked in addition to this binary success-rate bound.

Historical replays require similar care. Each replay shows one executed action sequence and its result. Alternative sequences require sufficient data support, explicit modeling assumptions, a validated model, or controlled comparisons. Conservative Q-Learning documents difficulties arising from distribution shift and actions outside logged-data support; it does not prove counterfactual learning impossible. The implication for this project is narrower: a library of successful attack videos cannot, by itself, certify that a newly generated sequence would have produced the same outcome. [25]

### Finding 5: bounded planning and feedback are a better research design than a fixed click script

The proposed system has two time scales. Before matchmaking, it confirms the selected mode, inventory, screen geometry, and supported model version. During scouting, it builds the opponent representation, generates a limited set of compatible policies, ranks them, and returns a decision by a measured deadline. During the attack, a separate short reaction loop updates observations and chooses the next allowed action. The fifteen-second target applies to the initial decision; it does not mean that all later decisions can be made correctly before combat begins.

```text
Pre-match army snapshot -----------+
                                  v
Frames -> screen recognition -> spatial state + explicit unknowns
                                  |
                                  v
                    compatible candidate policies
                                  |
                                  v
                 outcome estimates + support checks
                                  |
                                  v
                      mode-aware decision gate
                         /                 \
                advice / abstain      permitted test execution
                                            |
                                     observe and verify
                                            |
                                     update next action
```

Start with a small strategy library conditioned on the confirmed army, rather than asking an unrestricted text model to invent all actions. Generate variants over a limited set of entry sectors, deployment points or lines, resource allocations, and reaction rules. Prune candidates that exceed troop/spell counts, refer to unavailable abilities, use unsupported mechanics, or deploy outside the recognized legal region. Rank surviving candidates with an initially simple, transparent baseline; replace components only when experiments establish a benefit.

The first learned model could rank these candidate policies from demonstrations and outcomes. A stronger second stage could use a validated approximate simulator for limited lookahead over plausible hidden states. Full reinforcement learning is a later option if a suitable training environment and reward definition exist. None of these methods can evaluate every possible troop ordering, coordinate, and reaction sequence under the deadline. The proposed library deliberately trades breadth for testable behavior, with an explicit unsupported result for unfamiliar armies.

A plan must contain more than clock directions. Each action record should identify the troop, spell, hero, or ability; required quantity; legal deployment point/segment; earliest trigger; latest useful time; confirmation signal; and response to failed confirmation. For example, a research fixture could require a named inventory item to be deployed at a calibrated point in the ten-o'clock sector after the previous count change is verified. That describes the action format, not a recommended attack for the user's unspecified army. Timing and troop allocations must come from the actual candidate policy and its validation.

During execution, recognize whether the intended item is selected, whether its quantity changed as expected, whether a deployment occurred, and whether the scene still matches the plan. Trigger spells and abilities from observable conditions where reliable signals exist, with explicit timeouts. Avoid assuming that an issued input was accepted, and avoid blindly replaying an uncertain input: duplicate deployment may consume a scarce resource. Log recognition errors, rejected inputs, delayed actions, and tactical errors separately so that a failed attack can be diagnosed.

The runtime should stop issuing new actions when the screen state, coordinate mapping, or selected army becomes uncertain. A Stop control should cancel queued actions and release held input. It cannot promise to pause or undo a battle that the game has already started; the menu should make that state visible and hand control back promptly. A tactical abstention, a capture failure, and a user stop are different outcomes. They should not all be implemented as clicking Next, particularly when the mode's rejection semantics have not been verified.

The following allocation is an unmeasured design budget for a twelve-second primary path plus three seconds of reserve. It is not a benchmark or a claim that the supplied hardware meets it.

| Elapsed window | Proposed work | Budget |
|---|---|---|
| 0-0.5 seconds | Acquire a fresh usable frame and establish screen state | 0.5 s |
| 0.5-4 seconds | Opponent detection; parallel army-freshness checks | 3.5 s |
| 4-5 seconds | Spatial features and uncertainty flags | 1 s |
| 5-9 seconds | Generate, prune, and score bounded policy candidates | 4 s |
| 9-11 seconds | Support/calibration checks and mode-aware selection | 2 s |
| 11-12 seconds | Confirm view, output plan, prepare next step | 1 s |
| 12-15 seconds | Recovery and deadline reserve | 3 s |

Benchmark the end-to-end wall-clock interval from the first usable opponent frame, including preprocessing, queueing, data transfer, and final validation. Record median, p95, worst observed duration, deadline misses, and frame age while the client is running. Warm and cold starts should be measured separately; model loading belongs in preflight wherever possible. ONNX Runtime profiling can help locate inference bottlenecks, but it measures only part of this complete path. [19]

The proposed menu can remain small: platform/window selection, verified mode, confirmed army snapshot, Start, Stop, current phase, and the latest plan with labeled estimates and support status. It should show whether rejection is available, the observed remaining scout time, and any reason the analysis cannot support a decision. Begin the research UI in observation/advice mode; an execution toggle would require a separate deployment decision because of the documented bot restrictions. No menu or runtime was implemented in this research session. [1][2]

Finally, make screen-state handling version-specific. Supercell announced an extensive UI rework on 8 October 2026, including changes around the Battle button, army editing, and battle log. The announcement alone does not prove exactly when every client received it. Detect the actual interface and validate its anchors instead of importing coordinates from an older guide. This is a concrete reason to preserve screenshots, client/version metadata, and regression examples as the research expands. [8]

### Finding 6: prior art supports experimentation, while data and simulator fidelity remain the bottlenecks

Strong game-playing AI is real evidence in favor of the idea's broad direction. AlphaStar reached Grandmaster-level StarCraft II performance; DeepMind reported that it ranked above 99.8% of active players. That figure is a ranking percentile, not a 99.8% match win rate. The final reported agent had a camera interface and professionally reviewed action restrictions, so it should not be dismissed as an unconstrained omniscient player. Its training programme is nevertheless evidence about StarCraft II, not a ready-made CoC planner or a forecast for this laptop. [26][29]

Video PreTraining demonstrates that video can contribute to learning actions, but its reported denominators matter. The VPT paper used about seventy thousand hours of video and describes roughly 1.3 million ten-minute reinforcement-learning episodes in its fine-tuning experiment. The reported 2.5% diamond-pickaxe completion belongs to a specific model and evaluation condition, not to every task VPT attempted. This supports investigating imitation from recordings while cautioning against equating an impressive demonstration with highly reliable completion. Those training quantities are not estimates of what this project would require. [30]

SIMA is particularly relevant to the screen-to-action architecture: its original work used visual observations and keyboard/mouse actions across virtual environments. The initial skill evaluations emphasized tasks around ten seconds long. The later SIMA 2 report describes improved reasoning and generalization while retaining limitations around long-horizon tasks, memory, precise actions, and robust visual understanding. Preserve both sides of this evidence: visual agents are improving, and none of these inspected reports validates the combined CoC outcome, deadline, and coverage requested here. [31][32]

Game-specific repositories establish a narrower kind of precedent. The inspected COC_AUTOFARM README describes resource-based target filtering, Air Defense detection, spell use, and randomized troop placement. Another repository documents image matching and behavior trees for village management and attacks. These are original authors' descriptions, not independently measured capability results; neither inspected README supplies a held-out evaluation of calibrated ninety-eight-percent attack prediction. No repository was installed or run. A farming loop demonstrates useful component ideas while addressing a different success criterion from reliable competitive planning. [28][34]

A public CoC-AI simulator also requires scrutiny before reuse. Its inspected source calculates a variable called percent from modeled hit-point reduction. That warrants checking the reward definition and simulator mechanics before interpreting its percentages or stars as faithful modern CoC labels. It is not a complete fidelity audit, and the visible formula alone does not establish every disagreement with official scoring. The general experimental lesson is to compare modeled outcomes against real, manually observed outcomes before allowing simulated lookahead to drive a confidence claim. [33]

The proposed dataset should link the complete pre-match inventory, first opponent observations, mode/modifiers, version, chosen plan, timestamped actions, important battle frames, final destruction/stars, and execution deviations. Include failures and rejected candidates. Human annotations should mark visible versus unknown facts and preserve uncertain labels. Split by battle and layout family where feasible, and hold out later collection periods. Randomly separating nearby video frames would not provide an independent test of performance on unseen villages.

The first useful test is a perception audit on approximately twenty to thirty diverse, saved scouting observations, with manually checked army snapshots. This is a proposed small diagnostic set, not a claim that thirty images train a sufficient detector. Determine which input fields are readable, which require additional views, and whether a complete structured state and candidate plan can be returned under the deadline. Compare a simple template/heuristic baseline with any learned alternative before expanding the engineering effort.

If that succeeds, run a human-executed planning comparison on approximately fifty held-out layouts and one hundred paired attacks under comparable challenge conditions. Counterbalance plan order and record differences in execution and available information. This proposed study can detect obvious planning weaknesses and help separate perception from tactics; it cannot by itself establish universal ninety-eight-percent reliability. Freeze the final policy and acceptance threshold, then perform the separate representative reliability evaluation described in Finding 4.

Only expand after those gates. Add new armies, Town Hall ranges, modes, and update versions as explicit evaluation strata, reporting where evidence is thin. A pooled success rate dominated by easy opponents should not be marketed as support for every difficult configuration. The strongest counterargument to a broad negative conclusion is that a narrow system may be useful quickly against favorable, familiar situations. The strongest counterargument to a broad positive conclusion is that finding and validating a useful favorable subset remains unmeasured. This research found no validated system satisfying the combined general CoC, ninety-eight-percent, and fifteen-second requirements in the sources checked; it does not prove none exists or that the problem is impossible.

## Synthesis & Insights

The user's proposed pre-match inventory stage is the right separation of work for the research. It removes avoidable own-army discovery from the scouting deadline while retaining a freshness check. The main unresolved work is then concentrated where it belongs: opponent-state reconstruction, policy-conditioned prediction, and execution feedback. More precise clicks do not repair a wrong outcome model, and a better model does not repair an unverified mode assumption.

The recommended research hypothesis is narrower than the eventual product ambition: within a documented Town Hall/army/mode subset, can a structured planner improve human-executed results over a simple baseline and return useful, calibrated estimates under a measured deadline? A favorable result would justify expansion. It would not establish every-match support, and it would not remove the separately documented constraints on live gameplay automation. [1][2]

## Counterevidence Register

| Favorable evidence | What it establishes | What it leaves open |
|---|---|---|
| Official Google Play Games PC support | A supported normal-play client [9] | Capture reliability and any automation permission |
| Detection, ONNX export, and Windows capture primitives | Components can be investigated with existing tools [11][17][18] | Game-specific recognition and end-to-end performance |
| AlphaStar, VPT, SIMA and SIMA 2 | Learned strategic or visual control is a credible research direction [29][30][31][32] | The requested CoC accuracy, hardware, and deadline |
| Public CoC automation repositories | Authors have assembled relevant perception/control components [28][34] | Reproducible ninety-eight-percent forecasting |
| Selective prediction | Rejection can trade coverage for lower error under stated assumptions [23] | Useful acceptance rate and whether a mode permits replacement |

The most favorable plausible outcome is a narrow planner that reliably identifies favorable situations and improves execution consistency. The weakest load-bearing assumption remains that visible information and available outcome data are sufficient to rank competing policies accurately on unseen bases. No measured result from this project currently supports that assumption.

## Claims-Evidence Table

| Claim | Type and review outcome | Remaining limitation |
|---|---|---|
| Gameplay bots are prohibited; bans announced | Official policy; non-author checked [1][2] | No enforcement-probability estimate or live-adviser exemption |
| Regular and Ranked differ materially | Official release/support; non-author checked [3][4][5] | Current per-tier Next and scout timer need direct observation |
| Consumer GPG and Developer Emulator differ | Official Google documentation; non-author checked [10] | Consumer ADB/capture behavior on this PC untested |
| Confidence and coverage require validation | Original research; non-author checked [21][22][23] | No CoC calibration dataset or fitted estimator exists |
| 149/149 is minimum best-case one-sided bound example | Mathematical calculation; independently recomputed [24] | Fixed representative independent accepted trials required |
| Fifteen-second full pipeline on supplied hardware | Engineering target, unverified | No benchmark or implementation exists |
| Every Town Hall and every mode | Product ambition, unverified | Separate coverage, rules, and evaluation needed |

The machine-readable claim ledger records source IDs, authors, reviewers, and support status. Source checks validate what documentation says; they do not validate the proposed product's performance.

## Limitations & Caveats

There was no local inspection of the installed game, hardware configuration, client version, army, or actual Town Hall. No training data was acquired, model trained, battle simulated, input injected, or end-to-end benchmark performed. Proposed study sizes and timing allocations are experimental designs. They should not be read as training sufficiency estimates, project schedules, or measured performance.

Some official support articles exposed their text through indexed search or an equivalent official support path rather than direct page extraction. The API's dynamic documentation did not expose a complete schema. Current scout timing, target replacement, and exact hidden-state visibility were not verified for every mode. Historical official sources are explicitly labeled as historical. These retrieval gaps are preserved rather than filled with unsupported certainty.

Research papers from other games supply methodological evidence, not transferable CoC success rates. The source search was focused rather than exhaustive, and public repositories were inspected as documentation or limited source examples without execution. All five researchers used the same available model family and browsing environment, so distinct agents do not remove shared-model or source-index biases.

## Recommendations

Use Google Play Games for normal supported gameplay and the first recording experiments. For this laptop, benchmark a small local detector and bounded planner on saved observations before choosing a live capture/control backend. Keep the own-army snapshot before matchmaking and log every relevant change. Treat all Town Halls and all modes as expansion goals, with a visible support matrix.

Define success before choosing the 98% rule. If it means destruction, validate the event of reaching that destruction threshold. If it means three-star reliability, train and evaluate that endpoint. For Ranked progression, evaluate expected trophies over actual opportunities, and confirm rejection semantics manually. Do not manufacture a probability by renaming a weighted heuristic score.

The first concrete experiment is twenty to thirty manually annotated scouting cases from the actual client, followed by human-executed plan comparisons if perception and timing pass. Investigate outcome calibration before autonomous execution. The original unattended bot remains technically unvalidated and contrary to the cited bot policy; a research prototype should not be described as ready for deployment. No implementation is authorized or required by the present research request. [1][2]

## Methodology Appendix

The deep-research workflow comprised scope definition, focused retrieval, evidence persistence, independent cross-review, outline refinement, synthesis, critique, and artifact validation. User clarification updated the hardware assumptions and moved army inspection before matchmaking. The outline was revised to put mode and policy constraints first after the evidence exposed problems with unlimited target selection.

Five distinct initial researchers participated: Partner, First Principles, Film Room, Empiricist, and Insider. At most three ran alongside the chair. Initial investigations were isolated; the second wave did not receive the first wave's findings. The cross-review ring was First Principles -> Partner, Film Room -> First Principles, Empiricist -> Film Room, Insider -> Empiricist, and Partner -> Insider. Reviewers reopened primary sources or recomputed calculations. The chair authored the synthesis and proposed architecture, without claiming independent validation for its unmeasured designs.

Material corrections included narrowing current no-Next assertions to historical/directly supported facts, preserving uncertainty about the October UI rollout, distinguishing API access limitations from endpoint absence, and narrowing replay counterfactual claims. AlphaStar's final camera restrictions and favorable evidence were retained; VPT's 2.5% result was kept tied to its specific task and model. Authors accepted the corrections, and non-author reviewers resolved the material disputes. Remaining uncertainty concerns evidence gaps and experimental performance, not a manufactured vote or consensus guarantee.

The source registry and evidence store preserve canonical IDs and short locators. The claim ledger distinguishes supported documentation, qualified inference, historical evidence, and unverified targets. Search coverage included official Supercell rules and release notes, Google/Microsoft platform documentation, vision/runtime documentation, calibration/selective-prediction literature, original visual-agent work, and illustrative CoC repositories. No paid research service, account interaction, or software installation was used.

The requested research is complete. The proposed follow-on experiments are optional future work, not work silently begun in this session.

## Bibliography

[1] Supercell (n.d.). "Terms of Service". official policy; current. [Original source](https://supercell.com/en/terms-of-service/) (Retrieved: 2026-10-27).

[2] Supercell (2024). "Update to our Fair Play Policy and Next Steps". official announcement; 2024-04-30. [Original source](https://supercell.com/en/games/clashofclans/blog/misc/update-to-our-fair-play-policy-and-next-steps/) (Retrieved: 2026-10-27).

[3] Supercell (2025). "Get Ready for Ranked Update!". official release notes; 2025-10-06. [Original source](https://supercell.com/en/games/clashofclans/blog/release-notes/get-ready-for-ranked-update/) (Retrieved: 2026-10-27).

[4] Supercell (2026). "Big Changes Are Coming to Ranked This April". official announcement; 2026-04-16. [Original source](https://supercell.com/en/games/clashofclans/blog/news/big-changes-are-coming-to-ranked-this-april/) (Retrieved: 2026-10-27).

[5] Supercell Support (n.d.). "Ranked Leagues". official support; current. [Original source](https://support.supercell.com/clash-of-clans/en/articles/ranked-leagues-4.html) (Retrieved: 2026-10-27).

[6] Supercell Support (n.d.). "Trophy Matchmaking and Calculation in Multiplayer". official support; current. [Original source](https://support.supercell.com/clash-of-clans/en/articles/trophy-matchmaking-and-calculation-in-multiplayer-2.html) (Retrieved: 2026-10-27).

[7] Supercell (2019). "FAQ: Legend League Redesign". historical official FAQ; 2019-06-17. [Original source](https://supercell.com/en/games/clashofclans/blog/news/faq-legend-league-redesign/) (Retrieved: 2026-10-27).

[8] Supercell (2026). "We've Revamped the Clash of Clans User Interface". official announcement; 2026-10-08. [Original source](https://supercell.com/en/games/clashofclans/blog/news/weve-revamped-the-clash-of-clans-user-interface/) (Retrieved: 2026-10-27).

[9] Supercell Support (n.d.). "Clash of Clans & Clash Royale Now on PC with Google Play Games". official support; current. [Original source](https://support.supercell.com/clash-of-clans/en/articles/clash-of-clans-clash-royale-now-on-pc-with-google-play-games.html) (Retrieved: 2026-10-27).

[10] Google Android Developers (n.d.). "Google Play Games on PC Developer Emulator". official technical documentation; current. [Original source](https://developer.android.com/games/playgames/pg-emulator) (Retrieved: 2026-10-27).

[11] Microsoft Learn (n.d.). "Screen capture". official technical documentation; current. [Original source](https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture) (Retrieved: 2026-10-27).

[12] Google Android Developers (n.d.). "Android Debug Bridge (adb)". official technical documentation; current. [Original source](https://developer.android.com/tools/adb) (Retrieved: 2026-10-27).

[13] Genymobile (n.d.). "scrcpy". original project documentation; current. [Original source](https://github.com/Genymobile/scrcpy) (Retrieved: 2026-10-27).

[14] Supercell (n.d.). "Clash of Clans API". official API portal; current. [Original source](https://developer.clashofclans.com/) (Retrieved: 2026-10-27).

[15] OpenCV (n.d.). "Template Matching". official technical documentation; 4.13.0 at retrieval. [Original source](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html) (Retrieved: 2026-10-27).

[16] OpenCV (n.d.). "Basic concepts of the homography explained with code". official technical documentation; 4.13.0 at retrieval. [Original source](https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html) (Retrieved: 2026-10-27).

[17] Ultralytics (n.d.). "Object Detection with Ultralytics YOLO". official technical documentation; current. [Original source](https://docs.ultralytics.com/tasks/detect/) (Retrieved: 2026-10-27).

[18] Ultralytics (n.d.). "Model Export with Ultralytics YOLO". official technical documentation; current. [Original source](https://docs.ultralytics.com/modes/export/) (Retrieved: 2026-10-27).

[19] ONNX Runtime (n.d.). "Profiling tools". official technical documentation; current. [Original source](https://onnxruntime.ai/docs/performance/tune-performance/profiling-tools.html) (Retrieved: 2026-10-27).

[20] Supercell Support (n.d.). "Clan Castle Troops & Spells". official support; current. [Original source](https://support.supercell.com/clash-of-clans/en/articles/clan-castle-troops-and-spells-2.html) (Retrieved: 2026-10-27).

[21] Guo et al. (2017). "On Calibration of Modern Neural Networks". original research; 2017. [Original source](https://proceedings.mlr.press/v70/guo17a.html) (Retrieved: 2026-10-27).

[22] Ovadia et al. (2019). "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift". original research; 2019. [Original source](https://proceedings.neurips.cc/paper_files/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html) (Retrieved: 2026-10-27).

[23] Geifman and El-Yaniv (2017). "Selective Classification for Deep Neural Networks". original research; 2017. [Original source](https://proceedings.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html) (Retrieved: 2026-10-27).

[24] NIST (n.d.). "Exact Binomial Confidence Limits". official statistical reference; current. [Original source](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm) (Retrieved: 2026-10-27).

[25] Kumar et al. (2020). "Conservative Q-Learning for Offline Reinforcement Learning". original research; 2020. [Original source](https://proceedings.neurips.cc/paper/2020/file/0d2b2061826a5df3221116a5085a6052-Paper.pdf) (Retrieved: 2026-10-27).

[26] DeepMind (2019). "AlphaStar: Mastering the real-time strategy game StarCraft II". original research announcement; 2019. [Original source](https://deepmind.google/blog/alphastar-mastering-the-real-time-strategy-game-starcraft-ii/) (Retrieved: 2026-10-27).

[27] Supercell Support (n.d.). "Friendly Challenges". official support; current. [Original source](https://support.supercell.com/clash-of-clans/en/articles/friendly-challenges-3.html) (Retrieved: 2026-10-27).

[28] ramsayab (n.d.). "COC_AUTOFARM". original repository claims only; current. [Original source](https://github.com/ramsayab/COC_AUTOFARM) (Retrieved: 2026-10-27).

[29] DeepMind (2019). "AlphaStar: Grandmaster level in StarCraft II using multi-agent reinforcement learning". original research announcement; 2019-10-30. [Original source](https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/) (Retrieved: 2026-10-27).

[30] Baker et al., OpenAI (2022). "Video PreTraining (VPT): Learning to Act by Watching Unlabeled Online Videos". original research paper; 2022. [Original source](https://cdn.openai.com/vpt/Paper.pdf) (Retrieved: 2026-10-27).

[31] DeepMind (2024). "SIMA: Generalist AI agent for 3D virtual environments". original research announcement; 2024-03-13. [Original source](https://deepmind.google/blog/sima-generalist-ai-agent-for-3d-virtual-environments/) (Retrieved: 2026-10-27).

[32] DeepMind (2025). "SIMA 2: An agent that plays, reasons, and learns with you in virtual 3D worlds". original research announcement; 2025-11-13. [Original source](https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/) (Retrieved: 2026-10-27).

[33] Royz2123 (n.d.). "Clash-of-Clans-AI simulator.py". original source code; undated repository snapshot. [Original source](https://github.com/Royz2123/Clash-of-Clans-AI/blob/master/simulator.py) (Retrieved: 2026-10-27).

[34] jatizon (n.d.). "Clash of Clans Bot". original repository claims only; undated repository snapshot. [Original source](https://github.com/jatizon/clash-of-clans-bot) (Retrieved: 2026-10-27).

[35] Supercell (2020). "The Spring Update Is Here". historical official release notes; 2020-03-30. [Original source](https://supercell.com/en/games/clashofclans/blog/news/the-spring-update-is-here-2/) (Retrieved: 2026-10-27).
