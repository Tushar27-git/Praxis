# First live device check — 2026-10-28

User reports the game running in the background on a new account. BlueStacks HD-Player is running. Project ADB connected successfully to `127.0.0.1:5555`; `emulator-5554` also appears and represents the same target, not a second selected device.

The selected Android foreground package is `com.supercell.clashofclans`. The real frame is 1600×900 and saved locally at `output/native/live-game.png`. It shows the home village with Town Hall selected, explicitly labeled Level 2. The player level is 1. No tutorial overlay is visible in this observation. Do not infer selected army counts from animated camp occupants.

Measured through the current project subprocess/ADB transport:

| Operation | Duration |
|---|---:|
| First PNG capture | 4031 ms |
| Subsequent PNG captures | 3843, 2953, 3171 ms |
| Android foreground-package query | 172 ms |
| Uncompressed screencap | 1875 ms |

Raw frame was 5,760,016 bytes, with little-endian header `(1600, 900, 1, 0)`. These are a few local samples, not a performance distribution. Source of delay has not been isolated.

No Windows mouse/focus operations or Android game inputs were sent. The game was not independently covered or minimized by the agent; background status is user-reported. Capture through the emulator succeeds independent of a desktop screenshot. Actual input alignment and performance remain unverified.

The current `.75` second input freshness guard correctly makes these frames ineligible for action. Do not relax it merely to make taps pass. Investigate a faster capture stream and measure acquisition-to-action latency before enabling combat control. Automatic scene/army recognition and the autonomous battle loop remain unimplemented.

## Requested live attack diagnostic

The user authorized a live attack diagnostic after this check. The selected emulator continued to appear ready in `adb devices`, but every tested Android command returned `error: closed`, including `shell echo coc_probe` and `screenrecord --help`. A five-second H.264 probe produced zero bytes; that establishes a failed transport request, not lack of video-codec support. Both duplicate serials behaved the same. Reconnecting the selected local transport and then connecting again did not restore shell access. HD-Player was still running/responding. No attack, troop deployment, purchase, or other game input was sent.

Asked the user to check BlueStacks Settings → Advanced → Android Debug Bridge, enable/save it and report the displayed port. User confirmed enabled/5555; a subsequent harmless shell check and real Clash frame succeeded.

## Completed agent-guided live attack

This was direct agent-guided gameplay through diagnostic Python/ADB commands, not a standalone autonomous Start loop or automatic visual army reader. Each tap used the current .75second freshness guard, Android foreground-package check, and a matching reference-button/layout region. Two bounded deployment holds applied equivalent checks before starting; an already executing hold cannot be cancelled mid-command by that event. No desktop mouse/focus commands were issued.

- Inspection of My Army showed20 level-one Barbarians,20/30 capacity, no available spells/heroes/siege/reinforcements.
- Army Attack entered regular matchmaking; match cost10 gold. Entry chosen near the exposed northeast cannon at(580,100) in a640x360 frame.
- First2.5second stationary deployment hold deployed16 troops; second1second hold deployed the remaining4. Observation confirmed all forces deployed and42% damage, followed by a victory screen with100% damage andthree stars.
- Result lists1770 gold,5640 elixir and300/300 bonus. Home storage showed4000/4000 after returning. No gems or purchases were used.
- Evidence: output/native/live-attack-result.png. Returned home through a guarded tap; original1600x900 resolution restored with wm size reset and verified by actual capture (output/native/live-home-after-test.png).

Capture investigation: on-device PNG generation alone took1.95seconds; transferring its2,441,217-byte file took766ms. Five-second H.264 stream succeeded after ADB restoration (first1024bytes1078ms,609615totalbytes); no steady-stream end-to-end latency measured. Raw960x540 capture578ms; raw800x450421/485/515ms. Production capture now decodes raw RGBA_8888 (validated12/16byte headers) and encodes PNG locally. Actual640x360 capture samples328–453ms supported guarded inputs. Native interface uses the same improved capture path, but no combat controls were added.

Restored1600x900 raw capture was2734ms. Thus this change does not solve high-resolution combat latency. Temporary low-resolution operation allowed this diagnostic; do not claim all latencies fixed or weaken the freshness guard. Full suite33/33passed. One easy opponent and manual agent decisions establish neither a calibrated98% score nor a ten-second autonomous strategy.

## Second attack attempt blocked by freshness

User requested another guided live attack. Real home village/package was verified; original1600x900 capture2141ms. Temporary640x360 and512x288 captures/focus checks fluctuated substantially. Observed capture samples included484ms,719ms,1172ms,1234ms and2187ms; a raw diagnostic omitting PNG encoding still reached3734ms before input. Full activity query varied from125ms to531ms in separate samples. Thus local PNG encoding alone does not explain this later variability.

Every attempted Battle tap was rejected by the existing750ms guard, before any input command. No matchmaking, troop deployment or spending occurred. Original physical1600x900 resolution was restored. No product code changed. Next resolve persistent streaming and measure tail latency, rather than keep retrying stale screenshots or raise the guard.
