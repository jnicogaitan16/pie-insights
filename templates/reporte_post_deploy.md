# Reporte Post-Deploy: {INFORME}

> **Fecha:** {FECHA}
> **Período:** {FECHA_INICIO} → {FECHA_FIN} ({DIAS} días)
> **Ambiente:** Beta (inteduc_beta)

---

## 1. Resumen Ejecutivo

| Métrica | Valor | Target | Estado |
|---------|-------|--------|--------|
| Usuarios únicos | {X} | {TARGET} | {ALCANZADO/PENDIENTE} |
| Colegios únicos | {X} | {TARGET} | {ALCANZADO/PENDIENTE} |
| Eventos totales | {X} | — | Referencia |
| Registros MySQL | {X} | — | Verdad de BD |

**Veredicto:** {EXITOSO / BAJO USO / SIN ADOPCION / EN CRECIMIENTO / EN DECLIVE}

---

## 2. Datos MySQL (verdad de la BD)

| Métrica | Valor |
|---------|-------|
| Registros creados en período | {X} |
| Colegios con registros | {X} |
| Usuarios con registros | {X} |
| % registros completos | {X}% |

---

## 3. Datos Mixpanel (comportamiento)

| Métrica | Valor |
|---------|-------|
| Eventos totales (filtrado bots) | {X} |
| Usuarios únicos | {X} |
| Colegios con eventos | {X} |

### Desglose por acción
| Evento | Total | Usuarios únicos |
|--------|-------|----------------|
| {EVENTO_IMPORT} | {X} | {X} |
| {EVENTO_INDICATOR} | {X} | {X} |
| {EVENTO_TEXT} | {X} | {X} |

---

## 4. Cruce de Datos

### Tracking Health
```
Tracking Health = ({EVENTOS_MIXPANEL} / {REGISTROS_MYSQL}) × 100 = {X}%
Calificación: {SALUDABLE / PERDIDA MENOR / PERDIDA SIGNIFICATIVA}
```

### Colegios
| RBD | En MySQL | En Mixpanel | Estado |
|-----|---------|------------|--------|
| {RBD} | Si/No | Si/No | {OK / Sin tracking / Inactivo} |

---

## 5. Segmentación por Colegio

| RBD | Colegio | Registros BD | Eventos Mixpanel | Usuarios |
|-----|---------|-------------|-----------------|----------|
| {RBD} | {NOMBRE} | {X} | {X} | {X} |

---

## 6. Tendencia

{INSERTAR DESCRIPCION DE TENDENCIA: creciente, estable, decreciente}

---

## 7. Auditoría de Calidad de Datos

| Métrica | Valor |
|---------|-------|
| Eventos totales sin filtrar | {X} |
| Eventos de bots estimados | {X} ({X}%) |
| Eventos reales | {X} |
| Tracking Health | {X}% |
| Confiabilidad del análisis | {ALTA / MEDIA / BAJA} |

---

## 8. Recomendaciones

1. {RECOMENDACION_1}
2. {RECOMENDACION_2}
3. {RECOMENDACION_3}

---

*Generado con PIE-Insights — {FECHA}*
