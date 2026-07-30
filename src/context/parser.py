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


def parse(event):

    context = {}

    application = event.application
    title = event.title

    # ---------------------------------------------------------
    # Lex Doctor
    # ---------------------------------------------------------

    if application == "Lex Doctor":

        if "Procesos" in title:
            context["section"] = "Procesos"

        elif "Movimientos" in title:
            context["section"] = "Movimientos"

        partes = re.split(r"\s[-~]\s", title)

        if len(partes) >= 2:

            expediente = partes[-1].strip()

            context["case"] = expediente

            actor = expediente.split(" C/")[0].strip()

            context["client"] = actor

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