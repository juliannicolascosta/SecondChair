"""
Second Chair

Archivo principal.
"""

from src.storage.database import initialize
from src.memory.working_memory import WorkingMemory
from src.telemetry.observer import observe
from src.analytics.reports import today_summary
from src.memory.reports import sessions_summary


def main():

    initialize()

    memory = WorkingMemory()

    print("Second Chair ha iniciado correctamente.")

    try:

        observe(memory)

    finally:

        print()

        today_summary()

        sessions_summary(memory.sessions)


if __name__ == "__main__":

    main()
