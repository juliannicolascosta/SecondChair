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
        self.reason = None
        if automation_module is None:
            try:
                import uiautomation as automation_module
            except ModuleNotFoundError:
                self.reason = "dependency_not_installed"
                automation_module = None
            except (ImportError, OSError) as error:
                self.reason = f"initialization_{type(error).__name__}"
                automation_module = None
        self.automation = automation_module

    @property
    def available(self):
        return self.automation is not None

    def control_type_at_cursor(self):
        if self.automation is None:
            return None
        try:
            control = self.automation.ControlFromCursor()
            return CONTROL_MAP.get(control.ControlTypeName, "other_control")
        except Exception as error:
            self.reason = f"runtime_{type(error).__name__}"
            return None

    def classify_at_cursor(self):
        if not self.available:
            return None, "unavailable", self.reason or "not_configured"
        control_type = self.control_type_at_cursor()
        if control_type is None:
            return None, "unavailable", self.reason or "classification_failed"
        return control_type, "available", None
