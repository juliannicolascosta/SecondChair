"""
Second Chair

Módulo:
Telemetry

Archivo:
windows.py

Responsabilidad:
Obtener información de la ventana activa de Windows.
"""

import pygetwindow as gw


def get_active_window():

    window = gw.getActiveWindow()

    if window is None:
        return None

    return {
        "title": window.title
    }