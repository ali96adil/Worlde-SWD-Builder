# Worlde-SWD-Builder

Build-only GitHub Actions workflow for a generic **ESP32-S3 CMSIS-DAP (USB bulk) SWD probe**, based on the official [Espressif ESP USB Bridge](https://github.com/espressif/esp-usb-bridge).

## Build

Open **Actions → Build ESP32-S3 CMSIS-DAP → Run workflow**, or let a change to the workflow file trigger a build. On success, download the latest `orca-swd-esp32s3-8mb` artifact ZIP and extract `orca-swd-esp32s3.bin`.

- Upstream revision is pinned in the workflow for reproducibility.
- Build uses the official `espressif/idf:v5.4` container. No local ESP-IDF download is needed.
- The generated binary is **not flashed** by this workflow.
- SWD mode is explicitly selected and checked after build.
- ESP32-S3 8MB flash size is configured and validated to match the measured hardware; the earlier 2MB-default artifact must not be used.

## Hardware safety / pending checks

**DO NOT flash or connect the ESP32-S3 to the WORLDE controller yet.** First identify the ESP32-S3 board and confirm free, exposed GPIO pins and its USB wiring. With upstream default SWD pin configuration, GPIO8 is SWDIO and GPIO10 is SWCLK (not yet validated for this particular board).

WORLDE DEBUG1 findings from continuity measurements:
- Pin 3 connects to AT32F415 PA13 / SWDIO.
- Pin 4 connects to AT32F415 PA14 / SWCLK.
- Pin 1 is approximately 3.2 V target VDD/reference, **not** an external 5V supply input.
- Pin 2 is **unidentified: leave disconnected**.
- Ground must come from a separately verified GND point, not an assumed DEBUG1 pin.

Back up the original ESP32-S3 firmware before flashing. For WORLDE use **read-only SWD identification and non-destructive checks** only: never unlock read protection, mass erase, reset-and-flash, or alter the original firmware merely to gain access. SWD access and backup are not guaranteed if readout protection is enabled.
