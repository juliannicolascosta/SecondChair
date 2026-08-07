# Estado del Proyecto

## v0.1.3 — Workflow Trace

- Delimitación manual de flujos con inicio, cierre y cancelación.
- UUID estable y asociación persistente con `WorkSession` cerradas.
- Agregación de aplicaciones, procesos, ventanas, cambios de contexto e interacciones.
- Exportación anónima sin etiqueta, procesos ni identificadores internos.
- Comparación descriptiva entre ejecuciones con la misma etiqueta.
- Recorte temporal exacto de interacciones independiente de los límites de WorkSession.
- Estado explícito `collecting`, `pending`, `session_aggregate` o `exact`.
- Importación segura de analítica y pruebas aunque `PyGetWindow` no esté instalado.
- Suite reproducible en Windows mediante GitHub Actions.
- Sin IA, screenshots, clipboard, texto escrito ni valores de campos.

## v0.1.2 — Reliability & Calibration

- UI Automation declara `available`, `partial` o `unavailable` y conserva una
  causa diagnóstica; una métrica no observada nunca se informa como cero.
- Las transiciones de ventana, aplicación, contexto significativo y expediente
  se calculan y presentan por separado.
- Reconocimiento por metadatos de aplicaciones y servicios prioritarios, con el
  proceso como señal principal y el título como fallback controlado.
- Secciones estructurales de Lex Doctor reconocidas sin atribuir una ventana
  genérica como `Procesos` a Lex Doctor sin evidencia adicional.
- Continuidad conservadora para ventanas auxiliares inmediatamente posteriores
  a una ventana confirmada de Lex Doctor y reconocimiento del proceso de ChatGPT.
- Porcentajes de cobertura de aplicación/contexto y tiempo no asociado a
  WorkSessions para hacer explícitas las zonas todavía no medidas.
- Extracción contextual conservadora de la parte en carátulas `S/`, sin ampliar
  las reglas de promoción automática del DomainLearner.
- Separación de actividad previa entre múltiples aplicaciones cuando aparece el
  primer expediente explícito de una WorkSession.
- Continuidad pasiva de cinco minutos desde Lex Doctor hacia Outlook y WhatsApp
  Business, con procedencia, confianza y estado no confirmado persistidos.
- DomainLearner exige evidencia Lex directa para promover expedientes y
  contrapartes; una comunicación inferida sólo genera candidatos pendientes.
- Exportación anónima offline con métricas agregadas, sin identidades, títulos,
  documentos, rutas, correos ni teléfonos.
- Sin IA, OCR, screenshots, clipboard, texto escrito ni valores de campos.

## v0.1.1 — Interaction Telemetry

- Captura no bloqueante de clic, actividad agregada de teclado y scroll.
- Clasificación best-effort de controles mediante UI Automation, con fallback.
- Detalle efímero; persistencia agregada por WorkSession/jornada.
- Reporte `FRICCIÓN DEL DÍA` y ranking descriptivo de sesiones.
- Sin IA, screenshots, clipboard, texto, teclas, valores ni contraseñas.
- **SecondChair mide interacciones, no contenido.**

## Versión

0.1.3 (en desarrollo)

## Estado

Workflow Trace y calibración con flujos reales

## Objetivo actual

Medir de forma verificable, distinguir ausencia de medición de un cero real y
producir agregados compartibles sin exponer contexto sensible.

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

Calibrar Workflow Trace con ejecuciones reales controladas. La confirmación humana
y el cifrado local siguen siendo obligatorios antes de ampliar la captura de
conocimiento sensible.

## Estado general

🟢 En desarrollo
