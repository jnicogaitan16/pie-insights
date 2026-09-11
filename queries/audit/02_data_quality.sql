-- ============================================================
-- AUDITORÍA DE CALIDAD DE DATOS — MySQL
-- Objetivo: Verificar integridad y calidad de datos en la BD
-- Ejecutar via Python/pymysql
-- Actualizado: 2026-09-10 (Fase 0 — nombres reales)
-- ============================================================

-- 1. Top 30 tablas por tamaño
SELECT
  TABLE_NAME,
  TABLE_ROWS,
  ROUND(DATA_LENGTH / 1024 / 1024, 2) as size_mb,
  CREATE_TIME,
  UPDATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'inteduc_beta'
ORDER BY TABLE_ROWS DESC
LIMIT 30;

-- 2. Usuarios de prueba vs reales
SELECT
  CASE
    WHEN email LIKE '%test%' OR email LIKE '%prueba%' OR email LIKE '%demo%' OR email LIKE '%example%'
    THEN 'Test/Demo'
    ELSE 'Real'
  END as tipo_usuario,
  COUNT(*) as cantidad
FROM users
GROUP BY tipo_usuario;

-- 3. Colegios activos con config PIE vs total catálogo
SELECT
  'Total catalogo' as categoria,
  COUNT(*) as cantidad
FROM colegio
UNION ALL
SELECT
  'Con config PIE' as categoria,
  COUNT(DISTINCT rbd) as cantidad
FROM colegio_config
UNION ALL
SELECT
  'Con FUR 2026' as categoria,
  COUNT(DISTINCT form_rbd) as cantidad
FROM (
  SELECT form_rbd FROM fur_transitorio WHERE form_anio = 2026
  UNION
  SELECT form_rbd FROM fur_permanente WHERE form_anio = 2026
) fur_rbds
UNION ALL
SELECT
  'Con FUDEI 2026' as categoria,
  COUNT(DISTINCT form_rbd) as cantidad
FROM pie_form_fudei WHERE form_anio = 2026;

-- 4. Registros por mes (últimos 6 meses) — FUR Transitorio
SELECT
  DATE_FORMAT(form_generado, '%Y-%m') as mes,
  COUNT(*) as registros,
  COUNT(DISTINCT form_rbd) as colegios,
  COUNT(DISTINCT alumno_rut) as alumnos
FROM fur_transitorio
WHERE form_generado >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY DATE_FORMAT(form_generado, '%Y-%m')
ORDER BY mes;

-- 5. Colegios canary vs estándar
SELECT
  is_canary,
  COUNT(*) as colegios,
  GROUP_CONCAT(rbd ORDER BY rbd) as rbds
FROM colegio_config
WHERE anio = 2026
GROUP BY is_canary;
