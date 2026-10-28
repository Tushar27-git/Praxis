# Native runtime rebuild plan and frontier

**Authority:** docs/native-runtime-design.md, reflecting the user's explicit correction and answers. The manual web workbench is rejected as the product direction.

## Completed connection work
- [x] Native Python/Tk panel as default entrypoint; float/compact controls; no browser launch.
- [x] Official Android Platform Tools staged locally, ADB37.0.1-15733141; emulator-only serial targeting.
- [x] Background Android-frame transport, coordinate conversion, package/freshness/cancellation checks for future device input.
- [x] Native live preview and optional lossless frame/CSV recordings with transition-frame rejection.
- [x] Native/transport/recording tests, existing regressions and Windows PowerShell5.1 fallback check.

## Required next real-device gate
- [x] User installed BlueStacks and Clash; local ADB connected at 127.0.0.1:5555 and captured the actual home village.
- [ ] Receive real frames while the emulator is covered by another app; measure actual age/FPS/latency and verify viewport alignment.
- [x] Validate the actual game package and Android input behavior: agent-guided Battle/Army controls, northeast deployment holds and Return Home succeeded without Windows mouse commands. Full-resolution freshness remains unresolved.

## Autonomous behavior still unfinished
- [ ] Recognize home/army/search/scout/battle/result states from current live frames.
- [ ] Read the currently selected army and available heroes/spells/equipment automatically.
- [ ] Generate and validate game-specific strategy, deployment geometry and action feedback.
- [ ] One-Start autonomous search/selection/attack/result loop with Stop and measured preparation deadline.

## Verification record
33Python tests passed after raw-frame transport decoding was added (new valid12/16-byte headers, pixel conversion and malformed-frame regressions). Native widget checks are included. A real BlueStacks battle and return home succeeded in an agent-guided diagnostic: see docs/live-device-check.md. This did not exercise a standalone autonomous controller.

Fresh read-only review identified launcher fallback failure, recording cleanup failure and app-transition misattribution. All were reproduced by tests and fixed in one pass. Windows PowerShell5.1 fallback test now rejects a real isolated Python without Pillow and accepts the valid bundled fallback. Native cleanup always restores state even after recording close errors; package checks bracket capture.

Original browser server was stopped. Its files/tests remain as prior work only. A single real attack reached three stars/100%; no trained attack model, calibrated98% estimate, or ten-second autonomous preparation has been demonstrated. The native setup/capture layer is not completion of the user's autonomous-controller objective.
