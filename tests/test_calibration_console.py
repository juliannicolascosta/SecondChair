import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from src.telemetry.interaction.collector import InteractionCollector
from src.telemetry.interaction.models import InteractionType
from src.workflows.console import ConsoleCalibrationController
from src.workflows.repository import WorkflowTraceRepository


START = datetime(2026, 8, 8, 10, 0, 0)


class Clock:
    def __init__(self):
        self.value = START

    def __call__(self):
        result = self.value
        self.value += timedelta(minutes=5)
        return result


class FakeHotkey:
    def __init__(self):
        self.callback = None
        self.starts = 0
        self.stops = 0

    def start(self, callback):
        self.callback = callback
        self.starts += 1

    def stop(self):
        self.stops += 1

    def press(self):
        self.callback()


class CalibrationConsoleTests(unittest.TestCase):
    def test_same_key_starts_and_finishes_exact_calibration(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = Clock()
            repository = WorkflowTraceRepository(
                Path(directory) / "calibration.db",
                clock=clock,
            )
            collector = InteractionCollector()
            collector.running = True
            output = []
            hotkey = FakeHotkey()
            controller = ConsoleCalibrationController(
                repository,
                collector,
                hotkey_source=hotkey,
                input_func=lambda _prompt: "  Generar   factura  ",
                output=output.append,
                sleeper=lambda _seconds: None,
                countdown=3,
                clock=clock,
            )

            controller.start()
            hotkey.press()
            active = repository.current()
            self.assertEqual(active.label, "Generar factura")
            collector.record(
                InteractionType.KEYBOARD_ACTIVITY,
                timestamp=START + timedelta(minutes=1),
                window={"application": "Word", "process_name": "WINWORD.EXE"},
            )
            hotkey.press()

            self.assertIsNone(repository.current())
            trace = repository.list()[0]
            self.assertEqual(trace.interaction_metrics_status, "exact")
            self.assertEqual(trace.keyboard_actions, 1)
            rendered = "\n".join(output)
            self.assertIn("CALIBRACIÓN INICIADA", rendered)
            self.assertIn("CALIBRACIÓN FINALIZADA", rendered)
            self.assertIn(f"ID: {trace.id}", rendered)
            controller.stop()
            self.assertEqual((hotkey.starts, hotkey.stops), (1, 1))

    def test_empty_label_does_not_start_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = WorkflowTraceRepository(Path(directory) / "calibration.db")
            output = []
            controller = ConsoleCalibrationController(
                repository,
                InteractionCollector(),
                hotkey_source=FakeHotkey(),
                input_func=lambda _prompt: "   ",
                output=output.append,
                sleeper=lambda _seconds: None,
            )
            controller.toggle()
            self.assertIsNone(repository.current())
            self.assertTrue(any("cancelada" in line for line in output))

    def test_list_key_renders_latest_traces_and_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = WorkflowTraceRepository(Path(directory) / "calibration.db")
            trace = repository.start("Prueba")
            repository.finish()
            output = []
            controller = ConsoleCalibrationController(
                repository,
                InteractionCollector(),
                hotkey_source=FakeHotkey(),
                output=output.append,
            )
            controller.list()
            self.assertIn(trace.id, "\n".join(output))


if __name__ == "__main__":
    unittest.main()
