# V3 SWDIO turnaround experiment — qualification record

Status: **EXPERIMENT / NO-GO for hardware until CI and operator validation**.

## Why this is the next experiment

The installed ESP32-S3 8MB V2 probe successfully enumerates with OpenOCD and can drive/read GPIO7 nRESET, but `DPIDR` reads from WORLDE AT32F415 return repeated `SWD ack not OK @ 0 JUNK`. SWCLK pulses (~43.5kHz) and varying SWDIO voltage (~0–3.3V) were observed using a one-channel scope, but these measurements cannot distinguish a real target ACK from a probe-induced artifact. A 1ms/div single capture of a SWDIO edge is not sufficient to diagnose turnaround.

Espressif's currently unmerged upstream [PR #40](https://github.com/espressif/esp-usb-bridge/pull/40) reports that dedicated GPIO SWDIO output can remain driven during turnaround on ESP32-S2/S3, which caused all ACK reads to fail. The PR author reports successful nRF52 debugging after the fix. A commenter with ESP32-S3 similarly reports a fake ACK with or without a target connected, resolved by changing SWDIO output direction. In January 2026 an upstream maintainer noted that ESP-IDF v5.4+ dedicated GPIO changes were not yet accommodated; our V2 was built using ESP-IDF v5.4. These reports provide a **specific plausible software hypothesis**, not proof this WORLDE issue has the same cause.

## Implementation

- Source remains pinned to `09a160432555ba936a47a1b32ca7fbf17922d709`.
- Existing V2 GPIO7 open-drain nRESET patch remains intact.
- V3 applies only the minimal `debug_gpio.c` and `debug_gpio.h` changes from upstream PR #40 to release SWDIO during ACK turnaround and use regular GPIO output.
- Extra patch script aborts if anchored source code has changed; CI compiles ESP-IDF 5.4, 8MB, GPIO8=SWDIO, GPIO10=SWCLK.
- Artifact uses unique `experimental` name. Nothing is flashed automatically.

## Next physical GO gates

1. Keep and verify the existing 8MB raw ESP32 backup: SHA256 `07dfed79d3a6c413e3b53d4039f8147bf3fb2d1c9c2b19ccbf51dc685674baa0`.
2. Verify V3 build passed and new artifact SHA256 before considering any firmware update.
3. All ESP32↔WORLDE connections disconnected when changing ESP32 firmware. No WORLDE flash/write/unlock.
4. Verify CMSIS-DAP interface and idle nRESET after boot, then reconnect verified common ground, GPIO8/10 SWD lines and GPIO7 via 1k series resistance, with both devices powered normally.
5. Only try OpenOCD DPIDR read at conservative speed and save result. No erase, unlock, target firmware read attempts or backup until proven compatible. If SWD still returns JUNK, revert to a passive diagnostic plan and consider alternative probe.
6. Keep V2/V3 branches and firmware binaries separately; do not merge V3 into V2 or main just because CI passes.

## Previously observed display behavior

The one-channel scope image shows Vmax ~3.4V, Vmin ~0.1V and single rising edge but screen timebase is `1mS/div`, not requested `200us/div`. That screenshot does not expose complete ACK sequence or verify the culprit.
