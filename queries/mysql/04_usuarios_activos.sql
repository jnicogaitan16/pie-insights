-- ============================================================
-- USUARIOS ACTIVOS — Análisis de actividad por usuario
-- Objetivo: Medir quién usa el sistema y con qué frecuencia
-- Ejecutar via MCP mysql-qa
-- Actualizado: 2026-09-10 (Fase 3 — nombres corregidos, registro_pie agregado)
-- ============================================================
-- NOTA: tabla perfil usa perfil_id, perfil_nombre, perfil_slug, perfil_rbd

-- 1. Usuarios del sistema (todos)
SELECT
  u.id,
  u.name,
  u.email,
  pu.rbd,
  c.colegio_nombre,
  p.perfil_nombre as perfil
FROM users u
LEFT JOIN perfil_user pu ON pu.user_id = u.id
LEFT JOIN colegio c ON c.colegio_rbd = pu.rbd
LEFT JOIN perfil p ON p.perfil_id = pu.perfil_id
ORDER BY pu.rbd, u.name;

-- 2. Usuarios por colegio (para cruzar con Mixpanel)
SELECT
  pu.rbd,
  c.colegio_nombre,
  COUNT(DISTINCT pu.user_id) as usuarios_registrados,
  GROUP_CONCAT(DISTINCT p.perfil_nombre ORDER BY p.perfil_nombre) as perfiles
FROM perfil_user pu
LEFT JOIN colegio c ON c.colegio_rbd = pu.rbd
LEFT JOIN perfil p ON p.perfil_id = pu.perfil_id
WHERE pu.rbd > 0
GROUP BY pu.rbd, c.colegio_nombre
ORDER BY usuarios_registrados DESC;

-- 3. Perfiles disponibles en el sistema
SELECT perfil_id, perfil_nombre FROM perfil ORDER BY perfil_id;

-- 4. Distribución de usuarios por perfil
SELECT
  p.perfil_nombre as perfil,
  COUNT(*) as total_asignaciones,
  COUNT(DISTINCT pu.user_id) as usuarios_unicos,
  COUNT(DISTINCT pu.rbd) as colegios_unicos
FROM perfil_user pu
JOIN perfil p ON p.perfil_id = pu.perfil_id
GROUP BY p.perfil_nombre
ORDER BY total_asignaciones DESC;

-- 5. Actividad real por colegio (registro_pie — log de acciones)
-- Reemplazar {ANIO} por el año deseado (ej: 2026)
SELECT
  registro_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as total_acciones,
  COUNT(DISTINCT user_id) as usuarios_activos,
  MIN(registro_timestamp) as primera_accion,
  MAX(registro_timestamp) as ultima_accion,
  DATEDIFF(NOW(), MAX(registro_timestamp)) as dias_desde_ultima
FROM registro_pie_2026 rp
LEFT JOIN colegio c ON c.colegio_rbd = rp.registro_rbd
GROUP BY registro_rbd, c.colegio_nombre
ORDER BY total_acciones DESC;

-- 6. Actividad ultimo 30 dias (registro_pie)
SELECT
  registro_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as acciones_30d,
  COUNT(DISTINCT user_id) as usuarios_activos
FROM registro_pie_2026 rp
LEFT JOIN colegio c ON c.colegio_rbd = rp.registro_rbd
WHERE registro_timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY registro_rbd, c.colegio_nombre
ORDER BY acciones_30d DESC;

-- 7. Tendencia mensual por colegio (registro_pie)
SELECT
  registro_rbd as rbd,
  DATE_FORMAT(registro_timestamp, '%Y-%m') as mes,
  COUNT(*) as acciones,
  COUNT(DISTINCT user_id) as usuarios
FROM registro_pie_2026
GROUP BY registro_rbd, DATE_FORMAT(registro_timestamp, '%Y-%m')
ORDER BY registro_rbd, mes;
