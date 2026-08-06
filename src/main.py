"""
Second Chair

Archivo principal.
"""

from src.storage.database import initialize
from src.memory.working_memory import WorkingMemory
from src.telemetry.observer import observe
from src.analytics.reports import today_summary
from src.memory.reports import sessions_summary
from src.domain.learner import learning_day_summary
from src.domain.learner import DomainLearner
from src.domain.registry import DomainRegistry
from src.domain.repository import DomainRepository
from src.domain.resolver import DomainResolver


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

    memory = WorkingMemory(
        domain_learner=learner,
        domain_repository=domain_repository,
    )

    print("Second Chair ha iniciado correctamente.")

    try:

        observe(memory)

    finally:

        print()

        today_summary()

        sessions_summary(memory.sessions)

        learning_day_summary(memory.learning_results)


if __name__ == "__main__":

    main()
