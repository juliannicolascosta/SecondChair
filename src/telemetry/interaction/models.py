"""Content-free facts produced by interaction telemetry."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class InteractionType(str, Enum):
    MOUSE_CLICK = "mouse_click"
    KEYBOARD_ACTIVITY = "keyboard_activity"
    SCROLL = "scroll"
    BUTTON = "button"
    TEXT_FIELD = "text_field"
    COMBO_BOX = "combo_box"
    MENU = "menu"
    OTHER_CONTROL = "other_control"


@dataclass(frozen=True)
class InteractionEvent:
    """An ephemeral interaction fact. It deliberately has no content/value field."""

    timestamp: datetime
    interaction_type: InteractionType
    application: str | None = None
    process_name: str | None = None
    window_title: str | None = None
    control_type: str | None = None
    control_metrics_status: str = "unavailable"
    control_metrics_reason: str | None = None
    session_id: int | None = None

    def __post_init__(self):
        object.__setattr__(
            self,
            "interaction_type",
            InteractionType(self.interaction_type),
        )
