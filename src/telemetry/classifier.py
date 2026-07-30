"""
Second Chair

Módulo:
Telemetry

Archivo:
classifier.py

Responsabilidad:
Clasificar la actividad observada.
"""


def classify(window):

    title = window["title"].lower()

    result = {
        "application": window["application"],
        "title": window["title"],
        "category": "General",
        "activity": "Trabajo"
    }

    # VS Code
    if window["application"] == "VS Code":
        result["category"] = "Desarrollo"

        if ".py" in title:
            result["activity"] = "Programación"
        elif ".md" in title:
            result["activity"] = "Documentación"

    # Outlook
    elif window["application"] == "Outlook":
        result["category"] = "Comunicación"
        result["activity"] = "Correo"

    # WhatsApp (App de Escritorio)
    elif window["application"] == "WhatsApp":
        result["category"] = "Comunicación"
        result["activity"] = "Mensajería"

    # Edge / Chrome
    elif window["application"] in ["Edge", "Chrome"]:
        result["category"] = "Web"

        if "chatgpt" in title or "gemini" in title:
            result["activity"] = "Asistencia IA"
            
        elif "github" in title:
            result["activity"] = "Desarrollo"

        elif "tribunal" in title or "poder judicial" in title or "autoconsulta" in title:
            result["activity"] = "Consulta Judicial"

        elif "whatsapp" in title:
            result["activity"] = "Mensajería"

        elif ".pdf" in title:
            result["activity"] = "Lectura"

        else:
            result["activity"] = "Navegación"

    # Lex Doctor
    elif window["application"] == "Lex Doctor" or "lex" in title:
        result["category"] = "Gestión Jurídica"

        if "procesos" in title:
            result["activity"] = "Gestión de Expedientes"

        elif "movimientos" in title:
            result["activity"] = "Consulta de Movimientos"

        elif "agenda" in title:
            result["activity"] = "Agenda"

        elif "facturas" in title:
            result["activity"] = "Facturación"

        else:
            result["activity"] = "Lex Doctor"

    return result