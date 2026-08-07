"""Best-effort Windows UI Automation classification without reading control data."""

CONTROL_MAP = {
    "EditControl": "text_field",
    "DocumentControl": "text_field",
    "ButtonControl": "button",
    "ComboBoxControl": "combo_box",
    "MenuItemControl": "menu",
    "MenuControl": "menu",
    "CheckBoxControl": "other_control",
    "RadioButtonControl": "other_control",
    "ListControl": "other_control",
    "TreeControl": "other_control",
    "TabControl": "other_control",
    "HyperlinkControl": "other_control",
}


class UIAutomationInspector:
    """Optional adapter. Names, values and patterns are never requested."""

    def __init__(self, automation_module=None):
        if automation_module is None:
            try:
                import uiautomation as automation_module
            except (ImportError, OSError):
                automation_module = None
        self.automation = automation_module

    def control_type_at_cursor(self):
        if self.automation is None:
            return None
        try:
            control = self.automation.ControlFromCursor()
            return CONTROL_MAP.get(control.ControlTypeName, "other_control")
        except Exception:
            return None
