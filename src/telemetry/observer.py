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
from src.storage.database import save_event


def observe():

    current_event = None
    start_time = None

    while True:

        try:

            window = get_active_window()

            event = analyze_window(window)

            if event is None:

                time.sleep(1)
                continue

            event = enrich(event)

            if current_event is None:

                current_event = event
                start_time = datetime.now()

            elif event.title != current_event.title:

                end_time = datetime.now()

                duration = int(
                    (end_time - start_time).total_seconds()
                )

                print(
                    f"{end_time.strftime('%H:%M:%S')} | "
                    f"{current_event.application} | "
                    f"{current_event.title} | "
                    f"{duration}s"
                )

                save_event(

                    start_time.strftime("%Y-%m-%d %H:%M:%S"),

                    end_time.strftime("%Y-%m-%d %H:%M:%S"),

                    duration,

                    current_event.application,

                    current_event.title

                )

                current_event = event
                start_time = datetime.now()

            time.sleep(1)

        except Exception:

            print("\nERROR EN OBSERVER")

            traceback.print_exc()

            time.sleep(2)