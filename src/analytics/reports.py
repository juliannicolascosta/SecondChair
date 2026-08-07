"""Daily activity summaries built from persisted telemetry facts."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from src.analytics.queries import (
    events_for_date,
    idle_metrics_for_date,
    interaction_sessions_for_date,
)
from src.storage.database import INTERACTION_COLUMNS
from src.storage.database import DATABASE


@dataclass(frozen=True)
class DailySummary:
    day: date
    total_seconds: int
    by_application: dict[str, int]
    by_case: dict[str, int]
    by_client: dict[str, int]
    context_changes: int


@dataclass(frozen=True)
class DailyFrictionSummary:
    day: date
    total_seconds: int
    totals: dict[str, int]
    sessions: list[dict]


def seconds_to_text(seconds):
    seconds = max(0, int(seconds or 0))

    if seconds < 60:
        return f"{seconds}s"

    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def _context_key(row):
    """Represent the operational context without using the window title."""

    return (
        row.get("application"),
        row.get("client"),
        row.get("case_name"),
        row.get("section"),
        row.get("project"),
        row.get("document"),
    )


def build_daily_summary(rows, day):
    applications = defaultdict(int)
    cases = defaultdict(int)
    clients = defaultdict(int)
    total = 0
    context_changes = 0
    previous_context = None

    for row in rows:
        duration = max(0, int(row.get("duration") or 0))
        application = row.get("application") or "Desconocida"
        case_name = row.get("case_name")
        client = row.get("client")

        total += duration
        applications[application] += duration

        if case_name:
            cases[case_name] += duration

        if client:
            clients[client] += duration

        current_context = _context_key(row)
        if previous_context is not None and current_context != previous_context:
            context_changes += 1
        previous_context = current_context

    sort_totals = lambda values: dict(
        sorted(values.items(), key=lambda item: (-item[1], item[0]))
    )

    return DailySummary(
        day=day,
        total_seconds=total,
        by_application=sort_totals(applications),
        by_case=sort_totals(cases),
        by_client=sort_totals(clients),
        context_changes=context_changes,
    )


def daily_summary(day=None, database=DATABASE):
    selected_day = day or date.today()
    return build_daily_summary(
        events_for_date(selected_day, database),
        selected_day,
    )


def _print_group(title, values, output):
    output("")
    output(title)
    output("")

    if not values:
        output("Sin datos")
        return

    for label, seconds in values.items():
        output(f"{label:<45} {seconds_to_text(seconds)}")


def today_summary(database=DATABASE, output=print):
    summary = daily_summary(database=database)
    idle = idle_metrics_for_date(database=database)

    output("")
    output("=" * 60)
    output("SECOND CHAIR")
    output(f"Resumen diario — {summary.day.isoformat()}")
    output("=" * 60)
    output("")
    output(
        "Tiempo total de ventanas (incluye posibles pausas históricas): "
        f"{seconds_to_text(summary.total_seconds)}"
    )
    output(f"Tiempo activo medido: {seconds_to_text(idle['active_seconds'])}")
    output(f"Tiempo inactivo medido: {seconds_to_text(idle['inactive_seconds'])}")
    output(f"Cambios de contexto: {summary.context_changes}")

    _print_group("Aplicaciones", summary.by_application, output)
    _print_group("Expedientes", summary.by_case, output)
    _print_group("Clientes", summary.by_client, output)

    output("")
    output("=" * 60)

    return summary


def build_daily_friction_summary(rows, day):
    totals = {name: 0 for name in INTERACTION_COLUMNS}
    for row in rows:
        for name in totals:
            totals[name] += max(0, int(row.get(name) or 0))
    sessions = sorted(
        rows,
        key=lambda row: (-int(row.get("interaction_count") or 0), row.get("start_time", "")),
    )
    return DailyFrictionSummary(
        day=day,
        total_seconds=sum(max(0, int(row.get("duration") or 0)) for row in rows),
        totals=totals,
        sessions=sessions,
    )


def daily_friction_summary(day=None, database=DATABASE):
    selected_day = day or date.today()
    return build_daily_friction_summary(
        interaction_sessions_for_date(selected_day, database),
        selected_day,
    )


def friction_report(day=None, database=DATABASE, output=print):
    summary = daily_friction_summary(day, database)
    totals = summary.totals
    output("")
    output("=" * 40)
    output("FRICCIÓN DEL DÍA")
    output("=" * 40)
    output("")
    output(f"Tiempo observado: {seconds_to_text(summary.total_seconds)}")
    output("")
    labels = (
        ("Interacciones totales", "interaction_count"),
        ("Clics", "mouse_clicks"),
        ("Actividad de teclado", "keyboard_actions"),
        ("Scroll", "scroll_actions"),
        ("Campos de texto utilizados", "text_fields_used"),
        ("Botones", "buttons_used"),
        ("Desplegables", "combo_boxes_used"),
        ("Menús", "menus_used"),
        ("Cambios de ventana", "window_switches"),
    )
    for label, name in labels:
        output(f"{label}: {totals[name]:,}".replace(",", "."))
    output("")
    output("Sesiones con mayor fricción:")
    if not summary.sessions:
        output("Sin sesiones")
    for index, session in enumerate(summary.sessions[:5], start=1):
        output("")
        output(f"{index}. {session.get('label') or 'Sin contexto'}")
        output(f"   {session['mouse_clicks']} clics")
        output(f"   {session['text_fields_used']} campos")
        output(f"   {session['combo_boxes_used']} desplegables")
        output(f"   {seconds_to_text(session['duration'])}")
    return summary
