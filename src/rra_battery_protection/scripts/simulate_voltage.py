#!/usr/bin/env python3
"""Replay illustrative voltage profiles; does not contact hardware."""
import argparse
from rra_battery_protection.logic import Config, Protection


def profiles():
    return {
        "servo_dip": [7.6] * 20 + [7.1] + [7.6] * 30,
        "servo_sag_3s": [7.6] * 20 + [7.25, 7.5] * 3 + [7.6] * 30,
        "slow_discharge": [7.6] * 4 + [7.35] * 30 + [7.25] * 30 + [7.15] * 30,
        "deep_drop": [7.6] * 6 + [7.1] * 30,
        "bad_sample": [7.6] * 10 + [0.0] + [7.6] * 30,
        "sensor_loss": [7.6] * 8 + [None] * 12,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=["all", *profiles() ], default="all", nargs="?")
    args = parser.parse_args()
    selected = profiles() if args.profile == "all" else {args.profile: profiles()[args.profile]}
    for name, values in selected.items():
        p = Protection(Config(emergency_enabled=False))
        print(f"\n[{name}]")
        for i, value in enumerate(values):
            events = p.update(i * 0.5, value)
            if events:
                print(f"t={i * 0.5:5.1f}s sample={value!s:>4} filtered={p.last_filtered!s:>5} state={p.state.value} events={','.join(events)}")


if __name__ == "__main__":
    main()
