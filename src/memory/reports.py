"""Console presentation for in-memory WorkSession objects."""

from src.analytics.reports import seconds_to_text


def sessions_summary(sessions, output=print):
    output("")
    output("=" * 40)
    output("RESUMEN DE SESIONES")
    output("=" * 40)

    if not sessions:
        output("")
        output("Sin sesiones")
        return

    for index, session in enumerate(sessions, start=1):
        label = (
            session.case
            or session.client
            or session.project
            or session.primary_application
            or "Sin contexto"
        )

        output("")
        output(f"Sesión {index}")
        output("")
        output(label)
        output("")
        output(seconds_to_text(session.duration))
        output("")

        for application in session.applications_used:
            output(application)

        output("")
        output(f"{session.events_count} eventos")
        output("")
        output("--------")
