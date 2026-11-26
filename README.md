# Worlde-SWD-Builder

Build-only GitHub Actions workflow for an ESP32-S3 **CMSIS-DAP (USB bulk) SWD probe**, based on pinned official [Espressif ESP USB Bridge](https://github.com/espressif/esp-usb-bridge).

## V2: GPIO7 nRESET support (experimental; not hardware-validated)

This branch changes only the **ESP32-S3 probe firmware**, not the WORLDE controller firmware.

- **GPIO8:** SWDIO, WORLDE DEBUG1 pin 3 (AT32F415 PA13)
- **GPIO10:** SWCLK, WORLDE DEBUG1 pin 4 (AT32F415 PA14)
- **GPIO7:** nRESET open-drain output/input (via existing **1 kΩ series resistor** to the target NRST point near R5); high means *released*, never drive target high.
- **GND:** separate, verified common ground between boards.
- WORLDE DEBUG1 pin 1 is target 3.2 V **sense only**; pin 2 is unidentified; neither connects to ESP32 3V3/5V.

The pinned upstream revision's `PIN_nRESET_IN` always reports zero and `PIN_nRESET_OUT` does nothing. This branch adds real GPIO7 nRESET input/readback, low-only output, and release-to-high-impedance on disconnect. The source patch checks exact upstream anchor text; mismatches fail the build.

### Known physical measurements (user-reported; before V2)

- Target NRST about **3.2 V** when released; about **0.3 V** when pulled low through 1 kΩ. This verifies a reset response, **not** a successful SWD connection.
- Continuity verified for the three SWDIO/SWCLK/GND connections.
- OpenOCD 0.12.0 enumerates the ESP32-S3 CMSIS-DAPv2 probe, but reading SWD DPIDR fails with `Error connecting DP: cannot read IDR`.
- Neither SWD attach nor safe target firmware backup is proven. Read protection may block either.

## Build V2 (does not flash)

Open **Actions → Build ESP32-S3 CMSIS-DAP nRESET V2 → Run workflow**, or push an edit to the workflow/patch on this branch. On green build, download the artifact named `orca-swd-esp32s3-8mb-nreset-v2` which contains `orca-swd-esp32s3-nreset-v2.bin`.

The workflow:
1. Checks out builder sources and the official ESP USB Bridge at pinned commit `09a160432555ba936a47a1b32ca7fbf17922d709`.
2. Applies the narrow nRESET patch to upstream `DAP_config.h` (fails closed on upstream drift).
3. Uses ESP-IDF v5.4; builds and checks `CONFIG_DEBUG_PROBE_IFACE_SWD=y`, SWDIO=8, SWCLK=10, flash size=8MB.
4. Uploads a separate V2 artifact, **without flashing any device**.

The previous 2MB-default artifact must not be used. The 8MB V1 and 8MB nRESET V2 builds must not be confused.

## Hardware safety / GO gates

**Do not flash V2 until its CI is green, the ESP32-S3 original-firmware backup status is understood, and the wiring is verified with both boards unpowered.** A physical test must first confirm nRESET is released to approximately 3.2V when inactive and is never driven high by the probe. The nRESET series resistor is **not** a pull-down to ground; connect it only between GPIO7 and the verified NRST point when the tested V2 probe is ready.

Never power the WORLDE target from the ESP32; power each board separately through its normal USB input, with common GND and no shared 3.3V/5V wire. Keep GPIO7 resistor free and insulated during V1 testing.

For WORLDE, authorize only read-only SWD identity and nondestructive checks: **no unlock/readout protection disable, mass erase, flash writes, or firmware upgrades**. Even a working nRESET interface does not guarantee that a target will accept SWD; inspect DPIDR first.

## V1 baseline

On `main`, the earlier build uses the official upstream defaults and 8MB flash but has **no nRESET support**. The official editor/MIDI troubleshooting and the existing ESP32-S3 V1 firmware are not altered by this branch.
