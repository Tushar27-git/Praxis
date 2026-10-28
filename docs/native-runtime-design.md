# Native autonomous controller - corrected product contract

User clarification: 28 October 2026. This supersedes the offline web-workbench milestone as the product direction. FINAL_RESEARCH.md remains useful evidence, not authorization to substitute a manual product.

## Accepted requirements
- Native Python desktop application with a floating control panel/overlay. No browser-based product UI.
- Live game frames; no screenshot-upload or manual-annotation workflow as normal operation.
- One Start action should launch/attach to Clash, inspect the currently selected army automatically, enter Regular Battles, evaluate the opponent, and execute troop/spell/hero decisions.
- Observe the evolving battle and revise actions; loop until Stop. Recording is an optional diagnostic alongside the controller.
- Work while the user uses other apps. Do not move the Windows mouse or steal foreground focus.
- The emulator may stay running in a covered window. Minimized operation is not required.
- Read the actual selected army, rather than require one fixed predefined army. Unknown/unreadable states must remain explicit.
- Ten-second attack preparation is a target to measure, not a tested deadline or promise of perfect alignment/outcomes.
- Emulator use is accepted. BlueStacks and Clash are now installed; a new account's village was captured on 28 October 2026.

## Implementation decisions
Use an Android device connection for capture/input independent of desktop focus. First target BlueStacks5's documented ADB interface; verify actual game compatibility and frame delivery before treating it as supported. Do not infer consumer Google Play Games ADB access from Google's Developer Emulator.

Separate native UI, device transport, perception/state recognition, army recognition, candidate planning and feedback execution. Reuse validation ideas from the old prototype, not its untrained manual exposure score as a combat brain. The native app must report unavailable capabilities rather than offer a fake autonomous Start.

First real-device gate: attach to one explicit emulator serial; obtain fresh frames with the emulator covered; record dimensions/capture duration; validate coordinate transforms; confirm input is sent to that Android device without Windows mouse takeover. No physical-device or remote-network auto-discovery.

Next gates: recognize home/army/scouting/battle/results on the actual client; extract the selected inventory; establish legal deployment geometry; verify bounded action sequences and feedback on real frames. A published building detector alone does not provide army OCR, strategy, or a calibrated98% success estimate.

## Setup boundary
Google Play/Supercell authentication is performed by the user. Do not request passwords or OTPs. Do not bypass game compatibility, authentication, anti-cheat, or Windows security controls. Supercell's documented automation restrictions remain relevant; using an emulator does not grant an exemption.

## Sources checked
- https://support.bluestacks.com/hc/en-us/articles/23925869130381-How-to-enable-Android-Debug-Bridge-on-BlueStacks-5
- https://www.bluestacks.com/download.html
- https://developer.android.com/tools/adb
- https://developer.android.com/tools/releases/platform-tools
- https://developer.android.com/games/playgames/pg-emulator

## Current reality
The old browser/manual workbench is a rejected direction, not completion of this contract. No autonomous attack controller or trained current-army recognizer exists yet. BlueStacks ADB capture and deployment inputs were validated in one agent-guided diagnostic attack (20 level-one Barbarians, three stars/100%). Capture now transfers raw RGBA and encodes PNG on the PC. A temporary640x360 viewport produced328–453ms samples; the original1600x900 viewport was restored and remains too slow for the existing input freshness guard. See docs/live-device-check.md. Faster full-resolution capture and automatic perception remain unfinished.

## Live learning extension

User requested continuous low-latency local analysis and learning from predictions compared with actual battle results. Proposed design and reviewed evidence are in research/live-learning-design.md; ordered implementation tasks are in docs/superpowers/plans/2026-10-28-live-learning.md. Prediction learning and action-policy improvement are distinct. These components are not implemented by the research/planning step.
