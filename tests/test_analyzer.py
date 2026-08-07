import unittest

from src.telemetry.analyzer import analyze_window


class AnalyzerTests(unittest.TestCase):
    def test_process_metadata_identifies_word(self):
        event = analyze_window({
            "title": "PODER ESPECIAL ART.docx - Word",
            "process_name": "WINWORD.EXE",
        })
        self.assertEqual(event.application, "Word")

    def test_process_metadata_identifies_file_explorer(self):
        event = analyze_window({
            "title": "Clientes",
            "process_name": "explorer.exe",
        })
        self.assertEqual(event.application, "Explorador de archivos")

    def test_title_fallback_remains_compatible(self):
        event = analyze_window({"title": "Inbox - Outlook"})
        self.assertEqual(event.application, "Outlook")


if __name__ == "__main__":
    unittest.main()
