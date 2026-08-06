# Estado del Proyecto

## Versión

0.0.9 (en desarrollo)

## Estado

Deterministic Learning Engine

## Objetivo actual

Incorporar conocimiento inequívoco desde WorkSession cerradas sin confundir observaciones con hechos confirmados.

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

## Próximo objetivo

Diseñar confirmación humana para candidatos ambiguos y validar las reglas sobre datos controlados antes de persistir el dominio.

## Estado general

🟢 En desarrollo
