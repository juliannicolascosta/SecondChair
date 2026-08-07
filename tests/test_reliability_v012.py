import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from src.analytics.export import anonymous_daily_report, render_anonymous_report
from src.analytics.reports import build_daily_summary, friction_report
from src.models.event import Event
from src.models.work_session import WorkSession
from src.storage.database import initialize, save_event, save_session_interactions
from src.telemetry.analyzer import analyze_window
from src.telemetry.interaction.ui_automation import UIAutomationInspector


DAY = date(2026, 8, 7)
START = datetime(2026, 8, 7, 9, 0, 0)


def session_with_status(status, reason=None):
    event = Event(
        application="Outlook", title="Sensitive inbox title",
        start_time=START, end_time=START + timedelta(seconds=60), duration=60,
        client="Secret Client", case="Secret Client C/ Secret Company",
    )
    session = WorkSession.from_event(1, event)
    session.control_metrics_status = status
    session.control_metrics_reason = reason
    return session


class ReliabilityV012Tests(unittest.TestCase):
    def test_ui_automation_missing_dependency_has_diagnostic_reason(self):
        inspector = UIAutomationInspector(automation_module=None)
        if not inspector.available:
            self.assertIsNotNone(inspector.reason)

    def test_unavailable_control_metrics_are_never_rendered_as_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "unavailable.db"
            initialize(database)
            save_session_interactions(
                session_with_status("unavailable", "dependency_not_installed"), database
            )
            output = []
            friction_report(DAY, database, output.append)
        self.assertIn("Campos de texto utilizados: no disponible", output)
        self.assertNotIn("Campos de texto utilizados: 0", output)
        self.assertIn("Diagnóstico UI Automation: dependency_not_installed", output)

    def test_available_real_zero_is_rendered_as_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "available.db"
            initialize(database)
            save_session_interactions(session_with_status("available"), database)
            output = []
            friction_report(DAY, database, output.append)
        self.assertIn("Campos de texto utilizados: 0", output)

    def test_window_application_context_and_case_switches_are_distinct(self):
        rows = [
            {"duration": 10, "application": "Lex Doctor", "title": "Procesos ~ Case A", "case_name": "Case A"},
            {"duration": 10, "application": "Lex Doctor", "title": "Movimientos ~ Case B", "case_name": "Case B"},
            {"duration": 10, "application": "Outlook", "title": "Inbox", "case_name": None},
        ]
        summary = build_daily_summary(rows, DAY)
        self.assertEqual(summary.window_switches, 2)
        self.assertEqual(summary.application_switches, 1)
        self.assertEqual(summary.context_changes, 2)
        self.assertEqual(summary.distinct_cases, 2)
        self.assertEqual(summary.case_switches, 1)

    def test_allowed_metadata_recognizes_priority_applications(self):
        fixtures = (
            ("(2) WhatsApp Business - Edge", "msedge.exe", "WhatsApp Business"),
            ("Autoconsulta Web", "msedge.exe", "SISFE / Autoconsulta Web"),
            ("ARCA - Clave Fiscal", "msedge.exe", "ARCA"),
            ("Superintendencia de Riesgos del Trabajo - eServicios", "msedge.exe", "SRT"),
            ("ChatGPT", "msedge.exe", "ChatGPT"),
            ("Procesos ~ Actor C/ Demandado", "Lex-Doctor-11.exe", "Lex Doctor"),
            ("Document.docx - Word", "WINWORD.EXE", "Word"),
        )
        for title, process, expected in fixtures:
            with self.subTest(expected=expected):
                self.assertEqual(
                    analyze_window({"title": title, "process_name": process}).application,
                    expected,
                )

    def test_lex_auxiliary_window_requires_immediate_lex_evidence(self):
        window = {"title": "Procesos ~ Actor C/ Demandado", "process_name": None}
        self.assertEqual(analyze_window(window).application, "Desconocida")
        self.assertEqual(
            analyze_window(window, previous_application="Lex Doctor").application,
            "Lex Doctor",
        )

    def test_chatgpt_desktop_process_is_recognized(self):
        event = analyze_window({"title": "ChatGPT", "process_name": "ChatGPT.exe"})
        self.assertEqual(event.application, "ChatGPT")
        title_fallback = analyze_window({"title": "ChatGPT", "process_name": None})
        self.assertEqual(title_fallback.application, "ChatGPT")

    def test_exportable_report_cannot_leak_identity(self):
        forbidden = (
            "Secret Client", "Secret Company", "sensitive@example.com", "+54 11 1234",
        )
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "anonymous.db"
            initialize(database)
            save_event(
                "2026-08-07 09:00:00", "2026-08-07 09:01:00", 60,
                "Outlook", "sensitive@example.com +54 11 1234",
                client="Secret Client", case_name="Secret Client C/ Secret Company",
                document="C:/Secret Client/private.pdf", database=database,
            )
            save_session_interactions(session_with_status("unavailable"), database)
            report = anonymous_daily_report(DAY, database)
            output = []
            render_anonymous_report(report, output.append)
            rendered = "\n".join(output) + str(report.as_dict())
        for sensitive in forbidden:
            self.assertNotIn(sensitive, rendered)
        self.assertEqual(report.distinct_cases, 1)
        self.assertIsNone(report.text_fields_used)


if __name__ == "__main__":
    unittest.main()
