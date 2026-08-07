"""Rule-based grouping of completed events into WorkSession objects."""

from src.models.work_session import WorkSession


class SessionBuilder:
    def __init__(self, inactivity_seconds=600):
        self.inactivity_seconds = inactivity_seconds
        self.current_session = None
        self._next_id = 1

    def add_event(self, event):
        if event.start_time is None or event.end_time is None:
            raise ValueError("SessionBuilder requires a completed event")

        closed_session = None

        if self.current_session is None:
            self.current_session = self._new_session(event)
        elif self._must_close(event):
            closed_session = self.current_session
            self.current_session = self._new_session(event)
        else:
            self.current_session.add_event(event)

        return closed_session

    def finish(self):
        closed_session = self.current_session
        self.current_session = None
        return closed_session

    def _new_session(self, event):
        session = WorkSession.from_event(self._next_id, event)
        self._next_id += 1
        return session

    def _must_close(self, event):
        session = self.current_session
        inactivity = (event.start_time - session.end_time).total_seconds()

        if inactivity > self.inactivity_seconds:
            return True

        if session.case and event.case and session.case != event.case:
            return True

        if self._first_anchor_follows_other_applications(session, event):
            return True

        return self._context_changed_completely(session, event)

    @staticmethod
    def _first_anchor_follows_other_applications(session, event):
        """Do not retroactively attach unrelated setup activity to a new matter."""

        session_has_anchor = any((session.client, session.case, session.project))
        event_has_anchor = any((event.client, event.case, event.project))
        if session_has_anchor or not event_has_anchor:
            return False
        return any(
            existing.application != event.application
            for existing in session.events
        )

    @staticmethod
    def _context_changed_completely(session, event):
        current = {
            ("client", session.client),
            ("case", session.case),
            ("project", session.project),
        }
        incoming = {
            ("client", event.client),
            ("case", event.case),
            ("project", event.project),
        }
        current = {anchor for anchor in current if anchor[1]}
        incoming = {anchor for anchor in incoming if anchor[1]}

        return bool(current and incoming and current.isdisjoint(incoming))
