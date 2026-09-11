-- ============================================================
-- RANKING DE COLEGIOS — Top colegios por uso real
-- Objetivo: Identificar colegios champions y rezagados
-- Ejecutar via Python/pymysql
-- Actualizado: 2026-09-10 (Fase 0 — nombres reales)
-- ============================================================

-- 1. Top colegios por FUR (transitorio + permanente) en 2026
SELECT
  form_rbd as rbd,
  c.colegio_nombre,
  SUM(CASE WHEN src = 'transitorio' THEN cnt ELSE 0 END) as fur_transitorio,
  SUM(CASE WHEN src = 'permanente' THEN cnt ELSE 0 END) as fur_permanente,
  SUM(cnt) as total_fur,
  SUM(alumnos) as alumnos_unicos
FROM (
  SELECT form_rbd, 'transitorio' as src, COUNT(*) as cnt, COUNT(DISTINCT alumno_rut) as alumnos
  FROM fur_transitorio WHERE form_anio = 2026 GROUP BY form_rbd
  UNION ALL
  SELECT form_rbd, 'permanente' as src, COUNT(*) as cnt, COUNT(DISTINCT alumno_rut) as alumnos
  FROM fur_permanente WHERE form_anio = 2026 GROUP BY form_rbd
) combined
LEFT JOIN colegio c ON c.colegio_rbd = combined.form_rbd
GROUP BY form_rbd, c.colegio_nombre
ORDER BY total_fur DESC;

-- 2. Top colegios por FUDEI en 2026
SELECT
  form_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as total_fudei,
  COUNT(DISTINCT alumno_rut) as alumnos_unicos
FROM pie_form_fudei pf
LEFT JOIN colegio c ON c.colegio_rbd = pf.form_rbd
WHERE form_anio = 2026
GROUP BY form_rbd, c.colegio_nombre
ORDER BY total_fudei DESC;

-- 3. Colegios con config activa pero SIN FUR en 2026 (riesgo de churn)
SELECT
  cc.rbd,
  c.colegio_nombre,
  cc.anio,
  cc.is_canary,
  COALESCE(ft.cnt, 0) as fur_transitorios,
  COALESCE(fp.cnt, 0) as fur_permanentes
FROM colegio_config cc
LEFT JOIN colegio c ON c.colegio_rbd = cc.rbd
LEFT JOIN (
  SELECT form_rbd, COUNT(*) as cnt FROM fur_transitorio WHERE form_anio = 2026 GROUP BY form_rbd
) ft ON ft.form_rbd = cc.rbd
LEFT JOIN (
  SELECT form_rbd, COUNT(*) as cnt FROM fur_permanente WHERE form_anio = 2026 GROUP BY form_rbd
) fp ON fp.form_rbd = cc.rbd
WHERE cc.anio = 2026
  AND COALESCE(ft.cnt, 0) = 0
  AND COALESCE(fp.cnt, 0) = 0
ORDER BY cc.rbd;

-- 4. Distribución geográfica de colegios con FUR activo
SELECT
  r.nombre as region,
  COUNT(DISTINCT combined.form_rbd) as colegios_activos,
  SUM(combined.cnt) as total_fur
FROM (
  SELECT form_rbd, COUNT(*) as cnt FROM fur_transitorio WHERE form_anio = 2026 GROUP BY form_rbd
  UNION ALL
  SELECT form_rbd, COUNT(*) as cnt FROM fur_permanente WHERE form_anio = 2026 GROUP BY form_rbd
) combined
LEFT JOIN colegio c ON c.colegio_rbd = combined.form_rbd
LEFT JOIN region r ON r.id = c.colegio_cod_region
GROUP BY r.nombre
ORDER BY colegios_activos DESC;
