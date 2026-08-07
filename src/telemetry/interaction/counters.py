"""Counter semantics for interaction events."""

from dataclasses import asdict, dataclass

from src.telemetry.interaction.models import InteractionType


CONTROL_TYPES = {
    InteractionType.TEXT_FIELD: "text_fields_used",
    InteractionType.BUTTON: "buttons_used",
    InteractionType.COMBO_BOX: "combo_boxes_used",
    InteractionType.MENU: "menus_used",
}


@dataclass
class InteractionCounters:
    interaction_count: int = 0
    mouse_clicks: int = 0
    keyboard_actions: int = 0
    scroll_actions: int = 0
    text_fields_used: int = 0
    buttons_used: int = 0
    combo_boxes_used: int = 0
    menus_used: int = 0
    other_controls_used: int = 0
    window_switches: int = 0

    def record(self, event, *, physical_click=False):
        """Count one action; its control classification never adds another action."""

        kind = InteractionType(event.interaction_type)
        self.interaction_count += 1
        if physical_click or kind == InteractionType.MOUSE_CLICK:
            self.mouse_clicks += 1
        if kind == InteractionType.KEYBOARD_ACTIVITY:
            self.keyboard_actions += 1
        elif kind == InteractionType.SCROLL:
            self.scroll_actions += 1
        elif kind in CONTROL_TYPES:
            setattr(self, CONTROL_TYPES[kind], getattr(self, CONTROL_TYPES[kind]) + 1)
        elif kind == InteractionType.OTHER_CONTROL:
            self.other_controls_used += 1

    def add_window_switch(self):
        self.window_switches += 1

    def merge(self, other):
        for name, value in asdict(other).items():
            setattr(self, name, getattr(self, name) + value)
        return self

    def as_dict(self):
        return asdict(self)
