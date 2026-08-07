import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from src.analytics.queries import idle_metrics_for_date
from src.storage.database import initialize, save_idle_metrics
from src.telemetry.idle import IdleTimeTracker
from src.telemetry.shutdown import WindowsShutdownSignal, request_shutdown


class Clock:
    def __init__(self):
        self.value = datetime(2026, 8, 7, 10, 0, 0)

    def __call__(self):
        value = self.value
        self.value += timedelta(seconds=10)
        return value


class IdleTelemetryTests(unittest.TestCase):
    def test_separates_active_and_inactive_time(self):
        idle_values = iter([301, 301])
        tracker = IdleTimeTracker(lambda: next(idle_values), clock=Clock())
        tracker.sample()
        tracker.sample()
        tracker.sample()
        self.assertEqual(tracker.active_seconds, 0)
        self.assertEqual(tracker.inactive_seconds, 20)

    def test_persists_only_daily_aggregates(self):
        tracker = IdleTimeTracker(lambda: 0)
        tracker.active_seconds = 40
        tracker.inactive_seconds = 20
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "idle.db"
            initialize(database)
            save_idle_metrics(date(2026, 8, 7), tracker, database)
            metrics = idle_metrics_for_date(date(2026, 8, 7), database)
        self.assertEqual(metrics["observed_seconds"], 60)
        self.assertEqual(metrics["active_seconds"], 40)
        self.assertEqual(metrics["inactive_seconds"], 20)

    def test_named_signal_requests_clean_shutdown(self):
        signal = WindowsShutdownSignal()
        try:
            self.assertFalse(signal.is_set())
            self.assertTrue(request_shutdown())
            self.assertTrue(signal.is_set())
        finally:
            signal.close()


if __name__ == "__main__":
    unittest.main()
