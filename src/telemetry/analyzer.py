"""
Second Chair

Módulo:
Telemetry

Archivo:
analyzer.py

Responsabilidad:
Analizar la ventana activa.
"""

from src.models.event import Event


PROCESS_APPLICATIONS = {
    "msedge": "Edge",
    "chrome": "Chrome",
    "outlook": "Outlook",
    "olk": "Outlook",
    "winword": "Word",
    "excel": "Excel",
    "powerpnt": "PowerPoint",
    "explorer": "Explorador de archivos",
    "powershell": "PowerShell",
    "pwsh": "PowerShell",
    "code": "VS Code",
    "xolidosign": "XolidoSign",
    "lexdoctor": "Lex Doctor",
}


def _application_from_process(window):
    process = (window.get("process_name") or window.get("application") or "")
    normalized = process.lower().removesuffix(".exe")
    return PROCESS_APPLICATIONS.get(normalized)


def analyze_window(window):

    if window is None:
        return None

    title = window.get("title", "").strip()

    if not title:
        return None

    title_lower = title.lower()
    application = _application_from_process(window) or "Desconocida"

    if application != "Desconocida":
        pass

    elif "visual studio code" in title_lower or "vscode" in title_lower:
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

    elif title_lower.endswith(" - word"):
        application = "Word"

    elif "windows powershell" in title_lower:
        application = "PowerShell"

    return Event(
        application=application,
        title=title,
    )
