# Roadmap

## v0.0.2
- [x] Captura de ventana activa
- [x] Persistencia SQLite
- [x] Duración de eventos
- [x] GitHub
- [x] Manejo básico de errores

---

## v0.0.3
- [x] Timeline de actividad básico mediante eventos
- [ ] Mejor detección de aplicaciones
- [x] Context Engine inicial basado en reglas
- [x] Reportes diarios básicos

---

## v0.0.6 — Telemetry confiable y privada
- [x] Migración compatible de SQLite
- [x] Persistencia del evento activo durante el cierre limpio
- [x] Pruebas deterministas de Telemetry, Context y Storage
- [x] Cierre explícito de conexiones SQLite
- [x] Resumen diario desde SQLite
- [x] Tiempo total por aplicación, expediente y cliente
- [x] Conteo de cambios de contexto
- [ ] Pausa y exclusiones configurables
- [ ] Retención y minimización de títulos
- [ ] Identificación por proceso y ventana, no sólo por título
- [ ] Métricas de cobertura, desconocidos y errores de persistencia
- [ ] Confianza y procedencia para contexto inferido

---

## v0.0.7 — Work Session Engine
- [x] Modelo WorkSession
- [x] SessionBuilder determinista
- [x] Cierre por cambio de expediente
- [x] Cierre por más de diez minutos de inactividad
- [x] Cierre por contexto explícito completamente distinto
- [x] Integración con WorkingMemory
- [x] Historial diario de sesiones en memoria
- [x] Resumen de sesiones al cerrar
- [x] Pruebas de creación, cierre, duración y conteo
- [ ] Validación de reglas con datos reales controlados

---

## v0.0.8 — Domain Layer
- [x] Entidades jurídicas como dataclasses
- [x] Workspace completo en memoria
- [x] DomainRegistry con garantía de unicidad
- [x] Relaciones simples entre objetos
- [x] DomainResolver sin mutaciones automáticas
- [x] Separación entre Observed World y Domain World
- [x] Pruebas unitarias de Registry, Resolver, Workspace y relaciones
- [ ] Validación y promoción explícita de candidatos
- [ ] Integración con Memory
- [ ] Persistencia del dominio

---

## v0.1
- [x] Memory inicial en proceso
- [ ] Detección de clientes
- [ ] Detección de expedientes
- [ ] Contextos de trabajo

---

## v0.2
- [ ] Optimizer
- [ ] Detección de fricciones
- [ ] Recomendaciones automáticas

---

## v1.0
- [ ] Assistant
- [ ] Interacción en lenguaje natural
- [ ] Automatización inteligente
