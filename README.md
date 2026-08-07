# Second Chair

> **SecondChair mide interacciones, no contenido.**

## Interaction Telemetry (v0.1.1)

SecondChair mide fricción operativa mediante clics, actividad agregada de teclado,
scroll, cambios de ventana y tipos de control. Nunca conserva teclas, texto escrito,
valores de campos, contraseñas, portapapeles, capturas ni coordenadas. Los eventos
detallados son efímeros y acotados en memoria; SQLite sólo recibe contadores
agregados por `WorkSession`.

Un clic clasificado como botón, campo, combo o menú es una interacción: incrementa
`mouse_clicks` y el contador del control, pero `interaction_count` sólo una vez.
`window_switches` no incrementa el total. Una interacción nunca crea una
`WorkSession`; se asocia por timestamp cuando una sesión existente se cierra.

```powershell
python -m src.main
```

UI Automation es opcional: ante ausencia o error, el clic básico se conserva con
`control_type=None`.

SecondChair separa tiempo activo e inactivo usando el contador de última entrada
de Windows, con un umbral predeterminado de cinco minutos. No inspecciona cuál fue
la entrada. Si `Ctrl+C` no llega por el modo selección de la consola, se puede pedir
un cierre limpio desde otra PowerShell:

```powershell
python -m src.stop
```

Second Chair es una plataforma de inteligencia operativa para estudios jurídicos.

Actualmente registra la actividad del usuario en Windows, identifica la aplicación utilizada, extrae contexto básico y almacena eventos en una base SQLite.

## Estado actual

Versión: v0.1.0 (en desarrollo)

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
- Persistencia transaccional del dominio en tablas separadas de events
- Recarga de identidades, relaciones, evidencia y métricas entre reinicios

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
        repository.py
        registry.py
        resolver.py
        relations.py
        serializer.py
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

## Persistencia del dominio

Desde v0.1.0, eventos y dominio comparten `data/secondchair.db` pero utilizan tablas y versiones de esquema independientes. `events` conserva hechos observados; las tablas `domain_*` conservan conocimiento, relaciones, evidencia, candidatos y sesiones ya aprendidas.

La inicialización carga Workspace y reconstruye Registry antes de iniciar Telemetry. Cada WorkSession cerrada se persiste en una transacción. Las pruebas siempre usan bases temporales.

La base contiene información jurídica sensible en texto plano. El cifrado en reposo queda como riesgo prioritario pendiente.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
