# Second Chair
## Arquitectura del sistema

## WindowTelemetry e InteractionTelemetry

WindowTelemetry (`observer.py`) mide permanencia y transiciones de contexto y
produce `Event`. InteractionTelemetry (`telemetry/interaction`) es una capa
separada, basada en eventos, que mide acciones físicas y tipos de control. Al cerrar
una WorkSession, los eventos efímeros comprendidos entre inicio y fin se reducen a
contadores y se descartan.

```text
Windows hooks -> InteractionCollector -> detalle efímero acotado
                                           |
WorkSession cerrada ------------------------+
                                           v
                             contadores agregados -> SQLite -> reporte
```

Un clic identificado como botón incrementa `mouse_clicks`, `buttons_used` e
`interaction_count=1`. Teclado y scroll suman una interacción por callback. Los
cambios de ventana son una métrica separada. Una interacción no crea sesiones.

El callback de teclado no desreferencia datos nativos: sólo emite actividad. El de
mouse tampoco lee ni persiste coordenadas o deltas. UI Automation consulta sólo
`ControlTypeName`, nunca nombres, ValuePattern o contenido, y cualquier fallo
degrada a captura básica.

**SecondChair mide interacciones, no contenido.**

## Filosofía

Second Chair no es un software de automatización.

Es un sistema de observación, aprendizaje y optimización del trabajo profesional.

Antes de intervenir, observa.
Antes de automatizar, comprende.
Antes de sugerir, mide.

Su objetivo no es imponer una forma de trabajar, sino aprender cómo trabaja cada estudio jurídico, detectar fricciones, identificar oportunidades de mejora y asistir de manera proactiva.

---

# Principios

## 1. Los datos primero

Second Chair nunca supone.

Primero registra hechos.

Luego obtiene métricas.

Después detecta patrones.

Finalmente interviene.

---

## 2. Nunca perder información

Todo evento observado debe poder conservarse.

La memoria es el activo principal del sistema.

---

## 3. Separación de responsabilidades

Cada módulo tiene una única responsabilidad.

Telemetry observa.

Storage almacena.

Context interpreta hechos observados mediante reglas explícitas.

Memory agrupa y conserva contexto operativo.

Analytics calcula métricas descriptivas sobre eventos persistidos.

Optimizer propone mejoras.

Assistant interactúa con el usuario.

---

## 4. La automatización es la última etapa

Second Chair nunca automatiza un proceso que todavía no comprende.

Toda automatización debe surgir del conocimiento del flujo de trabajo real.

---

## Conceptos fundamentales

### Evento

Un hecho puntual ocurrido en un momento determinado.

Ejemplos:

- Cambio de ventana.
- Apertura de Outlook.
- Inicio de una reunión.
- Apertura de un expediente.

---

### Actividad

Una secuencia de eventos que representan una misma tarea.

Ejemplo:

Redactar una demanda.

---

### Contexto

El conjunto de información que rodea una actividad.

Incluye:

- aplicación
- documento
- expediente
- cliente
- duración
- interrupciones

---

### Sesión

Una `WorkSession` es una secuencia de eventos que representan una única tarea intelectual. No coincide necesariamente con una aplicación ni con todo el tiempo de ejecución de SecondChair.

Ejemplo: consultar un expediente en Lex Doctor, redactar en Word, leer un PDF y buscar jurisprudencia en Edge pueden pertenecer a una sola WorkSession.

La sesión técnica completa del proceso y la WorkSession son conceptos diferentes. El modelo histórico `Session` representa la primera idea; el runtime v0.0.7 utiliza `WorkSession` para agrupar trabajo intelectual.

---

# Definición de éxito

Second Chair será exitoso cuando sea capaz de responder, con precisión, preguntas como:

- ¿En qué trabajé hoy?

- ¿Cuánto tiempo dediqué a cada cliente?

- ¿Qué tareas me generan mayor fricción?

- ¿Dónde pierdo tiempo?

- ¿Qué actividades puedo automatizar?

- ¿Qué hábitos reducen mi productividad?

- ¿Qué debería estar haciendo ahora?

---

# Modelo de dominio

El núcleo del sistema gira alrededor del objeto Event.

```
Event

application

title

start_time

end_time

duration
```

En versiones futuras incorporará:

```
client

case

document

category

activity

confidence
```

Todo el sistema utilizará Event como unidad de información.

`Event` continúa siendo la unidad de evidencia. `WorkSession` es una agrupación derivada y reconstruible; nunca reemplaza ni modifica los eventos originales.

---

# Flujo implementado

```
Windows -> Telemetry -> Context -> Event -> Storage
                                      |        |
                                      v        v
                               SessionBuilder Analytics
                                      |
                                      v
                                WorkSession
```

Telemetry obtiene `application` y `title`. Context enriquece el mismo `Event` con `client`, `case`, `section`, `project` y `document`. El observer cierra y persiste el evento anterior cuando detecta un cambio, y persiste el último evento durante un cierre limpio.

