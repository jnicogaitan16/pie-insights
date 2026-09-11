# Cross-Query: Colegios en Riesgo de Churn

> **Objetivo:** Identificar colegios con config activa pero sin uso reciente
> **Actualizado:** 2026-09-10 (Fase 3 — queries validados)

---

## Procedimiento

### Paso 1: Colegios configurados vs ultima actividad

```sql
-- Via MCP mysql-qa:
SELECT
  cc.rbd, c.colegio_nombre, cc.is_canary,
  COALESCE(rp.total_acciones, 0) as acciones_totales,
  COALESCE(rp.ultima_accion, 'Sin actividad') as ultima_accion,
  CASE
    WHEN rp.ultima_accion IS NULL THEN 'SIN ACTIVIDAD'
    WHEN DATEDIFF(NOW(), rp.ultima_accion) > 60 THEN 'CHURN'
    WHEN DATEDIFF(NOW(), rp.ultima_accion) > 30 THEN 'RIESGO ALTO'
    ELSE 'ACTIVO'
  END as estado_churn,
  COALESCE(DATEDIFF(NOW(), rp.ultima_accion), 999) as dias_inactivo,
  COALESCE(r30.acciones_30d, 0) as acciones_ultimo_30d
FROM colegio_config cc
LEFT JOIN colegio c ON c.colegio_rbd = cc.rbd
LEFT JOIN (
  SELECT registro_rbd, COUNT(*) as total_acciones, MAX(registro_timestamp) as ultima_accion
  FROM registro_pie_2026 GROUP BY registro_rbd
) rp ON rp.registro_rbd = cc.rbd
LEFT JOIN (
  SELECT registro_rbd, COUNT(*) as acciones_30d
  FROM registro_pie_2026
  WHERE registro_timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
  GROUP BY registro_rbd
) r30 ON r30.registro_rbd = cc.rbd
WHERE cc.anio = 2026
ORDER BY dias_inactivo DESC;
```

### Paso 2: Colegios fuera de config con actividad historica

```sql
-- Colegios que usaron la plataforma pero no renovaron config:
SELECT
  rp.registro_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as acciones,
  COUNT(DISTINCT user_id) as usuarios,
  MAX(registro_timestamp) as ultima_accion
FROM registro_pie_2026 rp
LEFT JOIN colegio c ON c.colegio_rbd = rp.registro_rbd
WHERE rp.registro_rbd NOT IN (SELECT rbd FROM colegio_config WHERE anio = 2026)
GROUP BY rp.registro_rbd, c.colegio_nombre
ORDER BY acciones DESC;
```

### Paso 3: Clasificar riesgo

| Dias inactivo | Acciones 30d | Riesgo | Accion |
|---------------|-------------|--------|--------|
| > 60 dias | 0 | **CRITICO** | Contacto inmediato — confirmar abandono |
| 30-60 dias | 0 | **ALTO** | Contacto esta semana |
| 30-60 dias | > 0 | **MEDIO** | Monitorear tendencia |
| < 30 dias | > 0 | **BAJO** | Normal |
| Sin config | Historico > 0 | **OPORTUNIDAD** | Contactar para reactivar |

---

## Baseline (2026-09-10)

### Churn confirmado
| RBD | Colegio | Ultima actividad | Dias inactivo |
|-----|---------|-----------------|---------------|
| 4268 | Escuela Adventista | 2026-02-20 | 202 dias |

### Riesgo medio
| RBD | Colegio | Ultima actividad | Tendencia |
|-----|---------|-----------------|-----------|
| 8881 | Colegio Apoquindo | 2026-08-25 | 190 acc en marzo -> 1 en agosto |

### Churned sin config (oportunidad de reactivacion)
| RBD | Colegio | Acciones 2026 | Ultima actividad |
|-----|---------|--------------|-----------------|
| 9020 | Colegio Santa Catalina | 149 | 2026-02 |
| 16589 | Colegio El Quillay | 29 | 2026-06 |
| 10833 | Centro Educacional Menesiano | 5 | 2026-01 |
