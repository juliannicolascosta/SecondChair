"""
Second Chair

Archivo principal.
"""

from functools import partial

from datetime import date
from src.storage.database import initialize, save_idle_metrics, save_session_interactions
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
from src.telemetry.windows import get_idle_seconds
from src.telemetry.idle import IdleTimeTracker
from src.telemetry.shutdown import WindowsShutdownSignal


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

    ui_inspector = UIAutomationInspector()
    interaction_collector = InteractionCollector(
        event_source=WindowsEventSource(),
        ui_inspector=ui_inspector,
        window_provider=get_active_window,
    )
    idle_tracker = IdleTimeTracker(get_idle_seconds)
    shutdown_signal = WindowsShutdownSignal()
    memory = WorkingMemory(
        domain_learner=learner,
        domain_repository=domain_repository,
        interaction_collector=interaction_collector,
        interaction_sink=partial(save_session_interactions),
    )

    print("Second Chair ha iniciado correctamente.")
    print(
        "Clasificación de controles UI: "
        + ("activa" if ui_inspector.available else "no disponible; captura básica activa")
    )
    if not ui_inspector.available:
        print(f"Diagnóstico UI Automation: {ui_inspector.reason or 'not_configured'}")

    try:
        interaction_collector.start()
        observe(
            memory,
            idle_tracker=idle_tracker,
            shutdown_signal=shutdown_signal,
        )

    finally:
        interaction_collector.stop()
        shutdown_signal.close()
        save_idle_metrics(date.today(), idle_tracker)
        print()

        today_summary()

        friction_report()

        sessions_summary(memory.sessions)

        learning_day_summary(memory.learning_results)


if __name__ == "__main__":

    main()
