-- ============================================================
-- BASELINE DE INFORMES — Registros reales por tipo
-- Objetivo: Establecer la verdad de la BD para cada informe
-- Ejecutar via Python/pymysql
-- Actualizado: 2026-09-10 (Fase 0 — nombres reales descubiertos)
-- ============================================================

-- 1. FUR Transitorio por año y colegio (Speech, Psychoped, Kine TO, TL Deficit)
SELECT
  form_anio as anio,
  form_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as total_registros,
  COUNT(DISTINCT alumno_rut) as alumnos_unicos,
  MIN(form_generado) as primer_registro,
  MAX(form_generado) as ultimo_registro
FROM fur_transitorio ft
LEFT JOIN colegio c ON c.colegio_rbd = ft.form_rbd
WHERE form_anio >= 2025
GROUP BY form_anio, form_rbd, c.colegio_nombre
ORDER BY form_anio DESC, total_registros DESC;

-- 2. FUR Permanente por año y colegio
SELECT
  form_anio as anio,
  form_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as total_registros,
  COUNT(DISTINCT alumno_rut) as alumnos_unicos,
  MIN(form_generado) as primer_registro,
  MAX(form_generado) as ultimo_registro
FROM fur_permanente fp
LEFT JOIN colegio c ON c.colegio_rbd = fp.form_rbd
WHERE form_anio >= 2025
GROUP BY form_anio, form_rbd, c.colegio_nombre
ORDER BY form_anio DESC, total_registros DESC;

-- 3. FUDEI por año y colegio
SELECT
  form_anio as anio,
  form_rbd as rbd,
  c.colegio_nombre,
  COUNT(*) as total_registros,
  COUNT(DISTINCT alumno_rut) as alumnos_unicos
FROM pie_form_fudei pf
LEFT JOIN colegio c ON c.colegio_rbd = pf.form_rbd
WHERE form_anio >= 2025
GROUP BY form_anio, form_rbd, c.colegio_nombre
ORDER BY form_anio DESC, total_registros DESC;

-- 4. Informes especializados: conteo por tipo
--    (pie_form_informe_psicologico, pie_form_informe_fonoaudiologico, etc.)
SELECT 'Psicologico' as tipo, COUNT(*) as total FROM pie_form_informe_psicologico
UNION ALL SELECT 'Fonoaudiologico', COUNT(*) FROM pie_form_informe_fonoaudiologico
UNION ALL SELECT 'Fono IDTEL', COUNT(*) FROM pie_form_informe_fonoaudiologico_idtel
UNION ALL SELECT 'Pedagogico', COUNT(*) FROM pie_form_informe_pedagogico
UNION ALL SELECT 'Psicopedagogico', COUNT(*) FROM pie_form_informe_psicopedagogico
UNION ALL SELECT 'Psicoeducativo', COUNT(*) FROM pie_form_informe_psicoeducativo
UNION ALL SELECT 'TADI', COUNT(*) FROM pie_form_informe_tadi
UNION ALL SELECT 'ICAP', COUNT(*) FROM pie_form_informe_icap
UNION ALL SELECT 'IDEA', COUNT(*) FROM pie_form_informe_idea
UNION ALL SELECT 'PEFE', COUNT(*) FROM pie_form_informe_pefe
UNION ALL SELECT 'Terapia Ocupacional', COUNT(*) FROM pie_form_informe_terapia_ocupacional
UNION ALL SELECT 'Eval Psicoped MINEDUC', COUNT(*) FROM pie_form_informe_evaluacion_psicopedagogica_mineduc
UNION ALL SELECT 'Pauta Obs Ped MINEDUC', COUNT(*) FROM pie_form_informe_pauta_observacion_pedagogica_mineduc
ORDER BY total DESC;

-- 5. Colegios activos con configuración PIE (referencia)
SELECT rbd, anio, is_canary
FROM colegio_config
WHERE anio >= 2025
ORDER BY anio DESC, rbd;
