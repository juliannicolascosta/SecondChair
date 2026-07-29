"""
Second Chair

Módulo:
Telemetry

Archivo:
analyzer.py

Responsabilidad:
Analizar la ventana activa.
"""

from models.event import Event


def analyze_window(window):

    if window is None:

        return None

    title = window.get("title", "").strip()

    if not title:

        return None

    application = "Desconocida"

    if "Visual Studio Code" in title:

        application = "VS Code"

    elif "Microsoft Edge" in title:

        application = "Edge"

    elif "Outlook" in title:

        application = "Outlook"

    elif "WhatsApp" in title:

        application = "WhatsApp"

    elif "Lex-Doctor" in title:

        application = "Lex Doctor"

    return Event(

        application=application,

        title=title

    )