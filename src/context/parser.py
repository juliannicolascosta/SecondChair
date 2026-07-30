"""
Second Chair

Módulo:
Context

Archivo:
parser.py

Responsabilidad:
Extraer información útil desde títulos de ventanas.
"""

import re


def extract_case(title):

    pattern = r"(.+?)\s+c/\s+(.+)"

    match = re.search(
        pattern,
        title,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(0)

    return None


def extract_pdf(title):

    if ".pdf" in title.lower():
        return title

    return None