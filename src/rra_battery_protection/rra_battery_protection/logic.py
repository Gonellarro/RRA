"""Pure Python filtering/state logic; no ROS or hardware side effects."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from statistics import median


class State(str, Enum):
    NORMAL = "NORMAL"
    LOW_VOLTAGE_WARNING = "LOW_VOLTAGE_WARNING"
    SHUTDOWN_PENDING = "SHUTDOWN_PENDING"
    SHUTDOWN_REQUESTED = "SHUTDOWN_REQUESTED"
    POWER_CUTOFF_PENDING = "POWER_CUTOFF_PENDING"
    POWER_CUTOFF = "POWER_CUTOFF"
    SENSOR_FAULT = "SENSOR_FAULT"


@dataclass(frozen=True)
class Config:
    sample_period_s: float = 0.5
    ring_size: int = 20
    median_size: int = 5
    ema_tau_s: float = 2.0
    warning_v: float = 7.4
    shutdown_v: float = 7.3
    cutoff_v: float = 7.2
    emergency_v: float = 7.0
    warning_confirm_s: float = 10.0
    shutdown_confirm_s: float = 10.0
    cutoff_confirm_s: float = 5.0
    cutoff_after_request_s: float = 20.0
    prepared_grace_s: float = 5.0
    emergency_confirm_s: float = 1.0
    hysteresis_v: float = 0.10
    recovery_confirm_s: float = 3.0
    sensor_fault_s: float = 3.0
    min_valid_v: float = 5.0
    max_valid_v: float = 9.0
    emergency_enabled: bool = False


class Protection:
    """Monotonic-time thresholds with independent timers and latched actions."""
    def __init__(self, cfg: Config = Config()):
        self.cfg = cfg
        self.samples: deque[float] = deque(maxlen=cfg.ring_size)
        self.short: deque[float] = deque(maxlen=cfg.median_size)
        self.ema: float | None = None
        self.last_t: float | None = None
        self.pending_since: dict[str, float | None] = {k: None for k in ("warning", "shutdown", "cutoff", "emergency")}
        self.recovery_since: float | None = None
        self.invalid_since: float | None = None
        self.sensor_fault_latched = False
        self.state = State.NORMAL
        self.warning_latched = False
        self.shutdown_latched = False
        self.cutoff_latched = False
        self.emergency_latched = False
        self.last_instant: float | None = None
        self.last_filtered: float | None = None
        self.shutdown_requested_at: float | None = None
        self.companion_prepared_at: float | None = None
        self.cutoff_condition_confirmed = False
        self.cutoff_recovery_since: float | None = None

    def acknowledge_prepared(self, now: float) -> bool:
        """Record Companion's explicit 'shutdown prepared' acknowledgement."""
        if (not self.shutdown_latched or self.shutdown_requested_at is None
                or now < self.shutdown_requested_at or self.cutoff_latched):
            return False
        self.companion_prepared_at = now
        return True

    def _filter(self, v: float, dt: float) -> float:
        self.samples.append(v)
        self.short.append(v)
        med = float(median(self.short))
        alpha = 1.0 if self.ema is None else 1.0 - __import__("math").exp(-dt / self.cfg.ema_tau_s)
        self.ema = med if self.ema is None else alpha * med + (1.0 - alpha) * self.ema
        return self.ema

    @staticmethod
    def _elapsed(start: float | None, now: float) -> float:
        return 0.0 if start is None else max(0.0, now - start)

    def update(self, now: float, voltage: float | None, healthy: bool = True) -> list[str]:
        """Feed one timestamped sample and return one-shot events."""
        if self.last_t is not None and now <= self.last_t:
            raise ValueError("timestamps must be strictly increasing monotonic seconds")
        dt = self.cfg.sample_period_s if self.last_t is None else min(now - self.last_t, 2.0)
        self.last_t = now
        valid = healthy and voltage is not None and isfinite(voltage) and self.cfg.min_valid_v <= voltage <= self.cfg.max_valid_v
        if not valid:
            if self.invalid_since is None:
                self.invalid_since = now
            if now - self.invalid_since >= self.cfg.sensor_fault_s and not self.sensor_fault_latched:
                self.state = State.SENSOR_FAULT
                self.sensor_fault_latched = True
                if not self.shutdown_latched and not self.cutoff_latched:
                    self.pending_since = {k: None for k in self.pending_since}
                return ["sensor_fault"]
            return ["invalid_sample"]

        self.invalid_since = None
        if self.sensor_fault_latched:
            self.sensor_fault_latched = False
            if not self.shutdown_latched and not self.cutoff_latched:
                self.state = State.NORMAL
        self.last_instant = voltage
        filtered = self._filter(voltage, dt)
        self.last_filtered = filtered
        events: list[str] = []

        def request_shutdown() -> None:
            if not self.shutdown_latched:
                self.shutdown_latched = True
                self.shutdown_requested_at = now
                events.append("shutdown")

        def confirm(key: str, threshold: float, duration: float, enabled: bool = True) -> bool:
            if not enabled:
                return False
            if filtered <= threshold:
                if self.pending_since[key] is None:
                    self.pending_since[key] = now
                return now - self.pending_since[key] >= duration
            # Hysteresis band keeps a pending timer alive. Clear only after a
            # sustained rise above threshold + hysteresis.
            if filtered > threshold + self.cfg.hysteresis_v:
                if self.recovery_since is None:
                    self.recovery_since = now
                if now - self.recovery_since >= self.cfg.recovery_confirm_s:
                    self.pending_since[key] = None
            return False

        if filtered > self.cfg.warning_v + self.cfg.hysteresis_v:
            if self.recovery_since is None:
                self.recovery_since = now
            if now - self.recovery_since >= self.cfg.recovery_confirm_s:
                if not self.shutdown_latched and not self.cutoff_latched:
                    self.warning_latched = False
                    self.state = State.NORMAL
        else:
            self.recovery_since = None

        if not self.shutdown_latched and not self.cutoff_latched and not self.warning_latched and confirm("warning", self.cfg.warning_v, self.cfg.warning_confirm_s):
            self.warning_latched = True
            self.state = State.LOW_VOLTAGE_WARNING
            events.append("warning")
        if not self.shutdown_latched and confirm("shutdown", self.cfg.shutdown_v, self.cfg.shutdown_confirm_s):
            request_shutdown()
            self.state = State.SHUTDOWN_REQUESTED
        elif not self.shutdown_latched and filtered <= self.cfg.shutdown_v:
            self.state = State.SHUTDOWN_PENDING

        cutoff_confirmed = not self.cutoff_latched and confirm("cutoff", self.cfg.cutoff_v, self.cfg.cutoff_confirm_s)
        # Emergency path is based on consecutive valid instantaneous samples,
        # independent of the long EMA; one bad sample cannot satisfy 1 second.
        emergency_confirmed = False
        if self.cfg.emergency_enabled and not self.emergency_latched:
            if voltage <= self.cfg.emergency_v:
                if self.pending_since["emergency"] is None:
                    self.pending_since["emergency"] = now
                emergency_confirmed = now - self.pending_since["emergency"] >= self.cfg.emergency_confirm_s
            else:
                self.pending_since["emergency"] = None
        if cutoff_confirmed:
            self.cutoff_condition_confirmed = True
        if self.cutoff_condition_confirmed and filtered > self.cfg.cutoff_v + self.cfg.hysteresis_v:
            if self.cutoff_recovery_since is None:
                self.cutoff_recovery_since = now
            elif now - self.cutoff_recovery_since >= self.cfg.recovery_confirm_s:
                self.cutoff_condition_confirmed = False
                self.pending_since["cutoff"] = None
        else:
            self.cutoff_recovery_since = None
        if emergency_confirmed:
            # Deep emergency is the only path allowed to skip the orderly wait.
            request_shutdown()
            if emergency_confirmed:
                self.emergency_latched = True
                events.append("emergency_cutoff")
            self.cutoff_latched = True
            self.state = State.POWER_CUTOFF
            events.append("power_cutoff")
        elif self.cutoff_condition_confirmed and not self.cutoff_latched:
            # A direct/rapid drop may reach the 7.2 V timer before the 7.3 V
            # timer. Request shutdown immediately, then wait for readiness or
            # a bounded fallback interval before allowing the physical cut.
            request_shutdown()
            prepared = (self.companion_prepared_at is not None
                        and now - self.companion_prepared_at >= self.cfg.prepared_grace_s)
            fallback = (self.shutdown_requested_at is not None
                        and now - self.shutdown_requested_at >= self.cfg.cutoff_after_request_s)
            if prepared or fallback:
                self.cutoff_latched = True
                self.state = State.POWER_CUTOFF
                events.append("power_cutoff")
            else:
                self.state = State.POWER_CUTOFF_PENDING
        elif self.shutdown_latched and not self.cutoff_latched:
            self.state = State.SHUTDOWN_REQUESTED
        elif not self.cutoff_latched and filtered <= self.cfg.cutoff_v:
            self.state = State.POWER_CUTOFF_PENDING
        return events


def simulate(protection: Protection, values: list[float | None], period: float = 0.5) -> list[tuple[float, list[str], State, float | None]]:
    out = []
    for i, v in enumerate(values):
        t = i * period
        events = protection.update(t, v)
        out.append((t, events, protection.state, protection.last_filtered))
    return out
