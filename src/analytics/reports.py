"""
Second Chair

Módulo:
Analytics

Archivo:
reports.py

Responsabilidad:
Construir reportes de actividad.
"""

from collections import defaultdict

from src.analytics.queries import events_today


def seconds_to_text(seconds):

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours:

        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def today_summary():

    rows = events_today()

    applications = defaultdict(int)

    matters = defaultdict(int)

    for row in rows:

        application = row[0]
        duration = row[2]

        client = row[4]
        case_name = row[5]

        applications[application] += duration

        if client and case_name:

            key = f"{client} — {case_name}"

            matters[key] += duration

    print()

    print("=" * 60)

    print("SECOND CHAIR")
    print("Resumen del día")

    print("=" * 60)

    print()

    print("Aplicaciones")

    print()

    for app, seconds in sorted(

        applications.items(),

        key=lambda x: x[1],

        reverse=True

    ):

        print(

            f"{app:<20} {seconds_to_text(seconds)}"

        )

    print()

    print("Expedientes")

    print()

    for matter, seconds in sorted(

        matters.items(),

        key=lambda x: x[1],

        reverse=True

    ):

        print(

            f"{matter:<45} {seconds_to_text(seconds)}"

        )

    print()

    print("=" * 60)