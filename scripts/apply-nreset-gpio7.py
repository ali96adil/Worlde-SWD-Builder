#!/usr/bin/env python3
"""Patch the pinned esp-usb-bridge CMSIS-DAP backend to use GPIO7 for nRESET.

Build-only: edits the checked-out upstream source, never hardware.
Fails closed if the upstream code does not match the audited revision.
"""
from pathlib import Path
import sys


def replace_exact(source: str, before: str, after: str, label: str) -> str:
    count = source.count(before)
    if count != 1:
        raise SystemExit(f"Refusing nRESET patch: expected one {label} anchor, got {count}")
    return source.replace(before, after, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-nreset-gpio7.py path/to/DAP_config.h")
    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    source = replace_exact(
        source,
        '#include "debug_gpio.h"\n#include "esp_timer.h"',
        '#include "debug_gpio.h"\n#include "esp_err.h"\n#include "esp_timer.h"',
        "explicit error-check header",
    )
    source = replace_exact(
        source,
        """__STATIC_INLINE void PORT_SWD_SETUP (void) {
    debug_probe_init_swd_pins();
}""",
        """__STATIC_INLINE void PORT_SWD_SETUP (void) {
    debug_probe_init_swd_pins();
    // Set output latch HIGH before enabling: open-drain HIGH releases nRESET.
    ESP_ERROR_CHECK(gpio_set_level(GPIO_NUM_7, 1));
    const gpio_config_t reset_cfg = {
        .pin_bit_mask = (1ULL << GPIO_NUM_7),
        .mode = GPIO_MODE_INPUT_OUTPUT_OD,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&reset_cfg));
}""",
        "SWD setup",
    )
    source = replace_exact(
        source,
        """__STATIC_INLINE void PORT_OFF (void) {
    debug_probe_reset_pins();
}""",
        """__STATIC_INLINE void PORT_OFF (void) {
    // Never hold the target in reset after the debugger disconnects.
    (void)gpio_set_level(GPIO_NUM_7, 1);
    (void)gpio_set_direction(GPIO_NUM_7, GPIO_MODE_INPUT);
    debug_probe_reset_pins();
}""",
        "SWD teardown",
    )
    source = replace_exact(
        source,
        """__STATIC_FORCEINLINE uint32_t PIN_nRESET_IN  (void) {
  return (0U);
}""",
        """__STATIC_FORCEINLINE uint32_t PIN_nRESET_IN  (void) {
  return (gpio_get_level(GPIO_NUM_7) ? 1U : 0U);
}""",
        "nRESET input",
    )
    source = replace_exact(
        source,
        """__STATIC_FORCEINLINE void     PIN_nRESET_OUT (uint32_t bit) {
  ;
}""",
        """__STATIC_FORCEINLINE void     PIN_nRESET_OUT (uint32_t bit) {
  // Drive LOW only; HIGH is high impedance, using target's own pull-up.
  (void)gpio_set_level(GPIO_NUM_7, bit ? 1 : 0);
}""",
        "nRESET output",
    )
    path.write_text(source, encoding="utf-8")
    print("Applied guarded GPIO7 open-drain nRESET patch to", path)


if __name__ == "__main__":
    main()
