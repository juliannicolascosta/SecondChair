"""
Second Chair

Módulo:
Telemetry

Archivo:
observer.py

Responsabilidad:
Observar el entorno de trabajo y registrar eventos.
"""

from datetime import datetime
import time
import traceback

from src.telemetry.windows import get_active_window
from src.telemetry.analyzer import analyze_window
from src.context.engine import enrich
from src.context.continuity import ContextContinuity
from src.storage.database import save_event_model


def complete_event(event, end_time, event_sink=save_event_model):
    """Close, report and persist the event that has just finished."""

    event.end_time = end_time
    event.duration = max(
        0,
        int((event.end_time - event.start_time).total_seconds())
    )

    print(
        f"{end_time.strftime('%H:%M:%S')} | "
        f"{event.application} | "
        f"{event.title} | "
        f"{event.duration}s"
    )

    event_sink(event)


def observe(
    memory,
    window_provider=get_active_window,
    event_sink=save_event_model,
    clock=datetime.now,
    sleeper=time.sleep,
    poll_interval=1,
    max_iterations=None,
    idle_tracker=None,
    shutdown_signal=None,
    context_continuity=None,
    heartbeat=None,
):

    current_event = None
    context_continuity = context_continuity or ContextContinuity()
    iterations = 0

    try:
        while (
            (max_iterations is None or iterations < max_iterations)
            and not (shutdown_signal is not None and shutdown_signal.is_set())
        ):

            try:
                iterations += 1

                window = window_provider()

                if idle_tracker is not None:
                    idle_tracker.sample()

                if heartbeat is not None:
                    heartbeat()

                event = analyze_window(
                    window,
                    previous_application=(
                        current_event.application if current_event is not None else None
                    ),
                )

                if event is None:
                    sleeper(poll_interval)
                    continue

                event = enrich(event)
                event = context_continuity.apply(event)

                if current_event is None:

                    current_event = event
                    current_event.start_time = clock()

                elif (
                    event.title != current_event.title
                    or event.application != current_event.application
                ):

                    complete_event(current_event, clock(), event_sink)
                    memory.register(current_event)

                    current_event = event
                    current_event.start_time = clock()

                sleeper(poll_interval)

            except KeyboardInterrupt:

                print("\nSecond Chair detenido.")
                break

            except Exception:

                print("\nERROR EN OBSERVER")

                traceback.print_exc()

                sleeper(2)

    finally:
        if heartbeat is not None:
            heartbeat()
        if current_event is not None and current_event.end_time is None:
            complete_event(current_event, clock(), event_sink)
            memory.register(current_event)

        memory.finish()
