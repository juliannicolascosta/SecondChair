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

    title_lower = title.lower()
    application = "Desconocida"

    if "visual studio code" in title_lower or "vscode" in title_lower:
        application = "VS Code"

    elif "edge" in title_lower:
        application = "Edge"
        
    elif "chrome" in title_lower:
        application = "Chrome"

    elif "outlook" in title_lower:
        application = "Outlook"

    elif "whatsapp" in title_lower:
        application = "WhatsApp"

    elif "lex-doctor" in title_lower or "lex doctor" in title_lower or "lexdoctor" in title_lower:
        application = "Lex Doctor"

    return Event(
        application=application,
        title=title
    )