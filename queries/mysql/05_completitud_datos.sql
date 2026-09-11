-- ============================================================
-- COMPLETITUD DE DATOS — Porcentaje de registros completos
-- Objetivo: Medir calidad de los datos persistidos
-- Ejecutar via Python/pymysql
-- Actualizado: 2026-09-10 (Fase 0 — nombres reales)
-- ============================================================

-- 1. Estado de FUR Transitorio por año
SELECT
  form_anio as anio,
  form_estado,
  COUNT(*) as cantidad
FROM fur_transitorio
WHERE form_anio >= 2024
GROUP BY form_anio, form_estado
ORDER BY form_anio DESC, form_estado;

-- 2. Estado de FUR Permanente por año
SELECT
  form_anio as anio,
  form_estado,
  COUNT(*) as cantidad
FROM fur_permanente
WHERE form_anio >= 2024
GROUP BY form_anio, form_estado
ORDER BY form_anio DESC, form_estado;

-- 3. Completitud de campos en FUR Transitorio (2026)
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN form_rbd = 0 THEN 1 ELSE 0 END) as sin_rbd,
  SUM(CASE WHEN alumno_rut = 0 THEN 1 ELSE 0 END) as sin_alumno,
  SUM(CASE WHEN form_generado IS NULL THEN 1 ELSE 0 END) as sin_fecha,
  SUM(CASE WHEN diagnostico_actual = 0 THEN 1 ELSE 0 END) as sin_diagnostico,
  ROUND(SUM(CASE WHEN form_rbd = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_sin_rbd
FROM fur_transitorio
WHERE form_anio = 2026;

-- 4. Estado de FUDEI por año
SELECT
  form_anio as anio,
  form_estado,
  estado_mineduc,
  COUNT(*) as cantidad
FROM pie_form_fudei
WHERE form_anio >= 2024
GROUP BY form_anio, form_estado, estado_mineduc
ORDER BY form_anio DESC, form_estado;

-- 5. Registros huérfanos: FUR sin colegio válido
SELECT
  'FUR Trans sin colegio' as tipo,
  COUNT(*) as total
FROM fur_transitorio ft
LEFT JOIN colegio c ON c.colegio_rbd = ft.form_rbd
WHERE c.colegio_id IS NULL AND ft.form_rbd > 0
UNION ALL
SELECT
  'FUR Perm sin colegio' as tipo,
  COUNT(*) as total
FROM fur_permanente fp
LEFT JOIN colegio c ON c.colegio_rbd = fp.form_rbd
WHERE c.colegio_id IS NULL AND fp.form_rbd > 0;

-- 6. Top 30 tablas por tamaño (dimensionar la BD)
SELECT
  TABLE_NAME,
  TABLE_ROWS,
  ROUND(DATA_LENGTH / 1024 / 1024, 2) as size_mb
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'inteduc_beta'
ORDER BY TABLE_ROWS DESC
LIMIT 30;
