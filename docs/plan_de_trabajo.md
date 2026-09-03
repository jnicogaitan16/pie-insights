# Plan de Trabajo — PIE-Insights

**Proyecto:** Sistema de metricas post-deploy para IntegratePIE
**Inicio:** Septiembre 2026
**Metodologia:** Sprints de 1 semana, entregables incrementales
**Stack:** Python 3.11+ / Mixpanel API / GitHub Actions

---

## Resumen Ejecutivo

PIE-Insights automatiza la respuesta a: "El deploy fue exitoso?" consultando la API de Mixpanel para medir adopcion, uso y comportamiento de usuarios post-release en IntegratePIE.

### Feature piloto: Certificado de Egreso PIE
- **Evento Mixpanel:** `Page View` con `form-name = "Certificado de Egreso PIE"`
- **KPIs objetivo:** 50 usuarios unicos / 10 colegios activos en 7 dias

---

## Sprint 0 — Setup y Conexion (Semana 1)

**Objetivo:** Proyecto funcional con conexion verificada a Mixpanel API.

### Tareas

| # | Tarea | Archivo | Criterio de aceptacion |
|---|-------|---------|----------------------|
| 0.1 | Inicializar repo Git | `.gitignore`, `README.md` | Repo limpio, sin secrets |
| 0.2 | Crear estructura de carpetas | `src/`, `tests/`, `config/`, `docs/` | Estructura segun README |
| 0.3 | Configurar entorno virtual | `requirements.txt`, `env/` | `pip install -r requirements.txt` sin errores |
| 0.4 | Crear `.env.example` | `.env.example` | Documentado con todos los campos necesarios |
| 0.5 | Implementar cliente Mixpanel | `src/client.py` | Clase `MixpanelClient` con autenticacion |
| 0.6 | Implementar healthcheck | `src/healthcheck.py` | `python -m src.healthcheck` retorna OK/ERROR |
| 0.7 | Test de conexion | `tests/test_client.py` | Test pasa con credenciales validas |

### Detalle tecnico — `src/client.py`

```python
"""
Cliente para la API de Mixpanel.
Endpoints principales:
- GET /api/query/insights — Insights query
- GET /api/2.0/segmentation — Segmentation
- GET /api/2.0/export — Raw event export
- GET /api/2.0/funnels — Funnels

Autenticacion: Basic Auth con Service Account
Doc: https://developer.mixpanel.com/reference/authentication
"""
```

### Entregable Sprint 0
- `python -m src.healthcheck` conecta a Mixpanel y retorna status OK
- Tests pasan: `pytest tests/test_client.py`

---

## Sprint 1 — Consultas Base (Semana 2)

**Objetivo:** Poder consultar eventos, segmentar por propiedades, y obtener datos crudos.

### Tareas

| # | Tarea | Archivo | Criterio de aceptacion |
|---|-------|---------|----------------------|
| 1.1 | Query de eventos por nombre y rango de fechas | `src/queries/events.py` | Retorna conteo de eventos filtrado |
| 1.2 | Segmentacion por propiedad | `src/queries/segmentation.py` | Segmentar por `form-name`, `colegio`, `rut` |
| 1.3 | Query de usuarios unicos | `src/queries/events.py` | Contar distintos `distinct_id` por evento |
| 1.4 | Query de colegios unicos | `src/queries/events.py` | Contar distintos `rbd` por evento |
| 1.5 | Tests de queries | `tests/test_queries.py` | Mocks de API responses, tests pasan |
| 1.6 | CLI basico para queries | `src/queries/events.py` | `python -m src.queries.events --event "Page View" --days 7` |

### Endpoints Mixpanel a usar

