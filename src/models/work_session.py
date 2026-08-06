"""In-memory representation of one continuous intellectual task."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from src.models.event import Event


@dataclass
class WorkSession:
    id: int
    start_time: datetime
    end_time: datetime
    duration: int = 0
    client: str | None = None
    case: str | None = None
    project: str | None = None
    primary_application: str | None = None
    applications_used: list[str] = field(default_factory=list)
    context_switches: int = 0
    events_count: int = 0
    events: list[Event] = field(default_factory=list, repr=False)
    _application_seconds: dict[str, int] = field(
        default_factory=lambda: defaultdict(int),
        repr=False,
    )
    _last_context: tuple | None = field(default=None, repr=False)

    @classmethod
    def from_event(cls, session_id: int, event: Event):
        session = cls(
            id=session_id,
            start_time=event.start_time,
            end_time=event.end_time,
        )
        session.add_event(event)
        return session

    def add_event(self, event: Event):
        context = (
            event.application,
            event.client,
            event.case,
            event.section,
            event.project,
            event.document,
        )

        if self._last_context is not None and context != self._last_context:
            self.context_switches += 1

        self.events.append(event)
        self.events_count += 1
        self.end_time = event.end_time
        self.duration = max(
            0,
            int((self.end_time - self.start_time).total_seconds()),
        )

        self.client = self.client or event.client
        self.case = self.case or event.case
        self.project = self.project or event.project

        if event.application not in self.applications_used:
            self.applications_used.append(event.application)

        self._application_seconds[event.application] += max(0, event.duration)
        self.primary_application = max(
            self._application_seconds,
            key=self._application_seconds.get,
        )
        self._last_context = context
