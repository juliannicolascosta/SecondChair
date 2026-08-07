"""Working memory for completed events and today's WorkSession objects."""

from collections import deque
import traceback

from src.domain.learner import DomainLearner
from src.memory.session_builder import SessionBuilder


class WorkingMemory:
    def __init__(
        self,
        max_events=100,
        session_builder=None,
        domain_learner=None,
        domain_repository=None,
        interaction_collector=None,
        interaction_sink=None,
    ):
        self.events = deque(maxlen=max_events)
        self.session_builder = session_builder or SessionBuilder()
        self.domain_learner = domain_learner or DomainLearner()
        self.domain_repository = domain_repository
        self.interaction_collector = interaction_collector
        self.interaction_sink = interaction_sink
        self.sessions = []
        self.learning_results = []
        self.pending_persistence = []
        self.interaction_errors = []

    @property
    def workspace(self):
        return self.domain_learner.workspace

    @property
    def current_session(self):
        return self.session_builder.current_session

    def register(self, event):
        self.events.append(event)
        closed_session = self.session_builder.add_event(event)

        if closed_session is not None:
            self._record_closed_session(closed_session)

    def last(self):
        if not self.events:
            return None
        return self.events[-1]

    def all(self):
        return list(self.events)

    def finish(self):
        closed_session = self.session_builder.finish()

        if closed_session is not None:
            self._record_closed_session(closed_session)

        self.retry_pending_persistence()

        return closed_session

    def _record_closed_session(self, session):
        try:
            if self.interaction_collector is not None:
                self.interaction_collector.attach_to_session(session)
            if self.interaction_sink is not None:
                self.interaction_sink(session)
        except Exception as error:
            self.interaction_errors.append(type(error).__name__)
            print("\nERROR EN TELEMETRÍA DE INTERACCIÓN")
            traceback.print_exc()
        self.sessions.append(session)
        result = self.domain_learner.learn_from_session(session)
        self.learning_results.append(result)

        if self.domain_repository is not None:
            self._persist_learning(session, result)

    def _persist_learning(self, session, result):
        try:
            self.domain_repository.save_learning_result(
                result,
                self.workspace,
                session,
            )
        except Exception as error:
            result.warnings.append(
                f"Domain persistence failed: {type(error).__name__}"
            )
            self.pending_persistence.append((session, result))
            print("\nERROR EN PERSISTENCIA DEL DOMINIO")
            traceback.print_exc()

    def retry_pending_persistence(self):
        if self.domain_repository is None or not self.pending_persistence:
            return

        pending = self.pending_persistence
        self.pending_persistence = []
        for session, result in pending:
            self._persist_learning(session, result)
