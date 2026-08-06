# Lessons Learned

## v0.0.1

- Es preferible construir una base pequeña pero estable antes que muchas funciones incompletas.

---

## v0.0.2

- La duración debe asociarse a la ventana que finaliza, no a la que comienza.
- SQLite debe inicializarse automáticamente.
- Los errores del sistema operativo nunca deben detener el observer.

---

## v0.0.3

- Es mejor trabajar con objetos (`Event`) que con diccionarios.
- La arquitectura debe prepararse para crecer antes de incorporar inteligencia.

---

## v0.0.6

- `CREATE TABLE IF NOT EXISTS` no migra una base existente; el esquema debe versionarse y evolucionar explícitamente.
- El context manager de SQLite confirma o revierte transacciones, pero la conexión debe cerrarse explícitamente.
- El evento activo debe persistirse durante un cierre limpio para evitar huecos silenciosos.
- Telemetry debe poder ejecutarse con reloj, captura, espera y almacenamiento inyectables para ser verificable sin observar un escritorio real.
- Contexto inferido no equivale a contexto confiable: necesita procedencia, confianza y validación antes de alimentar optimizaciones.
- Analytics debe operar sobre eventos persistidos y ofrecer cálculos puros, independientes de la captura en vivo.
- Un cambio de contexto necesita una definición explícita y verificable; actualmente compara aplicación y metadatos contextuales entre eventos consecutivos.
- Las duraciones breves no deben redondearse a cero minutos porque ocultan interrupciones y cambios rápidos.

---

## v0.0.7

- Un cambio de aplicación no equivale a un cambio de tarea intelectual.
- Event debe permanecer como evidencia atómica; WorkSession es una agrupación derivada y revisable.
- Los eventos deben llegar completos a SessionBuilder para que duración, inactividad y aplicación principal sean deterministas.
- La ausencia de contexto no demuestra un cambio completo de tarea; cerrar en ese caso fragmentaría sesiones como Word, PDF y navegador.
- Las reglas iniciales deben permanecer explícitas y testeables antes de considerar modelos probabilísticos o inteligencia artificial.

---

## v0.0.8

- Un valor observado no debe convertirse automáticamente en una entidad jurídica confirmada.
- Resolver candidatos y registrarlos son responsabilidades distintas.
- La unicidad necesita normalización explícita; diferencias de mayúsculas o espacios no justifican entidades duplicadas.
- Las relaciones bidireccionales deben ser idempotentes para evitar referencias repetidas.
- El dominio debe poder evolucionar y probarse sin depender de captura, memoria, Analytics, SQLite o inteligencia artificial.
