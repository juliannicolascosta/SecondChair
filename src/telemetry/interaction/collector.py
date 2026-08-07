"""Non-blocking, content-free interaction collection and session aggregation."""

from collections import deque
from datetime import datetime
from threading import Lock

from src.telemetry.interaction.counters import InteractionCounters
from src.telemetry.interaction.models import InteractionEvent, InteractionType


CONTROL_INTERACTIONS = {
    "text_field": InteractionType.TEXT_FIELD,
    "button": InteractionType.BUTTON,
    "combo_box": InteractionType.COMBO_BOX,
    "menu": InteractionType.MENU,
    "other_control": InteractionType.OTHER_CONTROL,
}


class InteractionCollector:
    """Keeps bounded detail in memory and persists only session aggregates."""

    def __init__(
        self,
        event_source=None,
        ui_inspector=None,
        window_provider=None,
        clock=datetime.now,
        max_events=10000,
    ):
        self.event_source = event_source
        self.ui_inspector = ui_inspector
        self.window_provider = window_provider or (lambda: {})
        self.clock = clock
        self.events = deque(maxlen=max_events)
        self.counters = InteractionCounters()
        self.running = False
        self._lock = Lock()
        self._last_window = None

    def start(self):
        if self.running:
            return
        self.running = True
        if self.event_source is not None:
            self.event_source.start(self._receive)

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.event_source is not None:
            self.event_source.stop()

    def _receive(self, kind):
        if not self.running:
            return
        self.record(kind)

    def record(self, kind, *, window=None, timestamp=None):
        """Record only the fact that an action occurred, never its payload."""

        kind = InteractionType(kind)
        window = dict(window or self.window_provider() or {})
        control_type = None
        control_metrics_status = "unavailable"
        control_metrics_reason = "not_configured"
        physical_click = kind == InteractionType.MOUSE_CLICK
        if physical_click and self.ui_inspector is not None:
            control_type, control_metrics_status, control_metrics_reason = (
                self.ui_inspector.classify_at_cursor()
            )
            kind = CONTROL_INTERACTIONS.get(control_type, kind)

        event = InteractionEvent(
            timestamp=timestamp or self.clock(),
            interaction_type=kind,
            application=window.get("application"),
            process_name=window.get("process_name"),
            window_title=window.get("title"),
            control_type=control_type,
            control_metrics_status=control_metrics_status,
            control_metrics_reason=control_metrics_reason,
        )
        window_key = (event.process_name, event.window_title)
        with self._lock:
            if self._last_window is not None and window_key != self._last_window:
                self.counters.add_window_switch()
            if any(window_key):
                self._last_window = window_key
            self.events.append(event)
            self.counters.record(event, physical_click=physical_click)
        return event

    def attach_to_session(self, session):
        """Aggregate ephemeral events whose timestamps fall inside a closed session."""

        aggregate = InteractionCounters()
        with self._lock:
            matched = []
            retained = deque(maxlen=self.events.maxlen)
            for event in self.events:
                if session.start_time <= event.timestamp <= session.end_time:
                    matched.append(event)
                else:
                    retained.append(event)
            self.events = retained

        previous_window = None
        click_statuses = []
        reasons = []
        for event in matched:
            physical_click = event.interaction_type not in {
                InteractionType.KEYBOARD_ACTIVITY,
                InteractionType.SCROLL,
            }
            aggregate.record(event, physical_click=physical_click)
            if physical_click:
                click_statuses.append(event.control_metrics_status)
                if event.control_metrics_reason:
                    reasons.append(event.control_metrics_reason)
            window_key = (event.process_name, event.window_title)
            if previous_window is not None and window_key != previous_window:
                aggregate.add_window_switch()
            if any(window_key):
                previous_window = window_key
        session.apply_interaction_counters(aggregate)
        if self.ui_inspector is None or not self.ui_inspector.available:
            session.control_metrics_status = "unavailable"
            session.control_metrics_reason = (
                getattr(self.ui_inspector, "reason", None) or "not_configured"
            )
        elif click_statuses and all(status == "available" for status in click_statuses):
            session.control_metrics_status = "available"
            session.control_metrics_reason = None
        elif "available" in click_statuses:
            session.control_metrics_status = "partial"
            session.control_metrics_reason = reasons[0] if reasons else "classification_partial"
        elif click_statuses:
            session.control_metrics_status = "unavailable"
            session.control_metrics_reason = reasons[0] if reasons else "classification_failed"
        else:
            session.control_metrics_status = "available"
            session.control_metrics_reason = None
        return aggregate
