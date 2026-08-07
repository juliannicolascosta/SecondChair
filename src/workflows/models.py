"""Aggregate representation of a manually delimited workflow."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkflowTrace:
    id: str
    label: str
    start_time: datetime
    end_time: datetime | None
    status: str
    work_session_ids: tuple[str, ...] = ()
    applications_used: tuple[str, ...] = ()
    processes_used: tuple[str, ...] = ()
    window_count: int = 0
    context_switches: int = 0
    interaction_count: int = 0
    mouse_clicks: int = 0
    keyboard_actions: int = 0
    scroll_actions: int = 0
    text_fields_used: int | None = None
    buttons_used: int | None = None
    combo_boxes_used: int | None = None
    menus_used: int | None = None
    window_switches: int = 0
    control_metrics_status: str = "unavailable"
    interaction_metrics_status: str = "pending"

    @property
    def duration(self):
        if self.end_time is None:
            return 0
        return max(0, int((self.end_time - self.start_time).total_seconds()))
