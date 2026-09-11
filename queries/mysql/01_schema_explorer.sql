-- ============================================================
-- EXPLORACIÓN DE SCHEMA — inteduc_beta
-- Objetivo: Mapear tablas relevantes para análisis post-deploy
-- Ejecutar via Python/pymysql (Azure MySQL 8.x)
-- Última actualización: 2026-09-10 (Fase 0 completada)
-- ============================================================

-- 1. Inventario general de tablas (232 tablas en inteduc_beta)
SHOW TABLES;

-- 2. Tablas FUR (9 tablas)
--    fur_transitorio (149 rows) — NEE Transitorias: Speech, Psychoped, Kine TO, TL Deficit
--    fur_permanente (118 rows) — NEE Permanentes
--    diagnostico_fur_* (7 tablas) — Diagnósticos específicos por discapacidad
SHOW TABLES LIKE '%fur%';

-- 3. Tablas FUDEI (3 tablas principales)
--    pie_form_fudei (286 rows) — Formulario FUDEI principal
--    pie_form_fudei_sync_trace (22 rows) — Trazabilidad de sincronización
--    proceso_fudei (5 rows) — Procesos de FUDEI
SHOW TABLES LIKE '%fudei%';

-- 4. Tablas de informes (pie_form_informe_*)
--    No hay tabla EPI/PPI dedicada. EPI y PPI se generan desde 'informes' (65 rows)
--    y se configuran en 'informe_valor' (374 rows) con rbd, rut, nee_id, informe_id
SHOW TABLES LIKE '%informe%';

-- 5. Tablas PAI (9 tablas, 112K+ rows en marcados)
SHOW TABLES LIKE '%pai%';

-- 6. Tabla de colegios
--    colegio (15,990 rows) — Catálogo nacional de colegios
--    Campo RBD: colegio_rbd (mediumint)
--    colegio_config (127 rows) — Colegios activos con configuración PIE
SHOW TABLES LIKE '%colegio%';

-- 7. Tablas de usuarios
--    users (501 rows) — Usuarios del sistema
--    perfil_user (1,164 rows) — Relación usuario-perfil con RBD
SHOW TABLES LIKE '%user%';

-- 8. Tablas de cursos
--    curso (2,170 rows) — Cursos por colegio
SHOW TABLES LIKE '%curso%';

-- ============================================================
-- MAPEO: Dónde está el campo RBD en cada tabla
-- ============================================================
-- colegio         → colegio_rbd (mediumint)
-- colegio_config  → rbd
-- fur_transitorio → form_rbd (mediumint)
-- fur_permanente  → form_rbd (mediumint)
-- pie_form_fudei  → form_rbd (mediumint)
-- perfil_user     → rbd
-- informe_valor   → rbd
-- ============================================================
