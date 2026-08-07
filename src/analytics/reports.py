"""Daily activity summaries built from persisted telemetry facts."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from hashlib import sha256

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
    window_switches: int
    application_switches: int
    distinct_applications: int
    distinct_cases: int
    case_switches: int
    recognized_application_seconds: int
    contextualized_seconds: int
    communication_windows: int
    inferred_communication_windows: int


@dataclass(frozen=True)
class DailyFrictionSummary:
    day: date
    total_seconds: int
    totals: dict[str, int]
    sessions: list[dict]
    control_metrics_status: str = "unavailable"
    control_metrics_reason: str | None = None


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
    previous_window = None
    previous_application = None
    last_case = None
    case_ids = set()
    window_switches = 0
    application_switches = 0
    case_switches = 0
    recognized_application_seconds = 0
    contextualized_seconds = 0
    communication_windows = 0
    inferred_communication_windows = 0

    for row in rows:
        duration = max(0, int(row.get("duration") or 0))
        application = row.get("application") or "Desconocida"
        case_name = row.get("case_name")
        client = row.get("client")
        case_id = (
            sha256(case_name.strip().casefold().encode("utf-8")).hexdigest()
            if case_name else None
        )

        total += duration
        applications[application] += duration
        if application != "Desconocida":
            recognized_application_seconds += duration
        if any((case_name, client, row.get("section"), row.get("project"), row.get("document"))):
            contextualized_seconds += duration
        if row.get("activity_type"):
            communication_windows += 1
            if row.get("context_source") == "recent_lex_context":
                inferred_communication_windows += 1

        if case_name:
            cases[case_name] += duration
            case_ids.add(case_id)
            if last_case is not None and case_id != last_case:
                case_switches += 1
            last_case = case_id

        if client:
            clients[client] += duration

        current_context = _context_key(row)
        if previous_context is not None and current_context != previous_context:
            context_changes += 1
        previous_context = current_context

        current_window = (application, row.get("title"))
        if previous_window is not None and current_window != previous_window:
            window_switches += 1
        previous_window = current_window
        if previous_application is not None and application != previous_application:
            application_switches += 1
        previous_application = application

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
        window_switches=window_switches,
        application_switches=application_switches,
        distinct_applications=len(applications),
        distinct_cases=len(case_ids),
        case_switches=case_switches,
        recognized_application_seconds=recognized_application_seconds,
        contextualized_seconds=contextualized_seconds,
        communication_windows=communication_windows,
        inferred_communication_windows=inferred_communication_windows,
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


def percentage(part, total):
    return round((part / total) * 100, 1) if total else 0.0


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
    output(f"Cambios de ventana activa: {summary.window_switches}")
    output(f"Cambios de aplicación: {summary.application_switches}")
    output(f"Cambios de contexto significativo: {summary.context_changes}")
    output(f"Aplicaciones distintas: {summary.distinct_applications}")
    output(f"Expedientes distintos: {summary.distinct_cases}")
    output(f"Cambios entre expedientes: {summary.case_switches}")
    output(
        "Cobertura de aplicación reconocida: "
        f"{percentage(summary.recognized_application_seconds, summary.total_seconds):.1f}%"
    )
    output(
        "Cobertura de contexto reconocido: "
        f"{percentage(summary.contextualized_seconds, summary.total_seconds):.1f}%"
    )
    output(f"Ventanas de comunicación observadas: {summary.communication_windows}")
    output(
        "Comunicaciones asociadas por continuidad (no confirmadas): "
        f"{summary.inferred_communication_windows}"
    )

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
    statuses = [row.get("control_metrics_status", "unavailable") for row in rows]
    if statuses and all(status == "available" for status in statuses):
        control_status = "available"
    elif "available" in statuses or "partial" in statuses:
        control_status = "partial"
    else:
        control_status = "unavailable"
    reason = next(
        (row.get("control_metrics_reason") for row in rows if row.get("control_metrics_reason")),
        None,
    )
    return DailyFrictionSummary(
        day=day,
        total_seconds=sum(max(0, int(row.get("duration") or 0)) for row in rows),
        totals=totals,
        sessions=sessions,
        control_metrics_status=control_status,
        control_metrics_reason=reason,
    )


def daily_friction_summary(day=None, database=DATABASE):
    selected_day = day or date.today()
    result = build_daily_friction_summary(
        interaction_sessions_for_date(selected_day, database),
        selected_day,
    )
    result.totals["window_switches"] = daily_summary(selected_day, database).window_switches
    return result


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
    basic_labels = (
        ("Interacciones totales", "interaction_count"),
        ("Clics", "mouse_clicks"),
        ("Actividad de teclado", "keyboard_actions"),
        ("Scroll", "scroll_actions"),
    )
    control_labels = (
        ("Campos de texto utilizados", "text_fields_used"),
        ("Botones", "buttons_used"),
        ("Desplegables", "combo_boxes_used"),
        ("Menús", "menus_used"),
    )
    for label, name in basic_labels:
        output(f"{label}: {totals[name]:,}".replace(",", "."))
    for label, name in control_labels:
        if summary.control_metrics_status == "unavailable":
            output(f"{label}: no disponible")
        else:
            suffix = " (medición parcial)" if summary.control_metrics_status == "partial" else ""
            output(f"{label}: {totals[name]:,}{suffix}".replace(",", "."))
    output(f"Cambios de ventana activa: {totals['window_switches']:,}".replace(",", "."))
    if summary.control_metrics_status != "available" and summary.control_metrics_reason:
        output(f"Diagnóstico UI Automation: {summary.control_metrics_reason}")
    output("")
    output("Sesiones con mayor fricción:")
    if not summary.sessions:
        output("Sin sesiones")
    for index, session in enumerate(summary.sessions[:5], start=1):
        output("")
        output(f"{index}. {session.get('label') or 'Sin contexto'}")
        output(f"   {session['mouse_clicks']} clics")
        if session.get("control_metrics_status") == "available":
            output(f"   {session['text_fields_used']} campos")
            output(f"   {session['combo_boxes_used']} desplegables")
        else:
            output("   controles UI: no disponibles")
        output(f"   {seconds_to_text(session['duration'])}")
    return summary
