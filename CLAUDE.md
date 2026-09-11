# PIE-Insights — Reglas del Proyecto

## Seguridad de Base de Datos

### REGLA ABSOLUTA: SOLO LECTURA

**PROHIBIDO ejecutar cualquier query que NO sea SELECT.**

Queries bloqueadas (sin excepciones):
- `INSERT`, `UPDATE`, `DELETE`, `REPLACE`
- `DROP`, `ALTER`, `CREATE`, `TRUNCATE`
- `GRANT`, `REVOKE`, `SET`
- `CALL` (procedimientos almacenados)
- `LOAD DATA`, `INTO OUTFILE`
- Cualquier query que modifique datos, estructura o permisos

Antes de ejecutar cualquier query SQL via MCP mysql-qa:
1. Verificar que empiece con `SELECT`, `SHOW`, `DESCRIBE` o `EXPLAIN`
2. Verificar que NO contenga subconsultas con INSERT/UPDATE/DELETE
3. Si hay duda, NO ejecutar y preguntar al usuario

### Ambientes

| Ambiente | MySQL | Mixpanel | Uso |
|----------|-------|----------|-----|
| **Beta/QA** | [ver .env] (MCP mysql-qa) | Integratepie-beta ID [ver .env] | Este proyecto |
| Produccion | NO ACCESIBLE | Integratepie ID [ver .env] | No usar para cruce con MySQL QA |

- Siempre cruzar MySQL QA con Mixpanel Beta
- Nunca mezclar datos de produccion con QA sin etiquetarlo
- User IDs > 518 en Mixpanel son de produccion

## Alcance del Proyecto

PIE-Insights es un sistema de **consulta y analisis** para generar reportes post-deploy.

**Lo que SI hace:**
- Consultar MySQL (SELECT) para extraer datos de formularios, estudiantes, colegios
- Consultar Mixpanel (Run-Query) para eventos de comportamiento
- Cruzar ambas fuentes por colegio_rbd, user_id, rut, form_id
- Generar reportes, dashboards HTML, y planes de accion
- Identificar adopcion, churn, completitud, funnels

**Lo que NO hace:**
- Modificar datos en la BD
- Crear/eliminar tablas o registros
- Ejecutar migraciones
- Enviar datos a terceros

## Flujo de Trabajo

Cuando el usuario pide un reporte:

1. **Calibrar** — Preguntar tabla MySQL + evento Mixpanel + form-name si es un informe nuevo
2. **Consultar** — Solo SELECT a MySQL, Run-Query a Mixpanel (proyecto [ver .env], sin bots)
3. **Cruzar** — Agrupar por colegio_rbd y user_id en ambas fuentes
4. **Analizar** — Interpretar datos, detectar patrones y anomalias
5. **Presentar** — Dashboard HTML estandar (template) o tabla en chat
6. **Recomendar** — Plan de accion P0/P1/P2 con evidencia y metrica de exito

Cada dato debe incluir: fecha de consulta, rango temporal, fuente.

## Momentos Clave (Mixpanel)

- **Page View** = usuario ABRE un informe (con form-name)
- **Form Saved** = usuario GUARDA un informe (con form-name)
- **Form Download** = usuario DESCARGA un informe
- Funnel natural: Page View → Form Saved → Form Download

## Filtros Obligatorios

- **Bots Mixpanel:** Excluir 7 ciudades (Dulles, Cheyenne, Chicago, Phoenix, Des Moines, Boydton, San Jose)
- **Proyecto Mixpanel:** Siempre [ver .env] (beta), nunca [ver .env] (produccion)
- **Catalogo NEE:** Usar tabla derivada normalizada (no CASE WHEN suelto)
