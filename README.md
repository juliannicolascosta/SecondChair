# Second Chair

Second Chair es una plataforma de inteligencia operativa para estudios jurídicos.

Actualmente registra la actividad del usuario en Windows, identifica la aplicación utilizada, extrae contexto básico y almacena eventos en una base SQLite.

## Estado actual

Versión: v0.0.9 (en desarrollo)

Implementado:

- Captura de ventana activa
- Detección básica de aplicaciones
- Persistencia SQLite
- Registro de duración de eventos
- Modelo Event
- Arquitectura modular
- Contexto heurístico para Lex Doctor, VS Code y documentos PDF
- Migración compatible del esquema SQLite
- Memoria de trabajo acotada
- Resumen diario básico
- Totales diarios por aplicación, expediente y cliente
- Cantidad diaria de cambios de contexto
- Pruebas deterministas de Telemetry, Context y Storage
- Agrupación en memoria de eventos consecutivos en WorkSession
- Resumen de sesiones al cerrar SecondChair
- Domain Layer inicial completamente en memoria
- Registry de entidades jurídicas únicas
- Resolver no mutante para contexto observado
- Aprendizaje determinista y conservador desde WorkSession cerradas
- Auditoría diaria de conocimiento creado y candidatos pendientes

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

    context/
        engine.py
        parser.py

    memory/
        working_memory.py
        session_builder.py
        reports.py

    models/
        event.py
        work_session.py

    analytics/
        queries.py
        reports.py

    domain/
        candidates.py
        entities.py
        learner.py
        registry.py
        resolver.py
        relations.py
        workspace.py

tests/
```

## Próximo objetivo

Completar la base de telemetría confiable y privada antes de ampliar el Context Engine.

Second Chair deberá comprender:

- qué cliente está abierto
- qué expediente
- qué documento
- qué tarea está realizando el abogado

para luego detectar fricciones y sugerir optimizaciones.

Todavía no se considera suficientemente confiable para Optimizer ni Assistant.

Al detener el observer con `Ctrl+C`, SecondChair persiste el último evento y muestra el resumen diario y el resumen de sesiones. Las duraciones menores a un minuto se muestran en segundos.

## Event y WorkSession

Un `Event` es un hecho atómico: una ventana activa durante un intervalo determinado.

Una `WorkSession` agrupa varios eventos que pertenecen a una misma tarea intelectual. Cambiar entre Lex Doctor, Word, PDF y navegador no crea por sí solo una tarea nueva. Actualmente una sesión termina cuando cambia el expediente, transcurren más de diez minutos sin actividad o aparece un contexto explícito completamente distinto.

Las sesiones se mantienen sólo en memoria y no se guardan en SQLite.

## Dominio

El Observed World registra hechos mediante Event y WorkSession. El Domain World representa clientes, expedientes, organizaciones, personas y documentos estables dentro de un Workspace.

En v0.0.8 ambos mundos permanecen desacoplados: DomainResolver produce candidatos sin modificar DomainRegistry. El dominio no se persiste ni participa todavía de Memory o Assistant. La especificación completa está en [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md).

Desde v0.0.9, WorkingMemory entrega las WorkSession terminadas a DomainLearner. El Learner promueve sólo conocimiento inequívoco y conserva las inferencias ambiguas como `LearningCandidate` pendientes. Workspace continúa exclusivamente en memoria.

> Los eventos describen lo ocurrido. El Dominio describe la realidad conocida. Nunca deben confundirse.

El aprendizaje funciona completamente offline y sigue el orden: reglas, heurísticas, estadística e IA. En este hito sólo se aplican reglas y heurísticas deterministas.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
