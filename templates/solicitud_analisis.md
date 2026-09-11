# Solicitud de Analisis — PIE-Insights

<!-- Copiar, llenar los campos entre [ ] y pegar en Claude Code -->
<!-- Borrar las secciones que no apliquen -->

## Que quiero saber
[Pregunta concreta. Ej: "Como va la adopcion del Certificado de Egreso?" / "Hay colegios en riesgo de churn?" / "Comparar uso de FUR Speech vs Kine TO"]

## Informe(s) a analizar
[Nombre exacto. Ej: Certificado de Egreso PIE / FUR Speech / FUDEI / todos]

## Periodo
- Desde: [fecha o "ultimos 30 dias"]
- Hasta: [fecha o "hoy"]
- Comparar con periodo anterior: [si/no]

## Metricas que necesito
<!-- Marcar con x las que apliquen -->
- [ ] Registros MySQL (verdad de BD)
- [ ] Page View (quien abre)
- [ ] Form Saved (quien guarda)
- [ ] Form Download (quien descarga)
- [ ] Funnel completo (abrir → guardar → descargar)
- [ ] Desglose por colegio
- [ ] Desglose por usuario
- [ ] Tendencia semanal
- [ ] Completitud de campos
- [ ] Churn / colegios inactivos
- [ ] Tracking Health (cruce MySQL vs Mixpanel)
- [ ] Otra: [especificar]

## Nivel de profundidad
<!-- Elegir uno -->
- [ ] Rapido — solo KPIs principales y veredicto (5 min)
- [ ] Estandar — KPIs + desglose + tendencia (15 min)
- [ ] Profundo — todo lo anterior + cruce usuario por usuario + anomalias (30 min)

## Formato de salida
<!-- Elegir uno o mas -->
- [ ] Tabla resumen en chat
- [ ] Reporte markdown (docs/reportes/)
- [ ] Dashboard HTML con graficos
- [ ] Datos crudos (para usar en otro lado)

## Contexto adicional
[Algo que deba saber. Ej: "Hubo deploy ayer" / "Quiero presentar esto al equipo" / "Solo me interesa el colegio X"]

---

### Ejemplo llenado:

```
## Que quiero saber
Como va la adopcion de los certificados despues del rollout 100%

## Informe(s) a analizar
Certificado de Pertenencia + Certificado de Egreso

## Periodo
- Desde: ultimos 14 dias
- Hasta: hoy
- Comparar con periodo anterior: si

## Metricas que necesito
- [x] Registros MySQL
- [x] Form Saved
- [x] Form Download
- [x] Funnel completo
- [x] Desglose por colegio
- [ ] Desglose por usuario
- [x] Tendencia semanal
- [x] Completitud de campos

## Nivel de profundidad
- [x] Estandar

## Formato de salida
- [x] Dashboard HTML con graficos

## Contexto adicional
Se hizo rollout 100% el lunes. Quiero ver si hay colegios nuevos usandolo.
```
