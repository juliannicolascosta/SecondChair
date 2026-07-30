# Second Chair

Second Chair es una plataforma de inteligencia operativa para estudios jurídicos.

Actualmente registra la actividad del usuario en Windows, identifica la aplicación utilizada y almacena eventos en una base SQLite.

## Estado actual

Versión: v0.0.3

Implementado:

- Captura de ventana activa
- Detección básica de aplicaciones
- Persistencia SQLite
- Registro de duración de eventos
- Modelo Event
- Arquitectura modular

## Estructura

```
src/

    main.py

    models/
        event.py

    telemetry/
        windows.py
        analyzer.py
        observer.py

    storage/
        database.py
```

## Próximo objetivo

Construir el Context Engine.

Second Chair deberá comprender:

- qué cliente está abierto
- qué expediente
- qué documento
- qué tarea está realizando el abogado

para luego detectar fricciones y sugerir optimizaciones.
