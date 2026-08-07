"""Externally shareable daily report with an explicit anonymization contract."""

from dataclasses import asdict, dataclass
from datetime import date

from src.analytics.reports import (
    daily_friction_summary, daily_summary, percentage, seconds_to_text,
)
from src.storage.database import DATABASE


@dataclass(frozen=True)
class AnonymousDailyReport:
    day: str
    total_seconds: int
    application_seconds: dict[str, int]
    distinct_applications: int
    window_switches: int
    application_switches: int
    context_switches: int
    distinct_cases: int
    case_switches: int
    work_sessions: int
    work_session_seconds: int
    unassociated_seconds: int
    recognized_application_percent: float
    contextualized_percent: float
    communication_windows: int
    inferred_communication_windows: int
    interaction_count: int
    mouse_clicks: int
    keyboard_actions: int
    scroll_actions: int
    control_metrics_status: str
    text_fields_used: int | None
    buttons_used: int | None
    combo_boxes_used: int | None
    menus_used: int | None

    def as_dict(self):
        return asdict(self)


def anonymous_daily_report(day=None, database=DATABASE):
    selected_day = day or date.today()
    activity = daily_summary(selected_day, database)
    friction = daily_friction_summary(selected_day, database)
    controls_measured = friction.control_metrics_status != "unavailable"
    totals = friction.totals
    return AnonymousDailyReport(
        day=selected_day.isoformat(),
        total_seconds=activity.total_seconds,
        application_seconds=dict(activity.by_application),
        distinct_applications=activity.distinct_applications,
        window_switches=activity.window_switches,
        application_switches=activity.application_switches,
        context_switches=activity.context_changes,
        distinct_cases=activity.distinct_cases,
        case_switches=activity.case_switches,
        work_sessions=len(friction.sessions),
        work_session_seconds=friction.total_seconds,
        unassociated_seconds=max(0, activity.total_seconds - friction.total_seconds),
        recognized_application_percent=percentage(
            activity.recognized_application_seconds, activity.total_seconds
        ),
        contextualized_percent=percentage(
            activity.contextualized_seconds, activity.total_seconds
        ),
        communication_windows=activity.communication_windows,
        inferred_communication_windows=activity.inferred_communication_windows,
        interaction_count=totals["interaction_count"],
        mouse_clicks=totals["mouse_clicks"],
        keyboard_actions=totals["keyboard_actions"],
        scroll_actions=totals["scroll_actions"],
        control_metrics_status=friction.control_metrics_status,
        text_fields_used=totals["text_fields_used"] if controls_measured else None,
        buttons_used=totals["buttons_used"] if controls_measured else None,
        combo_boxes_used=totals["combo_boxes_used"] if controls_measured else None,
        menus_used=totals["menus_used"] if controls_measured else None,
    )


def render_anonymous_report(report, output=print):
    output("=" * 48)
    output("SECOND CHAIR — REPORTE ANONIMIZADO")
    output("=" * 48)
    output(f"Fecha: {report.day}")
    output(f"Tiempo observado: {seconds_to_text(report.total_seconds)}")
    output(f"Aplicaciones distintas: {report.distinct_applications}")
    for application, seconds in report.application_seconds.items():
        output(f"  {application}: {seconds_to_text(seconds)}")
    output(f"Cambios de ventana activa: {report.window_switches}")
    output(f"Cambios de aplicación: {report.application_switches}")
    output(f"Cambios de contexto significativo: {report.context_switches}")
    output(f"Expedientes distintos: {report.distinct_cases}")
    output(f"Cambios entre expedientes: {report.case_switches}")
    output(f"WorkSessions: {report.work_sessions}")
    output(f"Duración de WorkSessions: {seconds_to_text(report.work_session_seconds)}")
    output(f"Tiempo no asociado a WorkSessions: {seconds_to_text(report.unassociated_seconds)}")
    output(f"Cobertura de aplicación reconocida: {report.recognized_application_percent:.1f}%")
    output(f"Cobertura de contexto reconocido: {report.contextualized_percent:.1f}%")
    output(f"Ventanas de comunicación observadas: {report.communication_windows}")
    output(
        "Comunicaciones asociadas por continuidad: "
        f"{report.inferred_communication_windows}"
    )
    output(f"Interacciones: {report.interaction_count}")
    output(f"Clics: {report.mouse_clicks}")
    output(f"Actividad de teclado: {report.keyboard_actions}")
    output(f"Scroll: {report.scroll_actions}")
    if report.control_metrics_status == "unavailable":
        output("Controles UI: no disponibles")
    else:
        output(f"Campos de texto: {report.text_fields_used}")
        output(f"Botones: {report.buttons_used}")
        output(f"Desplegables: {report.combo_boxes_used}")
        output(f"Menús: {report.menus_used}")
        if report.control_metrics_status == "partial":
            output("Cobertura de controles UI: parcial")
    return report
