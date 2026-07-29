"""
Second Chair

Módulo:
Telemetry

Archivo:
analyzer.py

Responsabilidad:
Interpretar la información recibida desde Windows.
"""


def analyze_window(window):

    if window is None:
        return None

    title = window["title"]

    return {
        "title": title,
        "application": detect_application(title)
    }


def detect_application(title):

    title = title.lower()

    if "visual studio code" in title:
        return "VS Code"

    if "outlook" in title:
        return "Outlook"

    if "edge" in title:
        return "Edge"

    return "Desconocida"