# Cross-Query: Tracking Health

> **Objetivo:** Medir la integridad del tracking comparando registros MySQL vs eventos Mixpanel
> **Actualizado:** 2026-09-10 (Fase 3 — queries validados)

---

## Concepto

```
Tracking Health = cobertura de Mixpanel sobre la actividad real del sistema

Cobertura global = Eventos Mixpanel (con RBD) / Acciones MySQL (registro_pie)
Baseline 2026-09-10: 1,214 / 10,829 = 11.2%
```

**Importante:** El Tracking Health NO es un ratio 1:1 entre eventos y registros. Mixpanel solo trackea un subconjunto de acciones (FUR Import/Indicator, FUDEI Sync, EPI/PPI). El `registro_pie_YYYY` captura TODAS las acciones.

---

## Procedimiento

### Paso 1: Actividad real MySQL (registro_pie)

```sql
-- Via MCP mysql-qa:
SELECT
  registro_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as total_acciones,
  COUNT(DISTINCT user_id) as usuarios_activos,
  MAX(registro_timestamp) as ultima_accion
FROM registro_pie_2026 rp
LEFT JOIN colegio c ON c.colegio_rbd = rp.registro_rbd
GROUP BY registro_rbd, c.colegio_nombre
ORDER BY total_acciones DESC;
```

### Paso 2: Formularios MySQL (FUR + FUDEI)

```sql
-- Via MCP mysql-qa:
SELECT
  cc.rbd, c.colegio_nombre, cc.is_canary,
  COALESCE(ft.cnt, 0) as fur_trans,
  COALESCE(fp.cnt, 0) as fur_perm,
  COALESCE(fd.cnt, 0) as fudei,
  COALESCE(ft.cnt, 0) + COALESCE(fp.cnt, 0) + COALESCE(fd.cnt, 0) as total_form
FROM colegio_config cc
LEFT JOIN colegio c ON c.colegio_rbd = cc.rbd
LEFT JOIN (SELECT form_rbd, COUNT(*) as cnt FROM fur_transitorio WHERE form_anio = 2026 GROUP BY form_rbd) ft ON ft.form_rbd = cc.rbd
LEFT JOIN (SELECT form_rbd, COUNT(*) as cnt FROM fur_permanente WHERE form_anio = 2026 GROUP BY form_rbd) fp ON fp.form_rbd = cc.rbd
LEFT JOIN (SELECT form_rbd, COUNT(*) as cnt FROM pie_form_fudei WHERE form_anio = 2026 GROUP BY form_rbd) fd ON fd.form_rbd = cc.rbd
WHERE cc.anio = 2026
ORDER BY total_form DESC;
```

### Paso 3: Eventos Mixpanel por colegio_rbd (sin bots)

```
Via MCP mixpanel -> Run-Query:
project_id: 3443728 (Integratepie-beta)
report_type: insights
Metricas: $all_events (total + unique)
Breakdown: colegio_rbd (propertyType: number) — NO usar 'rbd' (solo FUR)
Filtros: excluir 7 ciudades bot
Periodo: 90 dias
```

### Paso 3b: Cruce por usuario (user_id)

```
Breakdown: user_id (propertyType: number)
Nota: user_ids > 518 son de produccion y no existen en users de inteduc_beta
Cruzar con: SELECT id, name, email FROM users WHERE id IN (...)
```

### Paso 4: Calcular y comparar

| RBD | MySQL acciones | MySQL formularios | Mixpanel eventos | Cobertura | Veredicto |
|-----|---------------|-------------------|-----------------|-----------|-----------|
| X | registro_pie | FUR+FUDEI | Run-Query | eventos/acciones | Ver tabla abajo |

### Interpretacion

| Patron | Significado | Accion |
|--------|------------|--------|
| MySQL >> Mixpanel | Normal — Mixpanel solo cubre FUR/FUDEI/EPI | Ninguna |
| Mixpanel >> MySQL formularios | Re-imports o testing | Verificar registro_pie para confirmar |
| MySQL > 0, Mixpanel = 0 | Sin tracking para ese colegio | Verificar si tracking estaba desplegado |
| MySQL = 0, Mixpanel > 0 | Eventos sin persistencia | Investigar con registro_pie |

---

## Mapeo Informe <-> Evento <-> Tabla

| Informe | Evento Mixpanel | Tabla MySQL | colegio_rbd | user_id | rut | form_id |
|---------|----------------|-------------|-------------|---------|-----|---------|
| FUR Speech | FUR Speech Import Completed | fur_transitorio | Si | Si | Si | Si |
| FUR Psychoped | FUR Psychoped Import Completed | fur_transitorio | Si | Si | Si | Si |
| FUR Kine TO | FUR Kine TO Import Completed | fur_transitorio | Si | Si | Si | Si |
| FUR TL Deficit | FUR TL Deficit Import Completed | fur_transitorio | Si | Si | Si | Si |
| FUR Permanente | SIN TRACKING | fur_permanente | — | — | — | — |
| FUDEI Pre-Sync | Fudei Pre-Sync Validation Shown | pie_form_fudei | **Si** | Si | Si | Si |
| FUDEI Sync | Fudei Sync Secret | pie_form_fudei | **Si** | Si | Si | — |
| EPI | EPI Generated Report | informes + informe_valor | **Si** | Si | Si | — |
| PPI | PPI Generated Report | informes + informe_valor | **Si** | Si | Si | — |
| Libro de Registro | SIN TRACKING | pie_form_libro_registro | — | — | — | — |
| PAEC | SIN TRACKING | (registro_pie acciones) | — | — | — | — |

> **CORRECCION (2026-09-10):** TODOS los eventos tienen `colegio_rbd`. El error anterior fue usar
> la propiedad `rbd` (solo FUR) en lugar de `colegio_rbd` (universal). EPI, PPI y FUDEI SI son
> cruzables por colegio.

---

## Baseline (2026-09-10)

| Metrica | Valor |
|---------|-------|
| Cobertura global Mixpanel | 11.2% |
| Eventos con RBD trackeados | FUR Speech/Psychoped/Kine TO/TL Deficit |
| Eventos SIN RBD | EPI, PPI, FUDEI |
| Modulos SIN tracking | FUR Permanente, Libro de Registro, PAEC, Pautas, EP MINEDUC |
| Bot traffic | 39.6% de eventos totales |
