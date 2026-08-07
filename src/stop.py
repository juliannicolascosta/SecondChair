"""Request a clean stop from a second terminal: python -m src.stop."""

from src.telemetry.shutdown import request_shutdown


def main():
    if request_shutdown():
        print("Solicitud de cierre enviada a SecondChair.")
    else:
        print("No hay una instancia de SecondChair en ejecución.")


if __name__ == "__main__":
    main()
