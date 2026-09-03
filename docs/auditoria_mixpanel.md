# Auditoría de Integración Mixpanel — IntegratePIE

**Fecha:** 2026-09-03
**Autor:** Auditoría automatizada con Claude Code
**Objetivo:** Entender el sistema actual de tracking, evaluar su estado, y definir la estrategia para un sistema de métricas post-deploy automatizado.

---

## Tabla de Contenidos

1. [Arquitectura Actual](#1-arquitectura-actual)
2. [Componentes del Sistema](#2-componentes-del-sistema)
3. [Eventos Instrumentados](#3-eventos-instrumentados)
4. [Cobertura de Tracking](#4-cobertura-de-tracking)
5. [Fortalezas del Sistema Actual](#5-fortalezas-del-sistema-actual)
6. [Debilidades y Gaps](#6-debilidades-y-gaps)
7. [Propuesta: Sistema de Métricas Post-Deploy](#7-propuesta-sistema-de-metricas-post-deploy)
8. [Decisión Arquitectónica: IntegratePIE vs Proyecto Aparte](#8-decision-arquitectonica-integratepie-vs-proyecto-aparte)
9. [Stack Tecnológico Recomendado](#9-stack-tecnologico-recomendado)
10. [Roadmap de Implementación](#10-roadmap-de-implementacion)

---

## 1. Arquitectura Actual

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                       │
│                                                                 │
│  event-tracker.js         event-tracker-constants.js            │
│  ┌──────────────┐         ┌──────────────────────┐              │
│  │ EventTracker │         │ PAGE_NAMES (70+)     │              │
│  │ class        │◄────────│ INFORMES_WHITELIST   │              │
│  └──────┬───────┘         └──────────────────────┘              │
│         │                                                       │
│  event-tracker.blade.php                                        │
│  ┌──────────────────────────────────────┐                       │
│  │ window.tracker = {                   │                       │
│  │   trackEvent()                       │                       │
│  │   trackEventPageView()              │                       │
│  │   trackEventSelectSchool()          │                       │
│  │   trackEventFormDownload()          │                       │
│  │   trackEventLogout()                │                       │
│  │   setUser()                         │                       │
│  │ }                                    │                       │
│  └──────────────┬───────────────────────┘                       │
│                 │ mixpanel.track() directo                      │
│                 ▼                                                │
│         ┌──────────────┐                                        │
│         │  Mixpanel CDN │──────────────────► Mixpanel Cloud     │
│         │  (JS SDK)     │                                       │
│         └───────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (Laravel)                        │
│                                                                 │
│  Controllers / Services                                         │
│  ┌────────────────────┐                                         │
│  │ EventTracker::     │       Facade                            │
│  │   track(event,     │──────► App\Facades\EventTracker         │
│  │         props)     │              │                           │
│  └────────────────────┘              ▼                           │
│                              App\Services\EventTracker          │
│                              ┌────────────────────────┐         │
│                              │ Artisan::call(          │         │
│                              │   'event:track', ...)   │         │
│                              └──────────┬─────────────┘         │
│                                         ▼                       │
│                              EventTrackerCommand                │
│                              ┌────────────────────────┐         │
│                              │ Mixpanel::getInstance() │         │
│                              │ $mp->identify(user)     │         │
│                              │ $mp->track(event,props) │         │
│                              └──────────┬─────────────┘         │
│                                         │                       │
│                                         ▼                       │
│                                  Mixpanel PHP SDK               │
│                                  (mixpanel/mixpanel-php)        │
│                                         │                       │
│                                         ▼                       │
│                                  Mixpanel Cloud (API)           │
│                                                                 │
│  FurTrackingService (especializado)                             │
│  ┌────────────────────────────────┐                             │
│  │ Niveles de tracking            │                             │
│  │ Kill switch                    │                             │
│  │ Guard FUR 2026 (anio/rbd)     │                             │
│  │ Eventos declarados en config   │──► EventTracker::track()    │
│  └────────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de datos

1. **Frontend:** `window.tracker.trackEventPageView('Nombre')` → Mixpanel JS SDK → Mixpanel Cloud
2. **Backend:** `EventTracker::track('Form Saved', [...])` → Artisan command → Mixpanel PHP SDK → Mixpanel Cloud
3. **FUR (especializado):** `FurTrackingService::track('clave', [...])` → niveles + guard → EventTracker → Mixpanel

---

## 2. Componentes del Sistema

### 2.1 Frontend

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `public/js/event-tracker.js` | Clase EventTracker: init Mixpanel JS SDK, track, setUser, logout | 57 |
| `public/js/event-tracker-constants.js` | Constantes PAGE_NAMES (70+ páginas) e INFORMES_NAMES_WHITELIST | ~80 |
| `resources/views/partials/event-tracker.blade.php` | Inicialización global de `window.tracker` con 6 métodos | 57 |

**Métodos disponibles en `window.tracker`:**
- `trackEvent(event, properties)` — Evento genérico (no recomendado)
- `trackEventPageView(page, properties)` — Vista de página (recomendado)
- `trackEventSelectSchool(properties)` — Selección de colegio
- `trackEventFormDownload(config, properties)` — Descarga de formulario
- `trackEventLogout(properties)` — Cierre de sesión
- `setUser(userId, userProperties)` — Identificar usuario

### 2.2 Backend

| Archivo | Propósito |
|---------|-----------|
| `app/Services/EventTracker.php` | Servicio que delega al comando Artisan |
| `app/Facades/EventTracker.php` | Facade para `EventTracker::track()` |
| `app/Console/Commands/EventTrackerCommand.php` | Comando que ejecuta Mixpanel PHP SDK |
| `config/event_tracker.php` | Config: platform (mixpanel), token |
| `app/Http/Helpers/UtilsHelper.php` | `getTrackerProperties()` y `getRequestProperties()` |
| `app/Services/Fur/FurTrackingService.php` | Sistema de tracking especializado para FUR con niveles |

### 2.3 Configuración

```php
// config/event_tracker.php
return [
    'platform' => env('ANALYTICS_PLATFORM', 'mixpanel'),
    'token'    => env('ANALYTICS_PLATFORM_TOKEN'),
];
```

**Variables de entorno requeridas:**
- `ANALYTICS_PLATFORM` = `mixpanel`
- `ANALYTICS_PLATFORM_TOKEN` = token del proyecto Mixpanel

### 2.4 Dependencias

| Paquete | Versión | Ubicación |
|---------|---------|-----------|
| `mixpanel/mixpanel-php` | ^2.11 | composer.json (backend) |
| `mixpanel-browser` | ^2.55.1 | package.json (frontend, pero usa CDN) |
| Mixpanel CDN JS | latest | Cargado dinámicamente en event-tracker.js |

### 2.5 FurTrackingService (patrón avanzado)

El módulo FUR tiene un sistema de tracking más sofisticado:

- **Niveles de tracking:** Eventos declarados en `config/fur.php` con nivel (1, 2, 3...)
- **Kill switch:** `fur.tracking.nivel_activo = 0` apaga todo
- **Guard FUR 2026:** Solo emite para años/colegios piloto (`furHdusHabilitadas`)
- **Eventos forzados:** Lista de eventos que ignoran el nivel
- **Nunca rompe el flujo funcional:** try/catch silencioso
- **Método `emitiria()`:** Consulta si un evento se emitiría sin emitirlo (para flags one-shot)

---

## 3. Eventos Instrumentados

### 3.1 Tipos de eventos

| Tipo de Evento | Origen | Cantidad |
|---------------|--------|----------|
| `Page View` | Frontend (45 vistas Blade) | 89 llamadas |
| `Form Saved` | Backend (38 controllers) | 38 llamadas |
| `Form Download` | Frontend (botonera) | Centralizado |
| `User Logged In` | Backend (LoginController) | 1 |
| `User Logout` | Frontend | 1 |
| `Select School` | Frontend | 1 |
| `FUR *` (varios) | Backend (FurTrackingService) | Declarados en config |
| `Generated Report` | Backend (PieController) | 1 |

### 3.2 Eventos backend (`EventTracker::track`)

| Evento | Controller | Formulario |
|--------|-----------|------------|
| `Form Saved` | InformeFichaSaludController | Valoración de Salud |
| `Form Saved` | AnamnesisController | Anamnesis |
| `Form Saved` | WiscVController | WISC V |
| `Form Saved` | WiscIIIController | WISC III |
| `Form Saved` | TestWaisIVController | WAIS IV |
| `Form Saved` | InformePsicologicoController | Informe Psicológico |
| `Form Saved` | InformeFonoaudiologicoController | Informe Fonoaudiológico |
| `Form Saved` | InformeFonoaudiologicoIdtelController | Informe Fono IDTEL |
| `Form Saved` | IdtelController | Protocolo IDTEL |
| `Form Saved` | InformeTadiController | Informe TADI |
| `Form Saved` | InformeICAPController | ICAP |
| `Form Saved` | InformePedagogicoController | Informe Pedagógico |
| `Form Saved` | InformePefeController | PEFE |
| `Form Saved` | InformePsicoeducativoController | Psicoeducativo |
| `Form Saved` | InformeEvaluaController | Evalúa |
| `Form Saved` | PsicopedagogicoLecMatController | Psicopedagógico Lec/Mat |
| `Form Saved` | PsicopedagogicoPrecalculoController | Psicopedagógico Pre |
| `Form Saved` | PsicopedagogicoFuncionesBasicasController | Psicopedagógico FB |
| `Form Saved` | EvaluacionPedagogicaController | Evaluación Pedagógica |
| `Form Saved` | PautaObservacionDirectaController | Pauta Observación |
| `Form Saved` | ConnersController (×3) | Test Conners |
| `Form Saved` | InformeFamiliaController | Informe Familia |
| `Form Saved` | InformeIdeaController | IDEA |
| `Form Saved` | InformeTerapiaOcupacionalController | Terapia Ocupacional |
| `Form Saved` | InformePoderSimpleController | Poder Simple |
| `Form Saved` | InformeCertificadoPertenenciaController | Certificado Pertenencia |
| `Form Saved` | InformeCertificadoEgresoController | Certificado Egreso |
| `Form Saved` | InformeFichaAutorizaMineducController | Ficha Autorización |
| `Form Saved` | PaiController | PAI |
| `Form Saved` | InformeAvanzadoController (×2) | Avanzados |
| `Form Saved` | PieController | PIE |
| `User Logged In` | LoginController | — |
| `Generated Report` | PieController | Generación Word/PDF |

### 3.3 Propiedades enviadas por evento

**Page View (frontend):**
```javascript
{
  'form-name': 'Nombre de la Página',
  'form-properties': { /* datos del form */ },
  // + session properties (user, colegio, env)
}
```

**Form Saved (backend):**
```php
[
  'alumno' => ['pie_id' => ..., 'pie_nee_id' => ...],
  'form-name' => 'Nombre del Formulario',
  'form-properties' => [
    'form_id' => ...,
    'form_tipo' => 'ingreso|reevaluacion|anual',
    'form_estado' => ...,
    'form_anio' => ...,
  ],
  // + session/request properties (user, colegio, browser, IP)
]
```

### 3.4 Propiedades de sesión/request

Enviadas automáticamente en cada evento:

| Propiedad | Origen | Descripción |
|-----------|--------|-------------|
| `username` | Sesión | RUT con guion |
| `rut` | Sesión | RUT sin formato |
| `user_id` | Sesión | ID del usuario |
| `email` | Sesión | Email |
| `name` | Sesión | Nombre completo |
| `colegio_name` | Sesión | Nombre del colegio |
| `colegio_rbd` | Sesión | RBD del colegio |
| `$browser` | Request | Navegador (UA-Parser) |
| `$device` | Request | Dispositivo |
| `$os` | Request | Sistema operativo |
| `ip` | Request | IP del usuario |
| `env` | Config | Ambiente (prod, qa, local) |

---

## 4. Cobertura de Tracking

### 4.1 Módulos CON tracking

| Módulo | Page View | Form Saved | Form Download | Cobertura |
|--------|-----------|------------|---------------|-----------|
| Login | — | ✅ | — | Parcial |
| Select Colegio | ✅ | — | — | ✅ |
| Panorama Curso | ✅ | — | — | ✅ |
| Equipo PIE | ✅ | — | — | ✅ |
| PAI (todos) | ✅ | ✅ | — | ✅ |
| Libro de Registro | ✅ | — | ✅ | Parcial |
| FUR | ✅ | — | ✅ | ✅ (FurTrackingService) |
| FUDEI | ✅ | — | — | Parcial |
| Informes (30+) | ✅ | ✅ | ✅ | ✅ |
| PACI 2.0 | ✅ | — | — | Parcial |
| Certificados | ✅ | ✅ | — | ✅ |

### 4.2 Módulos SIN tracking

| Módulo | Criticidad | Observación |
|--------|-----------|-------------|
| Coordinación | Alta | Sin eventos |
| Administración/Config | Media | Sin eventos |
| Permisos/Roles | Alta | Sin eventos |
| Proyección Subvenciones | Alta | Sin eventos |
| Capacitaciones | Baja | Sin eventos |
| Nómina PIE/Egresados | Media | Sin eventos de navegación propios |

### 4.3 Lo que falta para métricas post-deploy

| Métrica necesaria | Estado actual | Gap |
|-------------------|---------------|-----|
| Uso de un informe nuevo | Parcial (Page View + Form Saved) | No hay métrica de "primer uso" ni "adopción" |
| Qué colegio lo usa más | ✅ Tiene colegio_rbd en cada evento | Falta agregación automatizada |
| Cuántos usuarios registraron eventos | ✅ Tiene user_id/rut | Falta dashboard/alerta |
| Éxito de un deploy | ❌ No existe | No hay eventos de "feature activada" ni comparación pre/post |
| Tasa de adopción | ❌ No existe | No hay cohortes de "primera vez" vs "recurrente" |
| Errores post-deploy | Parcial (Sentry) | No correlacionado con Mixpanel |

---

## 5. Fortalezas del Sistema Actual

1. **Dual-track (frontend + backend):** Page Views en frontend, Form Saved en backend. Captura tanto la navegación como la persistencia.
2. **Identificación de usuario consistente:** `mixpanel.identify(rut)` en ambos canales. Permite unificar sesiones.
3. **Propiedades ricas:** Cada evento lleva usuario, colegio, formulario, tipo, estado. Permite segmentación profunda.
4. **FurTrackingService como patrón a seguir:** Sistema de niveles, kill switch, guard por año/rbd, declarativo en config. Es el modelo más maduro del proyecto.
5. **Documentación existente:** `docs/readme.tracker.md` documenta los 4 métodos principales con ejemplos.
6. **Whitelist de informes:** `INFORMES_NAMES_WHITELIST` controla qué informes emiten eventos de descarga.
7. **70+ páginas registradas:** `PAGE_NAMES` cubre prácticamente toda la aplicación.
8. **Abstracción de plataforma:** El config soporta cambiar de Mixpanel a Amplitude sin modificar instrumentación.

---

## 6. Debilidades y Gaps

### 6.1 Arquitectura

| # | Debilidad | Impacto | Detalle |
|---|-----------|---------|---------|
| 1 | **Backend trackea vía Artisan command** | Performance | Cada `EventTracker::track()` ejecuta `Artisan::call()` que instancia un nuevo proceso. En un controller con tráfico alto, esto agrega latencia. |
| 2 | **No hay cola (queue) para eventos** | Fiabilidad | Si Mixpanel no responde, el request del usuario se retrasa. Debería ser async/queued. |
| 3 | **Sin batching** | Eficiencia | Cada evento es una llamada HTTP individual a Mixpanel. El SDK PHP soporta flush por lotes. |
| 4 | **Sin retry en caso de fallo** | Pérdida de datos | Si la API de Mixpanel falla, el evento se pierde silenciosamente. |
| 5 | **`Form Saved` duplicado en 38 controllers** | Mantenibilidad | La misma estructura de tracking se copia en cada controller. Debería ser un trait o middleware. |

### 6.2 Métricas y Análisis

| # | Gap | Impacto |
|---|-----|---------|
| 6 | **No hay eventos de "feature flag"** | No se puede medir adopción de features nuevas post-deploy |
| 7 | **No hay evento "Feature First Use"** | No se sabe cuándo un usuario usa algo por primera vez |
| 8 | **No hay dashboard automatizado** | Las consultas a Mixpanel se hacen manualmente |
| 9 | **No hay alertas** | No se detecta si un informe nuevo tiene 0 uso después del deploy |
| 10 | **Sin correlación deploy ↔ métricas** | No se sabe qué commit/PR introdujo qué feature ni su impacto |

### 6.3 Datos

| # | Gap | Impacto |
|---|-----|---------|
| 11 | **Eventos `Form Saved` no distinguen "crear" de "editar"** | No se puede medir creación vs modificación |
| 12 | **No hay evento de "Form Viewed but Not Saved"** | No se mide abandono |
| 13 | **Sin super properties** | Propiedades como `env`, `app_version` deberían ser super properties (se envían en todos los eventos automáticamente) |

---

## 7. Propuesta: Sistema de Métricas Post-Deploy

### 7.1 Objetivo

Responder automáticamente después de cada deploy:
1. **¿Se usa la funcionalidad nueva?** → Tasa de adopción
2. **¿Qué colegio la usa más?** → Segmentación por colegio
3. **¿Cuántos usuarios interactuaron?** → Usuarios únicos
4. **¿Es exitoso el desarrollo?** → Métricas de éxito definidas pre-deploy

### 7.2 Componentes necesarios

```
┌─────────────────────────────────────────────────────────────────┐
│  1. INSTRUMENTACIÓN (IntegratePIE)                              │
│     - Eventos Mixpanel existentes (mejorados)                   │
│     - Nuevo: evento "Feature Activated" con deploy_version      │
│     - Nuevo: super property APP_VERSION en todos los eventos    │
│     └──────────────────────┬────────────────────────────────────│
│                            ▼                                    │
│  2. MIXPANEL CLOUD                                              │
│     - Almacena todos los eventos                                │
│     - API de consulta (JQL, Insights, Funnels)                  │
│     └──────────────────────┬────────────────────────────────────│
│                            ▼                                    │
│  3. SERVICIO DE MÉTRICAS (Proyecto aparte o cron job)           │
│     - Consulta Mixpanel API periódicamente                      │
│     - Genera reportes de adopción post-deploy                   │
│     - Envía alertas si una feature tiene 0 uso en X días        │
│     - Dashboard de métricas por deploy/feature                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Mejoras a la instrumentación existente

**a) Super property `app_version`:**
```javascript
// En event-tracker.blade.php
mixpanel.register({
    'app_version': '{{ config("app.version") }}',
    'env': '{{ config("sentry.environment") }}'
});
```

**b) Evento "Feature Deployed":**
```php
// En pipeline post-deploy o en un middleware de primer request
EventTracker::track('Feature Deployed', [
    'feature_name' => 'Certificado de Egreso PIE',
    'deploy_version' => config('app.version'),
    'deploy_date' => now()->toISOString(),
]);
```

**c) Centralizar `Form Saved` con trait:**
```php
trait TracksFormEvents {
    protected function trackFormSaved(Request $request, string $formName, array $extra = []) {
        EventTracker::track('Form Saved', array_merge([
            'form-name' => $formName,
            'form-properties' => [
                'form_id' => $request->input('form_id'),
                'form_tipo' => $request->input('tipo'),
                'form_estado' => $request->input('form_estado'),
                'form_anio' => $this->anio_activo,
            ],
        ], $extra));
    }
}
```

**d) Queue para eventos backend:**
```php
// En EventTracker::track(), usar dispatch en vez de Artisan::call
dispatch(function () use ($event, $properties) {
    Artisan::call('event:track', [
        'event' => $event,
        'properties' => json_encode($properties),
    ]);
})->afterResponse();
```

---

## 8. Decisión Arquitectónica: IntegratePIE vs Proyecto Aparte

### Opción A: Todo en IntegratePIE

| Pros | Contras |
|------|---------|
| Acceso directo a sesión/datos | Agrega complejidad al monolito |
| Sin latencia de red para instrumentar | El cron de consulta a Mixpanel API compite con requests |
| Deployment unificado | Difícil de reutilizar en otros proyectos |
| Ya tiene Mixpanel PHP SDK instalado | Acoplado al ciclo de release de IntegratePIE |

### Opción B: Proyecto aparte (microservicio de métricas)

| Pros | Contras |
|------|---------|
| Desacoplado de IntegratePIE | Requiere infra adicional |
| Reutilizable para otros proyectos Inteduc | Setup inicial más costoso |
| Puede tener su propio ciclo de deploy | Necesita API de IntegratePIE para datos de contexto |
| No afecta performance de la app principal | Latencia adicional si necesita datos en tiempo real |

### Opción C: Híbrida (recomendada)

| Componente | Ubicación | Justificación |
|-----------|-----------|---------------|
| **Instrumentación** (eventos Mixpanel) | IntegratePIE | Ya existe, solo mejorar |
| **Consulta a Mixpanel API** | Proyecto aparte (script/cron) | No mezclar lógica de análisis con la app |
| **Dashboard y alertas** | Proyecto aparte | Independiente del deploy de la app |
| **Definición de features y KPIs** | Config en IntegratePIE | Cada feature define sus métricas de éxito |

**Recomendación: Opción C (Híbrida)**

La instrumentación ya vive en IntegratePIE y debe seguir ahí (mejorada). Pero el sistema de consulta, dashboards y alertas debe ser un proyecto independiente que consuma la Mixpanel API para generar reportes.

---

## 9. Stack Tecnológico Recomendado

### Para la instrumentación (IntegratePIE):
- **Mixpanel PHP SDK** (ya instalado) — Mejorar con queue/batching
- **Mixpanel JS SDK** (ya instalado vía CDN) — Agregar super properties
- **Laravel Queue** (dispatchAfterResponse) — Async sin infraestructura nueva

### Para el servicio de métricas (proyecto aparte):

| Tecnología | Propósito | Justificación |
|-----------|-----------|---------------|
| **Python 3.x** | Script principal | Mixpanel tiene SDK oficial en Python, ideal para data analysis |
| **Mixpanel API** | Consulta de datos | JQL queries, Export API, Insights API |
| **Azure Functions** o **Cron job** | Ejecución periódica | Correr análisis post-deploy sin servidor dedicado |
| **Slack/Teams webhook** | Alertas | Notificar al equipo si una feature tiene bajo uso |
| **JSON/CSV** | Reportes | Archivos simples por deploy, versionables |

**Alternativa si se quiere algo más robusto:**
- **Mixpanel Boards** (nativo) — Dashboards sin código
- **Mixpanel Alerts** (nativo) — Alertas automáticas por umbrales
- **Mixpanel API + Jupyter Notebooks** — Análisis ad-hoc

### Mixpanel API endpoints relevantes:

| Endpoint | Uso |
|----------|-----|
| `GET /api/2.0/events` | Eventos por nombre y fecha |
| `GET /api/2.0/events/properties` | Propiedades de un evento |
| `GET /api/2.0/segmentation` | Segmentación por propiedad |
| `GET /api/2.0/retention` | Retención de usuarios |
| `POST /api/2.0/jql` | Queries JQL (JavaScript Query Language) |

---

## 10. Roadmap de Implementación

### Fase 1: Mejoras a instrumentación existente (en IntegratePIE)

| Tarea | Esfuerzo | Impacto |
|-------|----------|---------|
| Agregar super property `app_version` | 0.5 día | Correlacionar eventos con deploys |
| Mover `EventTracker::track` a `dispatchAfterResponse` | 1 día | Eliminar latencia en requests |
| Crear trait `TracksFormEvents` para centralizar `Form Saved` | 1 día | Reducir duplicación en 38 controllers |
| Agregar evento `Feature Deployed` en pipeline | 0.5 día | Marcar cuándo se activa cada feature |
| Registrar `app_version` como `APP_VERSION` env variable (ya existe en pipeline) | 0.2 día | Disponible para super property |

### Fase 2: Servicio de métricas post-deploy (proyecto aparte)

| Tarea | Esfuerzo | Impacto |
|-------|----------|---------|
| Crear script Python con Mixpanel API client | 1 día | Base del sistema |
| Definir KPIs por tipo de feature (informe, módulo, vista) | 0.5 día | Qué medir |
| Implementar consulta de adopción post-deploy | 1 día | Usuarios únicos, colegios, frecuencia |
| Implementar alertas por Slack/Teams | 0.5 día | Notificación de bajo uso |
| Configurar cron/Azure Function para ejecución periódica | 0.5 día | Automatización |
| Crear reporte semanal automatizado | 1 día | Visibilidad continua |

### Fase 3: Expansión

| Tarea | Esfuerzo |
|-------|----------|
| Agregar tracking a módulos sin cobertura (Coordinación, Admin, Permisos) | 2-3 días |
| Implementar evento "Feature First Use" | 1 día |
| Implementar funnels de conversión (View → Save → Download) | 1 día |
| Dashboard en Mixpanel Boards para stakeholders | 1 día |

---

## Anexo A: Ejemplo de consulta post-deploy

```python
# Ejemplo: ¿Cuántos usuarios usaron "Certificado de Egreso PIE" después del deploy?
import requests
from datetime import datetime, timedelta

MIXPANEL_TOKEN = 'your-project-secret'
DEPLOY_DATE = '2026-09-01'
FEATURE_NAME = 'Certificado de Egreso PIE'

response = requests.get(
    'https://mixpanel.com/api/2.0/segmentation',
    params={
        'event': 'Page View',
        'from_date': DEPLOY_DATE,
        'to_date': (datetime.now()).strftime('%Y-%m-%d'),
        'where': f'properties["form-name"] == "{FEATURE_NAME}"',
        'type': 'unique',
    },
    auth=(MIXPANEL_TOKEN, ''),
)
print(response.json())
```

## Anexo B: Inventario de archivos del sistema de tracking

```
CORE:
  app/Services/EventTracker.php              # Servicio principal
  app/Facades/EventTracker.php               # Facade
  app/Console/Commands/EventTrackerCommand.php # Comando Artisan
  config/event_tracker.php                   # Configuración

FRONTEND:
  public/js/event-tracker.js                 # Clase JS
  public/js/event-tracker-constants.js       # PAGE_NAMES, WHITELIST
  resources/views/partials/event-tracker.blade.php # Inicialización

ESPECIALIZADO (FUR):
  app/Services/Fur/FurTrackingService.php    # Tracking con niveles

HELPERS:
  app/Http/Helpers/UtilsHelper.php           # getTrackerProperties, getRequestProperties

INSTRUMENTACIÓN (38 controllers + 45 vistas):
  app/Http/Controllers/Informes/*.php        # Form Saved (backend)
  resources/views/templates/informe/*.blade.php # Page View (frontend)

DOCUMENTACIÓN:
  docs/readme.tracker.md                     # Guía de uso
```

---

*Auditoría generada el 2026-09-03 mediante análisis estático del código fuente de IntegratePIE.*
