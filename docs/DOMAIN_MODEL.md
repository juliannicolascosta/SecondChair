# Domain Model

## Propósito

El Domain Layer representa el mundo jurídico que SecondChair intenta comprender. En v0.0.8 funciona únicamente en memoria y permanece desacoplado de Telemetry, Context, Memory, Analytics y SQLite.

No utiliza inteligencia artificial.

## Observed World

El Observed World contiene hechos capturados del entorno de trabajo:

- ventana activa;
- aplicación;
- título;
- tiempos;
- metadatos extraídos mediante reglas.

Sus unidades principales son `Event` y `WorkSession`. Es evidencia operativa: describe lo que SecondChair observó, incluso cuando la interpretación es incompleta o ambigua.

## Domain World

El Domain World contiene conceptos jurídicos estables:

- clientes;
- expedientes;
- organizaciones;
- personas;
- documentos;
- relaciones entre ellos.

Una cadena observada no se convierte automáticamente en verdad del dominio. Resolver detecta candidatos; Registry decide qué entidades forman parte del Workspace.

## Workspace

`Workspace` representa el estudio jurídico completo. Contiene colecciones de:

- `clients`;
- `cases`;
- `organizations`;
- `persons`;
- `documents`;
- `statistics`.

En esta versión no se guarda ni se reconstruye desde SQLite. Sus estadísticas son conteos simples actualizados por DomainRegistry.

## Entidades

Todas las entidades son dataclasses con un identificador UUID generado en memoria.

### Client

Representa una persona u organización que mantiene una relación de cliente con el estudio. Conserva referencias a sus expedientes.

### Case

Representa un expediente o asunto. Puede relacionarse con un cliente, documentos, organizaciones y personas.

### Organization

Representa una empresa, organismo, tribunal u otra organización vinculada con expedientes.

### Person

Representa una persona física vinculada con uno o más expedientes.

### Document

Representa un documento identificado por nombre y, opcionalmente, una ruta observada. Puede pertenecer a varios expedientes.

## Relaciones

Las relaciones son referencias directas y bidireccionales entre objetos:

```text
Client       -> Cases
Case         -> Documents
Case         -> Organizations
Case         -> Persons
Document     -> Cases
Organization -> Cases
Person       -> Cases
```

Las funciones de `relations.py` son idempotentes: relacionar dos veces los mismos objetos no duplica referencias. Un expediente no puede asignarse simultáneamente a dos clientes.

No se utiliza una graph database.

## Registry

`DomainRegistry` es la única capa autorizada a incorporar entidades mediante:

- `obtener_o_crear_cliente()`;
- `obtener_o_crear_expediente()`;
- `obtener_o_crear_empresa()`;
- `obtener_o_crear_persona()`;
- `obtener_o_crear_documento()`.

La identidad se normaliza ignorando diferencias de mayúsculas, minúsculas, espacios iniciales y espacios repetidos. Una identidad normalizada siempre devuelve la misma instancia.

Registry también expone consultas `find_*` de sólo lectura para Resolver.

## Resolver

`DomainResolver` transforma un diccionario producido por parser/context en `DomainResolution`. Actualmente reconoce:

- `cliente` o `client`;
- `expediente` o `case`;
- `empresa` u `organization`;
- `documento` o `document`.

Si una entidad ya existe, Resolver puede devolver la instancia conocida consultando Registry. Si no existe, devuelve una entidad candidata separada.

Resolver nunca registra candidatos, modifica Workspace ni crea relaciones automáticamente. Esta separación evita convertir una inferencia observada en verdad del dominio sin una decisión explícita.

## Límites de v0.0.8

- Sin persistencia.
- Sin integración con Memory.
- Sin integración con Assistant.
- Sin resolución probabilística.
- Sin fusiones o alias de entidades.
- Sin validación humana integrada.