Analytics consulta SQLite en modo lectura y construye un resumen diario con:

- tiempo total;
- tiempo por aplicación;
- tiempo por expediente;
- tiempo por cliente;
- cambios entre contextos operativos consecutivos.

El primer evento del día no cuenta como cambio de contexto. Analytics describe hechos persistidos; no interpreta fricciones, recomienda acciones ni utiliza inteligencia artificial.

---

# Work Session Engine

El observer entrega a WorkingMemory eventos completos, con inicio, fin, duración y contexto. SessionBuilder incorpora cada evento a la sesión actual o la cierra cuando:

- cambia un expediente explícito;
- el siguiente evento comienza más de diez minutos después del anterior;
- los contextos explícitos de cliente, expediente o proyecto son completamente incompatibles.

Un cambio de aplicación no cierra una sesión. Los eventos sin anclas contextuales pueden continuar la tarea actual. WorkSession calcula aplicación principal, aplicaciones utilizadas, cambios de contexto, cantidad de eventos y duración entre el primer inicio y el último fin.

WorkingMemory conserva la sesión actual y el historial de sesiones cerradas durante el proceso. En v0.0.7 las WorkSession no se persisten en SQLite.

---

# Domain Layer

SecondChair separa dos representaciones:

```text
Observed World                       Domain World

Event                                Client
WorkSession                          Case
Context detectado    -> Resolver -> Organization
                                     Person
                                     Document
                                         |
                                         v
                                     Workspace
```

El Observed World registra evidencia. El Domain World representa entidades jurídicas estables. Resolver traduce contexto observado a candidatos, pero no los incorpora automáticamente.

DomainRegistry garantiza unicidad y es el único responsable de agregar entidades a Workspace. Relations mantiene referencias simples entre objetos, sin graph database.

En v0.0.8 esta capa está aislada: no modifica Telemetry, Analytics, WorkingMemory ni SQLite. Consultar [DOMAIN_MODEL.md](DOMAIN_MODEL.md) para el modelo completo.

---

# Deterministic Learning Engine

Principio central:

> Los eventos describen lo ocurrido. El Dominio describe la realidad conocida. Nunca deben confundirse.

El flujo de v0.0.9 es:

```text
Completed WorkSession
        |
        v
 DomainResolver       interpreta sin mutar
        |
        v
LearningCandidate     conserva fuente, confianza y motivo
        |
        v
 DomainLearner        decide promover o dejar pendiente
        |
        v
 DomainRegistry       garantiza unicidad
        |
        v
    Workspace         conserva conocimiento durante el proceso
```

DomainLearner sólo recibe WorkSession cerradas. Conserva los IDs aprendidos para impedir procesamiento repetido y devuelve un LearningResult por sesión. WorkingMemory guarda esos resultados para auditoría diaria.

Los umbrales de promoción son constantes centralizadas. Una carátula completa de Lex Doctor puede promover expediente y cliente. Una contraparte sólo se promueve como organización cuando presenta un marcador explícito. Los documentos necesitan un nombre identificable y sólo se relacionan con un expediente inequívoco.

La arquitectura aplica este orden de capacidades:

```text
reglas -> heurísticas -> estadística -> IA
```

v0.0.9 utiliza solamente las dos primeras, de forma determinista y offline. No persiste Workspace, no crea tablas y no modifica Analytics.

---

# Persistencia del dominio

v0.1.0 ubica persistencia y serialización en `src/domain/repository.py` y `src/domain/serializer.py`. La decisión mantiene juntos el puerto de persistencia y el modelo que reconstruye, sin mezclarlo con `src/storage/database.py`, cuya responsabilidad sigue siendo `events`.

```text
Domain models/rules
        |
        v
serializer.py       transformación pura
        |
        v
repository.py       transacciones, migraciones y SQL
        |
        v
secondchair.db
   |          |
 events   domain_* tables
 hechos   conocimiento
```

Learner nunca ejecuta SQL. Repository nunca decide qué candidato promover. Registry conserva autoridad exclusiva sobre creación y recuperación de entidades en memoria.

## Ciclo de carga

1. Inicializar `events`.
2. Inicializar y migrar el esquema del dominio.
3. Cargar Workspace, UUID, métricas y relaciones.
4. Reconstruir DomainRegistry y DomainResolver.
5. Cargar las claves de WorkSession ya aprendidas.
6. Crear DomainLearner y WorkingMemory.

## Ciclo de guardado

Una WorkSession cerrada produce LearningResult. En una sola transacción, Repository actualiza entidades y relaciones, guarda evidencia/candidatos y marca la clave estable de sesión como aprendida. Un rollback conserva el LearningResult en memoria y no afecta `events`.

El esquema del dominio usa `domain_meta.schema_version`; no reutiliza `PRAGMA user_version`, reservado por el esquema histórico de eventos. Todas las conexiones activan foreign keys.
