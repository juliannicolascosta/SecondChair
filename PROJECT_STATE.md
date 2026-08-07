# Estado del Proyecto

## v0.1.1 — Interaction Telemetry

- Captura no bloqueante de clic, actividad agregada de teclado y scroll.
- Clasificación best-effort de controles mediante UI Automation, con fallback.
- Detalle efímero; persistencia agregada por WorkSession/jornada.
- Reporte `FRICCIÓN DEL DÍA` y ranking descriptivo de sesiones.
- Sin IA, screenshots, clipboard, texto, teclas, valores ni contraseñas.
- **SecondChair mide interacciones, no contenido.**

## Versión

0.1.0 (en desarrollo)

## Estado

Persistencia segura del dominio

## Objetivo actual

Conservar conocimiento, relaciones, evidencia y candidatos entre reinicios sin alterar el historial de eventos.

## Último avance

- Migración compatible del esquema SQLite existente
- Persistencia del evento activo al cerrar limpiamente
- Persistencia basada en el modelo Event
- Contexto sincronizado entre el diccionario y los campos tipados
- Conexiones SQLite cerradas explícitamente
- Observer inyectable y verificable mediante pruebas
- Suite inicial de 5 pruebas
- Analytics diario basado exclusivamente en eventos persistidos
- Tiempo total y agrupaciones por aplicación, expediente y cliente
- Conteo de cambios de contexto entre eventos consecutivos
- Suite ampliada de 9 pruebas
- Modelo WorkSession en memoria
- SessionBuilder basado en reglas explícitas
- Integración con WorkingMemory
- Historial diario de sesiones en memoria
- Resumen de sesiones durante el cierre limpio
- Suite ampliada de 17 pruebas
- Entidades Client, Case, Organization, Person, Document y Workspace
- DomainRegistry con unicidad normalizada
- Relaciones bidireccionales e idempotentes
- DomainResolver no mutante
- Separación documentada entre Observed World y Domain World
- Suite ampliada de 25 pruebas
- LearningCandidate y LearningResult auditables
- DomainLearner offline con umbrales explícitos
- Promoción conservadora de clientes, expedientes, organizaciones y documentos
- Candidatos ambiguos pendientes de confirmación futura
- Integración de sesiones cerradas con Workspace
- Protección contra aprendizaje repetido por ID de sesión
- Resumen de aprendizaje del día
- Suite ampliada de 35 pruebas
- DomainRepository transaccional y completamente offline
- Esquema de dominio v1 separado de events
- Migración explícita 0→1 sin pérdida
- UUID, claves canónicas, fechas y métricas persistentes
- Candidatos pending, accepted y rejected
- Evidencia de promociones con procedencia y confianza
- Protección de reaprendizaje entre procesos
- Recuperación de Workspace y relaciones al iniciar
- Suite ampliada de 47 pruebas

## Próximo objetivo

Diseñar confirmación humana y cifrado local antes de ampliar la captura de conocimiento sensible.

## Estado general

🟢 En desarrollo
