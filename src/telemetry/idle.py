"""Aggregate active and inactive time without capturing user input."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class IdleTimeTracker:
    idle_provider: callable
    threshold_seconds: int = 300
    clock: callable = datetime.now
    active_seconds: int = 0
    inactive_seconds: int = 0
    _last_sample: datetime | None = None

    def sample(self):
        now = self.clock()
        if self._last_sample is None:
            self._last_sample = now
            return

        elapsed = max(0, int((now - self._last_sample).total_seconds()))
        self._last_sample = now
        if self.idle_provider() >= self.threshold_seconds:
            self.inactive_seconds += elapsed
        else:
            self.active_seconds += elapsed

    @property
    def observed_seconds(self):
        return self.active_seconds + self.inactive_seconds
