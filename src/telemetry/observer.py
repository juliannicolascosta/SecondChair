"""
Second Chair

Módulo:
Telemetry

Archivo:
observer.py

Responsabilidad:
Observar el entorno de trabajo.
"""

from datetime import datetime
import time

from telemetry.windows import get_active_window
from telemetry.analyzer import analyze_window
from telemetry.classifier import classify
from storage.database import save_event


def observe():

    last_window = None
    last_change = time.time()

    while True:

        window = get_active_window()

        window = analyze_window(window)

        window = classify(window)

        if (
            window is not None
            and window["title"] is not None
            and window["title"].strip()
        ):

            if window["title"] != last_window:

                now = datetime.now().strftime("%H:%M:%S")

                duration = int(time.time() - last_change)

                print(
                    f"{now} | "
                    f"{window['application']} | "
                    f"{window['category']} | "
                    f"{window['activity']} | "
                    f"{duration}s"
                )

                save_event(
                    now,
                    window["application"],
                    window["title"],
                    duration
                )

                last_window = window["title"]
                last_change = time.time()

        time.sleep(1)