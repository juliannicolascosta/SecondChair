"""
Second Chair

Archivo:
main.py

Responsabilidad:
Punto de entrada del sistema.
"""

from storage.database import initialize
from telemetry.observer import observe


def start():

    print("Second Chair ha iniciado correctamente.")

    initialize()

    observe()


if __name__ == "__main__":

    try:

        start()

    except KeyboardInterrupt:

        print("\nSecond Chair finalizado por el usuario.")

    except Exception as error:

        print(f"\nError inesperado: {error}")