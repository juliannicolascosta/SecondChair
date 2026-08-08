"""Single-key calibration controls for the live SecondChair console."""

import time
from datetime import datetime

from src.workflows.reports import render_trace, render_trace_list


class ConsoleCalibrationController:
    def __init__(
        self,
        repository,
        collector,
        *,
        hotkey_source,
        input_func=input,
        output=print,
        sleeper=time.sleep,
        countdown=3,
        clock=datetime.now,
    ):
        self.repository = repository
        self.collector = collector
        self.hotkey_source = hotkey_source
        self.input_func = input_func
        self.output = output
        self.sleeper = sleeper
        self.countdown = countdown
        self.clock = clock
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.hotkey_source.start(self.toggle)
        self.output("Calibración: presione F8 para iniciar o finalizar desde cualquier ventana.")

    def stop(self):
        self.running = False
        self.hotkey_source.stop()

    def toggle(self):
        try:
            if self.repository.current() is None:
                self._begin()
            else:
                self._finish()
        except Exception as error:
            self.output(f"No se pudo controlar la calibración: {error}")

    def list(self):
        render_trace_list(self.repository.list(), self.output)

    def _begin(self):
        label = " ".join(self.input_func("¿Qué flujo vamos a calibrar? ").split())
        if not label:
            self.output("Calibración cancelada: el nombre no puede estar vacío.")
            return
        self.output("Cambie a la aplicación inicial.")
        for remaining in range(self.countdown, 0, -1):
            self.output(f"Inicio en {remaining}...")
            self.sleeper(1)
        trace = self.repository.start(label)
        self.output(f"CALIBRACIÓN INICIADA | {trace.label} | ID {trace.id}")
        self.output("Presione F8 desde cualquier aplicación para finalizar.")

    def _finish(self):
        boundary = self.clock()
        self.collector.mark_control_boundary(boundary)
        trace = self.repository.finish(end_time=boundary)
        self.repository.finalize_pending(self.collector)
        trace = self.repository.get(trace.id)
        self.output("CALIBRACIÓN FINALIZADA")
        render_trace(trace, self.output)
