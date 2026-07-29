"""
Second Chair

Archivo:
main.py

Responsabilidad:
Punto de entrada principal de la aplicación.
"""

from storage.database import initialize
from telemetry.observer import observe


def start():

    initialize()

    print("Second Chair ha iniciado correctamente.")

    observe()


if __name__ == "__main__":
    start()