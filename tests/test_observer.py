import unittest
from datetime import datetime, timedelta

from src.memory.working_memory import WorkingMemory
from src.telemetry.observer import observe


class Clock:

    def __init__(self):
        self.value = datetime(2026, 1, 1, 10, 0, 0)

    def __call__(self):
        result = self.value
        self.value += timedelta(seconds=5)
        return result


class ObserverTests(unittest.TestCase):

    def test_keyboard_interrupt_persists_last_event(self):
        calls = iter([
            {"title": "Inbox - Outlook"},
            KeyboardInterrupt(),
        ])
        persisted = []

        def window_provider():
            value = next(calls)
            if isinstance(value, BaseException):
                raise value
            return value

        observe(
            WorkingMemory(),
            window_provider=window_provider,
            event_sink=persisted.append,
            clock=Clock(),
            sleeper=lambda _seconds: None,
        )

        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0].application, "Outlook")
        self.assertEqual(persisted[0].duration, 5)

    def test_transition_and_shutdown_persist_both_events(self):
        windows = iter([
            {"title": "one.py - Project - Visual Studio Code"},
            {"title": "Inbox - Outlook"},
        ])
        persisted = []
        memory = WorkingMemory()

        observe(
            memory,
            window_provider=lambda: next(windows),
            event_sink=persisted.append,
            clock=Clock(),
            sleeper=lambda _seconds: None,
            max_iterations=2,
        )

        self.assertEqual(len(persisted), 2)
        self.assertEqual(persisted[0].application, "VS Code")
        self.assertEqual(persisted[0].duration, 5)
        self.assertEqual(persisted[1].application, "Outlook")
        self.assertEqual(persisted[1].duration, 5)
        self.assertEqual(len(memory.all()), 2)

    def test_same_title_in_different_application_is_a_transition(self):
        windows = iter([
            {"title": "Shared - Visual Studio Code"},
            {"title": "Shared - Outlook"},
        ])
        persisted = []

        observe(
            WorkingMemory(),
            window_provider=lambda: next(windows),
            event_sink=persisted.append,
            clock=Clock(),
            sleeper=lambda _seconds: None,
            max_iterations=2,
        )

        self.assertEqual(len(persisted), 2)

    def test_heartbeat_runs_during_observation_and_finalization(self):
        beats = []
        observe(
            WorkingMemory(),
            window_provider=lambda: {"title": "Inbox - Outlook"},
            event_sink=lambda _event: None,
            clock=Clock(),
            sleeper=lambda _seconds: None,
            max_iterations=1,
            heartbeat=lambda: beats.append(True),
        )
        self.assertEqual(len(beats), 2)


if __name__ == "__main__":
    unittest.main()