| Endpoint | Uso | Doc |
|----------|-----|-----|
| `/api/query/insights` | Eventos agregados, conteo, unicos | [Insights Query](https://developer.mixpanel.com/reference/insights-query) |
| `/api/2.0/segmentation` | Desglose por propiedad | [Segmentation](https://developer.mixpanel.com/reference/segmentation) |
| `/api/2.0/export` | Eventos crudos (backup) | [Export](https://developer.mixpanel.com/reference/raw-event-export) |

### Entregable Sprint 1
- CLI funcional: `python -m src.queries.events --event "Page View" --days 7`
- Output: tabla con fecha, evento, count, usuarios unicos

---

## Sprint 2 — Reporte de Adopcion (Semana 3)

**Objetivo:** Generar reporte automatico de adopcion post-deploy para una feature.

### Tareas

| # | Tarea | Archivo | Criterio de aceptacion |
|---|-------|---------|----------------------|
| 2.1 | Definir schema de features | `config/features.json` | JSON con nombre, deploy_date, eventos, filtros, KPIs |
| 2.2 | Cargar config de features | `src/config.py` | Leer y validar `features.json` |
| 2.3 | Logica de reporte de adopcion | `src/reports/adoption.py` | Calcular metricas vs KPIs, generar veredicto |
| 2.4 | Output en consola formateado | `src/reports/adoption.py` | Tabla legible con metricas y status |
| 2.5 | Output en Markdown | `src/reports/adoption.py` | Archivo `.md` con reporte completo |
| 2.6 | Tests del reporte | `tests/test_reports.py` | Tests con datos mock |

### Schema `config/features.json`

```json
{
  "features": [
    {
      "name": "Certificado de Egreso PIE",
      "deploy_date": "2026-09-01",
      "events": [
        {
          "name": "Page View",
          "filter": { "form-name": "Certificado de Egreso PIE" }
        },
        {
          "name": "Form Saved",
          "filter": { "form-name": "Certificado de Egreso PIE" }
        },
        {
          "name": "Form Download",
          "filter": { "form-name": "Certificado de Egreso PIE" }
        }
      ],
      "kpis": {
        "unique_users_7d": 50,
        "unique_schools_7d": 10,
        "total_events_7d": 200
      }
    }
  ]
}
```

### Formato del reporte

```
============================================================
REPORTE DE ADOPCION POST-DEPLOY
============================================================
Feature:          Certificado de Egreso PIE
Deploy:           2026-09-01
Periodo medido:   2026-09-01 → 2026-09-08 (7 dias)

METRICAS                    ACTUAL    TARGET    STATUS
------------------------------------------------------------
Usuarios unicos (7d)           63        50    ALCANZADO
Colegios activos (7d)          12        10    ALCANZADO
Eventos totales (7d)          187       200    PENDIENTE (93%)

DETALLE POR EVENTO
------------------------------------------------------------
Page View                      89 eventos / 63 usuarios
Form Saved                     61 eventos / 45 usuarios
Form Download                  37 eventos / 31 usuarios

VEREDICTO: EXITOSO (2/3 KPIs alcanzados)
============================================================
```

### Entregable Sprint 2
- `python -m src.reports.adoption --feature "Certificado de Egreso PIE" --days 7`
- Genera reporte en consola y opcionalmente en `reports/adoption_YYYY-MM-DD.md`

---

## Sprint 3 — Alertas y Notificaciones (Semana 4)

**Objetivo:** Notificar automaticamente cuando una feature no alcanza los KPIs.

### Tareas

| # | Tarea | Archivo | Criterio de aceptacion |
|---|-------|---------|----------------------|
| 3.1 | Logica de evaluacion de umbrales | `src/alerts/evaluator.py` | Comparar metricas vs KPIs, decidir alerta |
| 3.2 | Notificacion Slack | `src/alerts/slack.py` | Enviar mensaje a webhook con reporte resumido |
| 3.3 | Notificacion por consola/log | `src/alerts/logger.py` | Log estructurado de alertas |
| 3.4 | Comando para evaluar todas las features | `src/alerts/check_all.py` | `python -m src.alerts.check_all` |
| 3.5 | Tests de alertas | `tests/test_alerts.py` | Tests con mocks de Slack |

### Reglas de alerta

| Condicion | Nivel | Accion |
|-----------|-------|--------|
| 0% de KPIs alcanzados en 7d | CRITICO | Slack + log |
| <50% de KPIs alcanzados en 7d | ADVERTENCIA | Slack + log |
| >=50% de KPIs alcanzados | OK | Solo log |
| Sin eventos en 3d post-deploy | CRITICO | Slack inmediato |

### Entregable Sprint 3
- `python -m src.alerts.check_all` evalua todas las features y notifica
- Slack recibe mensaje formateado con veredicto

---

## Sprint 4 — Automatizacion (Semana 5)

**Objetivo:** Ejecutar los reportes y alertas de forma automatica y periodica.

### Tareas

| # | Tarea | Archivo | Criterio de aceptacion |
|---|-------|---------|----------------------|
| 4.1 | GitHub Action para reporte diario | `.github/workflows/daily-report.yml` | Ejecuta a las 9:00 AM Chile |
| 4.2 | GitHub Action para alerta post-deploy | `.github/workflows/post-deploy.yml` | Trigger manual o por webhook |
| 4.3 | Script principal unificado | `src/main.py` | `python -m src.main --mode report|alert|check` |
| 4.4 | Historial de reportes | `src/reports/history.py` | Guardar reportes en `reports/` con timestamp |
| 4.5 | Documentacion de uso | `README.md` | Actualizar con instrucciones finales |

### GitHub Action — Reporte diario

```yaml
name: Daily Adoption Report
on:
  schedule:
    - cron: '0 12 * * 1-5'  # 9:00 AM Chile (UTC-3), lunes a viernes
  workflow_dispatch:         # Trigger manual

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python -m src.main --mode report
        env:
          MIXPANEL_PROJECT_ID: ${{ secrets.MIXPANEL_PROJECT_ID }}
          MIXPANEL_API_SECRET: ${{ secrets.MIXPANEL_API_SECRET }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Entregable Sprint 4
- GitHub Action ejecuta reporte diario automaticamente
- Reportes se acumulan en `reports/`
- Slack recibe resumen diario

---

## Sprint 5 — Refinamiento y Expansion (Semana 6)

**Objetivo:** Agregar features secundarias, mejorar reportes, y expandir cobertura.

### Tareas

| # | Tarea | Archivo | Criterio de aceptacion |
|---|-------|---------|----------------------|
| 5.1 | Reporte de tendencia (7d, 14d, 30d) | `src/reports/trends.py` | Grafico de tendencia por feature |
| 5.2 | Comparacion entre features | `src/reports/comparison.py` | Tabla comparativa multi-feature |
| 5.3 | Agregar features adicionales a `features.json` | `config/features.json` | Al menos 3 features monitoreadas |
| 5.4 | Dashboard HTML simple | `templates/dashboard.html` | Reporte visual con Jinja2 |
| 5.5 | Documentacion final | `docs/` | Guia de como agregar nuevas features |

### Entregable Sprint 5
- Dashboard HTML con resumen de todas las features
- 3+ features monitoreadas
- Documentacion completa

---

## Resumen de Sprints

| Sprint | Semana | Objetivo | Entregable clave |
|--------|--------|----------|-----------------|
| 0 | 1 | Setup y conexion | `healthcheck` funcional |
| 1 | 2 | Consultas base | CLI de queries |
| 2 | 3 | Reporte de adopcion | Reporte post-deploy |
| 3 | 4 | Alertas | Notificaciones Slack |
| 4 | 5 | Automatizacion | GitHub Actions |
| 5 | 6 | Refinamiento | Dashboard + multi-feature |

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| No obtener API Secret a tiempo | Media | Alto | Usar Mixpanel Agent como fallback para validar queries |
| Rate limits de Mixpanel API | Baja | Medio | Implementar retry con backoff exponencial |
| Datos insuficientes en Mixpanel | Media | Alto | Validar con healthcheck que los eventos existen |
| Cambio de naming en eventos | Baja | Medio | Centralizar nombres en `config/features.json` |
| GitHub Actions sin secrets configurados | Baja | Medio | Probar localmente primero, CI despues |

---

## Dependencias

### Para empezar (Sprint 0)
- [x] Repo creado
- [x] Python 3.11+ instalado
- [x] Entorno virtual configurado
- [ ] **API Secret o Service Account de Mixpanel** (pedir al admin)
- [ ] **Project ID de Mixpanel** (visible en Project Settings)

### Para Sprint 3+
- [ ] Slack webhook URL (crear en el workspace del equipo)

### Para Sprint 4+
- [ ] Repo en GitHub (para Actions)
- [ ] Secrets configurados en GitHub repo settings

---

## Como agregar una nueva feature a monitorear

1. Abrir `config/features.json`
2. Agregar un nuevo objeto al array `features`:
   ```json
   {
     "name": "Nombre de la Feature",
     "deploy_date": "YYYY-MM-DD",
     "events": [
       { "name": "Page View", "filter": { "form-name": "..." } }
     ],
     "kpis": {
       "unique_users_7d": 50,
       "unique_schools_7d": 10
     }
   }
   ```
3. Ejecutar: `python -m src.reports.adoption --feature "Nombre de la Feature" --days 7`

---

## Criterios de Exito del Proyecto

- [ ] Conexion estable a Mixpanel API
- [ ] Reporte de adopcion funcional para al menos 1 feature
- [ ] Alertas automaticas cuando KPIs no se cumplen
- [ ] Ejecucion automatica via GitHub Actions
- [ ] Documentacion suficiente para que otro dev lo mantenga
