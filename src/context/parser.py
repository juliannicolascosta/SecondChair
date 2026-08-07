"""
Second Chair

Módulo:
Context

Archivo:
parser.py

Responsabilidad:
Extraer información contextual desde
la ventana activa.
"""

import re


LEX_SECTIONS = (
    "Procesos", "Movimientos", "Agenda", "Facturas", "Edición de textos",
)


def parse_lex_title(title):
    """Extract structural Lex Doctor metadata already visible in the title."""
    context = {}
    title_lower = title.lower()
    for section in LEX_SECTIONS:
        if title_lower.startswith(section.lower()) or title_lower == section.lower():
            context["section"] = section
            break
    parts = re.split(r"\s[-~]\s", title, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        case_name = parts[1].strip()
        context["case"] = case_name
        actor = re.split(r"\s+C/", case_name, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        if actor:
            context["client"] = actor
    return context


def parse(event):

    context = {}

    application = event.application
    title = event.title

    # ---------------------------------------------------------
    # Lex Doctor
    # ---------------------------------------------------------

    if application == "Lex Doctor":
        context.update(parse_lex_title(title))

    # ---------------------------------------------------------
    # VS Code
    # ---------------------------------------------------------

    elif application == "VS Code":

        proyecto = title.split(" - ")[0].strip()

        context["project"] = proyecto

    # ---------------------------------------------------------
    # PDFs
    # ---------------------------------------------------------

    if title.lower().endswith(".pdf"):

        context["document"] = title

    return context
