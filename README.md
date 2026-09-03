# PIE-Insights

Sistema automatizado de monitoreo de adopcion y metricas post-deploy para IntegratePIE, usando la API de Mixpanel.

## Que hace

- Consulta la API de Mixpanel para medir adopcion de features post-deploy
- Genera reportes automaticos (usuarios unicos, colegios activos, frecuencia)
- Alerta cuando una feature no alcanza los KPIs esperados
- Compara metricas contra baselines definidos

## Stack

- **Python 3.11+**
- **requests** — HTTP client para Mixpanel API
- **python-dotenv** — manejo de variables de entorno
- **pandas** — procesamiento de datos
- **Jinja2** — templates para reportes
- **pytest** — testing

## Setup rapido

```bash
# 1. Clonar y entrar al proyecto
cd pie-insights

# 2. Crear y activar entorno virtual
python3 -m venv env
source env/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Mixpanel

# 5. Verificar conexion
python -m src.healthcheck
```

## Estructura del proyecto

```
pie-insights/
├── src/
│   ├── __init__.py
│   ├── client.py          # Cliente Mixpanel API
│   ├── healthcheck.py     # Verificar conexion
│   ├── queries/
│   │   ├── __init__.py
│   │   ├── events.py      # Consultas de eventos
│   │   ├── funnels.py     # Consultas de funnels
│   │   └── segmentation.py # Segmentacion
│   ├── reports/
│   │   ├── __init__.py
│   │   └── adoption.py    # Reporte de adopcion post-deploy
│   └── alerts/
│       ├── __init__.py
│       └── slack.py        # Notificaciones Slack
├── config/
│   └── features.json      # Definicion de features a monitorear
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   └── test_queries.py
├── docs/
│   ├── auditoria_mixpanel.md
│   └── plan_de_trabajo.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Uso

```bash
# Reporte de adopcion de una feature
python -m src.reports.adoption --feature "Certificado de Egreso PIE" --days 7

# Consultar eventos de los ultimos 30 dias
python -m src.queries.events --event "Page View" --days 30

# Healthcheck de la API
python -m src.healthcheck
```

## Documentacion

- [Plan de trabajo por sprints](docs/plan_de_trabajo.md)
- [Auditoria de Mixpanel](docs/auditoria_mixpanel.md)
