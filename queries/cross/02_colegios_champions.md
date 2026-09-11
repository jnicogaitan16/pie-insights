# Cross-Query: Ranking de Colegios

> **Objetivo:** Clasificar colegios cruzando actividad MySQL (registro_pie + formularios) con Mixpanel
> **Actualizado:** 2026-09-10 (Fase 3 — queries validados)

---

## Procedimiento

### Paso 1: Ranking completo MySQL (query principal)

```sql
-- Via MCP mysql-qa:
SELECT
  cc.rbd, c.colegio_nombre, cc.is_canary,
  COALESCE(rp.total_acciones, 0) as acciones_2026,
  COALESCE(rp.usuarios_activos, 0) as usuarios_activos,
  COALESCE(rp.ultima_accion, 'Sin actividad') as ultima_accion,
  COALESCE(ft.cnt, 0) as fur_trans,
  COALESCE(fp.cnt, 0) as fur_perm,
  COALESCE(fd.cnt, 0) as fudei,
  COALESCE(ft.cnt, 0) + COALESCE(fp.cnt, 0) + COALESCE(fd.cnt, 0) as total_formularios
FROM colegio_config cc
LEFT JOIN colegio c ON c.colegio_rbd = cc.rbd
LEFT JOIN (
  SELECT registro_rbd, COUNT(*) as total_acciones, COUNT(DISTINCT user_id) as usuarios_activos,
    MAX(registro_timestamp) as ultima_accion
  FROM registro_pie_2026 GROUP BY registro_rbd
) rp ON rp.registro_rbd = cc.rbd
LEFT JOIN (SELECT form_rbd, COUNT(*) as cnt FROM fur_transitorio WHERE form_anio = 2026 GROUP BY form_rbd) ft ON ft.form_rbd = cc.rbd
LEFT JOIN (SELECT form_rbd, COUNT(*) as cnt FROM fur_permanente WHERE form_anio = 2026 GROUP BY form_rbd) fp ON fp.form_rbd = cc.rbd
LEFT JOIN (SELECT form_rbd, COUNT(*) as cnt FROM pie_form_fudei WHERE form_anio = 2026 GROUP BY form_rbd) fd ON fd.form_rbd = cc.rbd
WHERE cc.anio = 2026
ORDER BY acciones_2026 DESC;
```

### Paso 2: Actividad reciente (ultimo 30 dias)

```sql
-- Via MCP mysql-qa:
SELECT
  registro_rbd as rbd, c.colegio_nombre,
  COUNT(*) as acciones_30d,
  COUNT(DISTINCT user_id) as usuarios_activos,
  MAX(registro_timestamp) as ultima_accion
FROM registro_pie_2026 rp
LEFT JOIN colegio c ON c.colegio_rbd = rp.registro_rbd
WHERE registro_timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY registro_rbd, c.colegio_nombre
ORDER BY acciones_30d DESC;
```

### Paso 3: Eventos Mixpanel por RBD

```
Via MCP mixpanel -> Run-Query:
project_id: 3443728
Metricas: $all_events total + unique
Breakdown: rbd
Filtros: 7 ciudades bot excluidas
Periodo: 90 dias
```

### Paso 4: Clasificar

| Clasificacion | Criterio |
|---------------|----------|
| **CHAMPION** | >1,000 acciones/mes, >3 usuarios, formularios completados, actividad constante |
| **ADOPTANTE TEMPRANO** | Uso real sostenido, formularios creados, 1+ usuario real |
| **TESTING CON POTENCIAL** | Actividad reciente creciente, multiples usuarios, algun formulario |
| **TESTING** | Actividad esporadica, datos de prueba evidentes |
| **BAJO ENGAGEMENT** | Config activa, <50 acciones totales, sin formularios |
| **DECLINANDO** | Actividad historica significativa pero caida >80% en ultimo mes |
| **CHURN** | Sin actividad en >60 dias |

---

## Baseline (2026-09-10)

| # | RBD | Colegio | Clasificacion | Acciones | Formularios | Ultimo 30d |
|---|-----|---------|---------------|----------|-------------|------------|
| 1 | 8474 | Liceo Inteduc | CHAMPION | 9,923 | 70 | 1,172 |
| 2 | 151 | Cinderella S School | ADOPTANTE | 220 | 4 | 45 |
| 3 | 8881 | Colegio Apoquindo | TESTING-DECLINANDO | 203 | 0 | 1 |
| 4 | 26372 | San Lucas Test | TESTING | 200 | 1 | 8 |
| 5 | 4268 | Esc. Adventista | CHURN | 150 | 1 | 0 |
| 6 | 9308 | Mayflower School | TESTING CON POTENCIAL | 88 | 1 | 18 |
| 7 | 8718 | Esc. Danes | BAJO ENGAGEMENT | 45 | 0 | 6 |
