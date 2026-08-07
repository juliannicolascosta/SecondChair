"""Content-minimized rendering and comparison for workflow traces."""

from dataclasses import asdict


COMPARABLE_METRICS = (
    "duration", "window_count", "window_switches", "context_switches",
    "interaction_count", "mouse_clicks", "keyboard_actions", "scroll_actions",
    "text_fields_used", "buttons_used", "combo_boxes_used", "menus_used",
)


def anonymous_trace(trace):
    data = asdict(trace)
    data.pop("label", None)
    data["duration"] = trace.duration
    data["work_session_count"] = len(trace.work_session_ids)
    data.pop("work_session_ids", None)
    data["application_count"] = len(trace.applications_used)
    data["process_count"] = len(trace.processes_used)
    data.pop("processes_used", None)
    return data


def compare_traces(first, second):
    if first.label != second.label:
        raise ValueError("workflow trace labels must match")
    comparison = {}
    for name in COMPARABLE_METRICS:
        before, after = getattr(first, name), getattr(second, name)
        if before is None or after is None:
            comparison[name] = {"before": before, "after": after, "delta": None, "percent": None}
            continue
        delta = after - before
        percent = round(delta * 100 / before, 1) if before else None
        comparison[name] = {"before": before, "after": after, "delta": delta, "percent": percent}
    return comparison


def render_trace(trace, output=print):
    output(f"FLUJO: {trace.label}")
    output(f"Estado: {trace.status}")
    output(f"Duración: {trace.duration}s")
    output(f"WorkSessions: {len(trace.work_session_ids)}")
    output(f"Aplicaciones: {', '.join(trace.applications_used) or 'ninguna'}")
    output(f"Ventanas: {trace.window_count}")
    output(f"Cambios de ventana: {trace.window_switches}")
    output(f"Cambios de contexto: {trace.context_switches}")
    output(f"Interacciones: {trace.interaction_count}")
    output(f"Estado de interacciones: {trace.interaction_metrics_status}")
    output(f"Clics: {trace.mouse_clicks}")
    output(f"Teclado agregado: {trace.keyboard_actions}")
    output(f"Scroll: {trace.scroll_actions}")
    if trace.control_metrics_status == "unavailable":
        output("Controles UI: no disponibles")
    else:
        output(f"Campos de texto: {trace.text_fields_used}")
        output(f"Botones: {trace.buttons_used}")
        output(f"Desplegables: {trace.combo_boxes_used}")
        output(f"Menús: {trace.menus_used}")
    return trace
