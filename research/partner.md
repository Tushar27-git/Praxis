# Partner brief — 2026-10-27

Position: A narrow, experimentally validated farming adviser is plausible. A competitive policy of attacking only at a score of 98% or more and otherwise skipping has a mode-dependent constraint. Neither the 15-second target nor a calibrated 98% success rate is demonstrated.

## Claims and evidence

**PARTNER-1 — Supported.** Supercell's 6 October 2025 release split regular Battles from Ranked. Regular Battles unlock at TH2, allow unlimited attacks, and carry no risk of losing trophies; Ranked unlocks at TH7 and limits attacks. Choose the intended mode before assessing the product.

Excerpt: “Enjoy endless attacking, farm resources, enjoy Events, and practice strategies.”

- https://supercell.com/en/games/clashofclans/blog/release-notes/get-ready-for-ranked-update/
- https://support.supercell.com/clash-of-clans/en/articles/battle-vs-ranked-battle-whats-the-difference.html

**PARTNER-2 — Supported, with source inconsistency disclosed.** The 16 April 2026 announcement divides Legend into three tiers: III has 24 battles weekly; II has 30 weekly; I has eight daily within four-week tournaments. Players below global rank 10,000 demote from Legend I each week. The current support table retains these counts. Its general overview loosely suggests monthly tournaments for Legend; use the detailed announcement and table rather than generalizing that overview to III/II.

Excerpt: “Legend League is now split into three tiers.”

- https://supercell.com/en/games/clashofclans/blog/news/big-changes-are-coming-to-ranked-this-april/
- https://support.supercell.com/clash-of-clans/en/articles/ranked-leagues-4.html

**PARTNER-3 — Supported matching facts; current universal no-Next rule unverified.** Current support says ordinary Ranked matches attempt similar Town Hall levels, then use league placement. Legend I matches eight opponents daily, primarily according to trophy count. The official 17 June 2019 FAQ explicitly prohibits Next. That is historical evidence, not proof of every tier's 2026 UI. Contemporary unofficial guides report no Next, but direct current-client observation is needed before certifying it. The separate finish-current-battle clause does not establish pre-attack Next behavior.

Historical excerpt: “No. You can only attack the 8 Villages you are given each League Day.”

- https://support.supercell.com/clash-of-clans/en/articles/trophy-matchmaking-and-calculation-in-multiplayer-2.html
- https://support.supercell.com/clash-of-clans/en/articles/legend-league-matchmaking-3.html
- https://supercell.com/en/games/clashofclans/blog/news/faq-legend-league-redesign/

Inference: An unlimited easy-base search is a better conceptual fit for regular farming than limited competitive allowances. Whether that search is available in the intended current UI must be checked.

**PARTNER-4 — Supported narrowly.** Current support requires completion of the present Ranked battle before another begins. Leaving or closing a battle does not enable immediate matchmaking. This rules out rapid abandonment of active battles, without proving pre-attack skip rules or timer duration.

Excerpt: “You must finish your current Ranked Battle before starting a new one.”

- https://support.supercell.com/clash-of-clans/en/articles/ranked-leagues-4.html

**PARTNER-5 — Supported scoring facts; recommendation is inference.** Ranked gives three stars 40 trophies; two stars 16–32; one star 5–15; zero stars 0–4. Below Legend I the defender receives the unused portion of 40. Legend I exchanges trophies on attacks and defenses. Therefore expected 98% destruction, 98% probability of three stars, and an ordinary victory are different objectives.

Excerpt: “3⭐ Victory = 40 Trophies.”

- https://support.supercell.com/clash-of-clans/en/articles/trophy-matchmaking-and-calculation-in-multiplayer-2.html
- https://support.supercell.com/clash-of-clans/en/articles/legend-league-4.html

Inference: Competitive optimization should consider expected trophy yield across available attacks. For regular farming, loot per elapsed minute may be more useful than destruction.

**PARTNER-6 — Partially supported.** No current primary document found in this search establishes the assumed universal 30-second pre-attack timer. Treat it as an input assumption pending observation. Clan Wars permit scouting in the 23-hour preparation period. Friendly Challenges permit pre-attack scouting, take the army from the current training screen, and do not allow army editing when entered through Scout. They also support league battle modifiers and offer a practical manual evaluation environment.

Excerpt: “you can scout the base before attacking.”

- https://support.supercell.com/clash-of-clans/en/articles/friendly-challenges-3.html
- https://support.supercell.com/clash-of-clans/en/articles/about-clan-wars-2.html

**PARTNER-7 — Supported as announcement, not verified deployment.** On 8 October 2026, Supercell announced/documented a full UI rework, including army editing and Battle Log moving inside Battle. The article includes future-facing rollout wording; exact installation on the user's current device is unverified. It also documents possible device/language visual issues.

Excerpt: “Battle Log, Army editing, and the battle menu now live inside the Battle button.”

- https://supercell.com/en/games/clashofclans/blog/news/weve-revamped-the-clash-of-clans-user-interface/

Inference: Evaluate actual version, resolution, language, scenery, and zoom. An old tutorial does not establish current button locations.

## Decision, counterargument, and test

Recommendation: Choose mode and define success first: three stars, destruction at least 98%, ordinary victory, or loot target. Start with one Town Hall range, one fixed army, and a small strategy library. Pre-reading the player's army before matchmaking would reserve the opponent-view budget for the opponent. This is a proposed experiment, not demonstrated feasibility or a policy approval.

Time the entire pipeline from first usable opponent frame through perception, plan selection, confidence output, and readiness to execute. A model response under 15 seconds alone does not establish the system deadline.

Strongest counterargument: Selecting visibly weak regular-Battle bases and using a familiar robust attack may be useful without solving expert competitive planning. That supports a narrow experiment, not calibrated 98% success on unfamiliar bases.

Cheap falsifying test: Manually screen-record several entries in the intended mode. Record Next/exit availability, countdown duration, when the army becomes fixed, and whether rejection consumes an attack. Then time the planner on 20–30 frozen first-view recordings with army known beforehand. Missing complete plans within 15 seconds falsifies the latency target cheaply. Passing only justifies a larger held-out execution study.

Weakest load-bearing claim: Exact current skip/timer behavior, which needs direct client observation.

Cross-review: First Principles inspected the original sources; the source inconsistency and history/rollout boundaries above incorporate that review. The reviewer must resolve final status; this author does not self-certify it.
