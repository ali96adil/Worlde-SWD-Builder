#!/usr/bin/env python3
"""Experimental fix for SWDIO turnaround in pinned esp-usb-bridge.

Based on upstream PR #40 (unmerged, as of 2026-11-27):
https://github.com/espressif/esp-usb-bridge/pull/40

This patch runs in GitHub Actions source checkout ONLY. Never writes
to an ESP32 or WORLDE device. Anchors fail closed if upstream drifts.
"""
from pathlib import Path
import sys


def exact_replace(src: str, old: str, new: str, what: str) -> str:
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"Refusing to patch {what}: expected one anchor, got {count}")
    return src.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-swdio-turnaround-v3.py bridge/components/debug_probe")
    root = Path(sys.argv[1])
    header = root / "debug_gpio.h"
    impl = root / "debug_gpio.c"
    h = header.read_text(encoding="utf-8")
    c = impl.read_text(encoding="utf-8")

    c = exact_replace(
        c,
        """        dedic_gpio_bundle_config_t io_bundle_config = {
            .gpio_array = bundle_io_gpios,
            .array_size = ARRAY_SIZE(bundle_io_gpios),
            .flags = {
                .out_en = 1,
                .in_en = 1,
            },
        };""",
        """        dedic_gpio_bundle_config_t io_bundle_config = {
            .gpio_array = bundle_io_gpios,
            .array_size = ARRAY_SIZE(bundle_io_gpios),
            .flags = {
                .out_en = 0, // SWDIO must release its output during ACK turnaround.
                .in_en = 1,
            },
        };""",
        "SWDIO dedicated GPIO bundle mode",
    )
    h = exact_replace(
        h,
        """__STATIC_FORCEINLINE void debug_probe_swdio_out_enable(void)
{
    REG_WRITE(GPIO_FUNC0_OUT_SEL_CFG_REG + (GPIO_SWDIO * 4), dedic_gpio_conf);
    gpio_ll_output_enable(dedic_gpio_dev, GPIO_SWDIO);
}

__STATIC_FORCEINLINE void debug_probe_swdio_out_disable(void)
{
    gpio_ll_output_disable(dedic_gpio_dev, GPIO_SWDIO);
}""",
        """__STATIC_FORCEINLINE void debug_probe_swdio_out_enable(void)
{
    gpio_ll_output_enable(dedic_gpio_dev, GPIO_SWDIO);
}

__STATIC_FORCEINLINE void debug_probe_swdio_out_disable(void)
{
    REG_WRITE(GPIO_FUNC0_OUT_SEL_CFG_REG + (GPIO_SWDIO * 4), dedic_gpio_conf);
    gpio_ll_output_disable(dedic_gpio_dev, GPIO_SWDIO);
}""",
        "SWDIO output enable/disable",
    )
    h = exact_replace(
        h,
        """__STATIC_FORCEINLINE void debug_probe_swdio_set(void)
{
    dedic_gpio_cpu_ll_write_mask(GPIO_SWDIO_OUT_MASK, GPIO_SWDIO_OUT_MASK);
}

__STATIC_FORCEINLINE void debug_probe_swdio_clr(void)
{
    dedic_gpio_cpu_ll_write_mask(GPIO_SWDIO_OUT_MASK, 0);
}

__STATIC_FORCEINLINE void debug_probe_swdio_write(int val)
{
    dedic_gpio_cpu_ll_write_mask(GPIO_SWDIO_OUT_MASK, (val & 0x01) ? GPIO_SWDIO_OUT_MASK : 0);
}""",
        """__STATIC_FORCEINLINE void debug_probe_swdio_set(void)
{
    gpio_ll_set_level(dedic_gpio_dev, GPIO_SWDIO, 1);
}

__STATIC_FORCEINLINE void debug_probe_swdio_clr(void)
{
    gpio_ll_set_level(dedic_gpio_dev, GPIO_SWDIO, 0);
}

__STATIC_FORCEINLINE void debug_probe_swdio_write(int val)
{
    gpio_ll_set_level(dedic_gpio_dev, GPIO_SWDIO, (val & 0x1) ? 1 : 0);
}""",
        "SWDIO ordinary GPIO writes",
    )
    impl.write_text(c, encoding="utf-8")
    header.write_text(h, encoding="utf-8")
    print("Applied experimental SWDIO turnaround patch, based on upstream PR #40")


if __name__ == "__main__":
    main()
