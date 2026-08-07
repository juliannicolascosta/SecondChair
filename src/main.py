"""
Second Chair

Archivo principal.
"""

from functools import partial

from src.storage.database import initialize, save_session_interactions
from src.memory.working_memory import WorkingMemory
from src.telemetry.observer import observe
from src.analytics.reports import friction_report, today_summary
from src.memory.reports import sessions_summary
from src.domain.learner import learning_day_summary
from src.domain.learner import DomainLearner
from src.domain.registry import DomainRegistry
from src.domain.repository import DomainRepository
from src.domain.resolver import DomainResolver
from src.telemetry.interaction.collector import InteractionCollector
from src.telemetry.interaction.ui_automation import UIAutomationInspector
from src.telemetry.interaction.windows_events import WindowsEventSource
from src.telemetry.windows import get_active_window


def main():

    initialize()

    domain_repository = DomainRepository()
    domain_repository.initialize()
    workspace = domain_repository.load_workspace()
    registry = DomainRegistry(workspace)
    resolver = DomainResolver(registry)
    learner = DomainLearner(workspace, registry, resolver)
    learner.learned_session_ids.update(
        domain_repository.load_learned_session_ids()
    )

    interaction_collector = InteractionCollector(
        event_source=WindowsEventSource(),
        ui_inspector=UIAutomationInspector(),
        window_provider=get_active_window,
    )
    memory = WorkingMemory(
        domain_learner=learner,
        domain_repository=domain_repository,
        interaction_collector=interaction_collector,
        interaction_sink=partial(save_session_interactions),
    )

    print("Second Chair ha iniciado correctamente.")

    try:
        interaction_collector.start()
        observe(memory)

    finally:
        interaction_collector.stop()
        print()

        today_summary()

        friction_report()

        sessions_summary(memory.sessions)

        learning_day_summary(memory.learning_results)


if __name__ == "__main__":

    main()
