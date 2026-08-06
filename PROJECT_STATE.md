# Estado del Proyecto

## Versión

0.0.8 (en desarrollo)

## Estado

Domain Layer

## Objetivo actual

Construir el primer modelo explícito del mundo jurídico sin integrarlo todavía al flujo observado.

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

## Próximo objetivo

Diseñar un proceso explícito de validación y promoción de candidatos antes de integrar Domain con Memory.

## Estado general

🟢 En desarrollo
