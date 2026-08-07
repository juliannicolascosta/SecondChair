"""Passive, content-free continuity between a Lex matter and communications."""

from datetime import datetime


COMMUNICATION_APPLICATIONS = {"Outlook", "WhatsApp Business"}


def classify_communication(application, title):
    """Classify visible window state without reading message content."""

    normalized = (title or "").strip().casefold()
    if application == "WhatsApp Business":
        return "messaging_window"
    if application != "Outlook":
        return None
    if normalized.startswith(("re:", "responder", "reply")):
        return "email_reply"
    if normalized.startswith(("fw:", "rv:", "reenviar", "forward")):
        return "email_forward"
    if any(marker in normalized for marker in (
        "nuevo mensaje", "new message", "sin título - mensaje", "untitled - message",
    )):
        return "email_compose"
    return "email_window"


class ContextContinuity:
    """Keep a short-lived, unconfirmed Lex context for communication windows."""

    def __init__(self, timeout_seconds=300, clock=datetime.now):
        self.timeout_seconds = timeout_seconds
        self.clock = clock
        self._recent = None

    def apply(self, event):
        now = self.clock()
        if event.application == "Lex Doctor" and event.case:
            self._recent = {
                "client": event.client,
                "case": event.case,
                "observed_at": now,
            }
            return event

        activity = classify_communication(event.application, event.title)
        if activity is None:
            return event

        event.activity_type = activity
        if self._recent is None:
            return event
        age = (now - self._recent["observed_at"]).total_seconds()
        if age < 0 or age > self.timeout_seconds:
            self._recent = None
            return event

        event.client = event.client or self._recent["client"]
        event.case = event.case or self._recent["case"]
        event.context_source = "recent_lex_context"
        event.context_confidence = 0.60
        event.context_confirmed = False
        event.context.update({
            "client": event.client,
            "case": event.case,
            "activity_type": event.activity_type,
            "context_source": event.context_source,
            "context_confidence": event.context_confidence,
            "context_confirmed": event.context_confirmed,
        })
        return event
