"""
Second Chair

Archivo:
main.py

Responsabilidad:
Punto de entrada de la aplicación.
"""

from src.storage.database import initialize
from src.telemetry.observer import observe
from src.memory.manager import MemoryManager


def start():

    print("Second Chair ha iniciado correctamente.")

    initialize()

    memory = MemoryManager()

    observe(memory)


if __name__ == "__main__":

    start()