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

from telemetry.windows import get_active_window
from telemetry.analyzer import analyze_window
from storage.database import save_event


def observe():

    current_window = None
    start_time = None

    while True:

        try:

            window = get_active_window()

            window = analyze_window(window)

            if (
                window is None
                or window["title"] is None
                or not window["title"].strip()
            ):
                time.sleep(1)
                continue

            # Primera ventana detectada

            if current_window is None:

                current_window = window
                start_time = datetime.now()

                print(
                    f"{start_time.strftime('%H:%M:%S')} | "
                    f"{window['application']} | "
                    f"{window['title']}"
                )

                time.sleep(1)
                continue

            # Cambio de ventana

            if window["title"] != current_window["title"]:

                end_time = datetime.now()

                duration = int(
                    (end_time - start_time).total_seconds()
                )

                save_event(
                    start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    duration,
                    current_window["application"],
                    current_window["title"]
                )

                print(
                    f"{end_time.strftime('%H:%M:%S')} | "
                    f"{current_window['application']} | "
                    f"{duration}s"
                )

                current_window = window
                start_time = end_time

            time.sleep(1)

        except KeyboardInterrupt:

            print("\nSecond Chair detenido.")
            break

        except Exception:

            print("\nERROR EN OBSERVER")
            traceback.print_exc()

            time.sleep(2)