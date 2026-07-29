"""
Second Chair

Módulo:
Telemetry

Archivo:
observer.py

Responsabilidad:
Observar el entorno de trabajo.
"""

from telemetry.windows import get_active_window
from telemetry.analyzer import analyze_window
from storage.database import save_event

from datetime import datetime
import time


def observe():

    last_window = None

    while True:

        window = get_active_window()
        window = analyze_window(window)

        if (
            window is not None
            and window["title"] is not None
            and window["title"].strip()
        ):

            if window["title"] != last_window:

                now = datetime.now().strftime("%H:%M:%S")

                print(
                    f"{now} | {window['application']} | {window['title']}"
                )

                save_event(
                    now,
                    window["application"],
                    window["title"]
                )

                last_window = window["title"]

        time.sleep(1)