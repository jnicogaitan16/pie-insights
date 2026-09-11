"""
Cliente para la API de Mixpanel.

Endpoints principales:
- GET /api/query/insights — Insights query (eventos agregados)
- GET /api/2.0/segmentation — Segmentation (desglose por propiedad)
- GET /api/2.0/export — Raw event export
- GET /api/2.0/funnels — Funnels

Autenticacion: Basic Auth con Service Account
Doc: https://developer.mixpanel.com/reference/authentication
"""

import os
import time
import logging
from base64 import b64encode

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Mixpanel API base URLs por data residency
API_BASE = {
    "US": "https://mixpanel.com",
    "EU": "https://eu.mixpanel.com",
}

DATA_API_BASE = {
    "US": "https://data.mixpanel.com",
    "EU": "https://data-eu.mixpanel.com",
}


class MixpanelClient:
    """Cliente para interactuar con la API de Mixpanel via Service Account."""

    def __init__(
        self,
        project_id: str | None = None,
        api_secret: str | None = None,
        service_account_user: str | None = None,
        service_account_pass: str | None = None,
        data_residency: str = "US",
        max_retries: int = 3,
    ):
        self.project_id = project_id or os.getenv("MIXPANEL_PROJECT_ID")
        self.api_secret = api_secret or os.getenv("MIXPANEL_API_SECRET")
        self.sa_user = service_account_user or os.getenv("MIXPANEL_SERVICE_ACCOUNT_USERNAME")
        self.sa_pass = service_account_pass or os.getenv("MIXPANEL_SERVICE_ACCOUNT_PASSWORD")
        self.data_residency = data_residency.upper()
        self.max_retries = max_retries

        if not self.project_id:
            raise ValueError("MIXPANEL_PROJECT_ID es requerido (env var o parametro)")

        # Determinar metodo de autenticacion
        if self.sa_user and self.sa_pass:
            self._auth_method = "service_account"
        elif self.api_secret:
            self._auth_method = "api_secret"
        else:
            raise ValueError(
                "Se requiere MIXPANEL_API_SECRET o "
                "MIXPANEL_SERVICE_ACCOUNT_USERNAME + MIXPANEL_SERVICE_ACCOUNT_PASSWORD"
            )

        self._base_url = API_BASE[self.data_residency]
        self._data_url = DATA_API_BASE[self.data_residency]
        self._session = requests.Session()
        self._session.headers.update(self._build_auth_headers())

    def _build_auth_headers(self) -> dict:
        """Construye headers de autenticacion segun el metodo disponible."""
        if self._auth_method == "service_account":
            credentials = b64encode(
                f"{self.sa_user}:{self.sa_pass}".encode()
            ).decode()
            return {"Authorization": f"Basic {credentials}"}
        else:
            credentials = b64encode(f"{self.api_secret}:".encode()).decode()
            return {"Authorization": f"Basic {credentials}"}

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Ejecuta request con retry y backoff exponencial."""
        for attempt in range(self.max_retries):
            try:
                resp = self._session.request(method, url, timeout=30, **kwargs)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                    logger.warning("Rate limited. Reintentando en %ds...", retry_after)
                    time.sleep(retry_after)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("Error de conexion. Reintentando en %ds... (%s)", wait, e)
                    time.sleep(wait)
                else:
                    raise

        raise requests.exceptions.RetryError(
            f"Max reintentos ({self.max_retries}) alcanzado para {url}"
        )

    # --- API Endpoints ---

    def insights(self, params: dict) -> dict:
        """
        Consulta Insights API (eventos agregados, conteo, unicos).
        Doc: https://developer.mixpanel.com/reference/insights-query

        params debe incluir al menos:
        - project_id (se agrega automaticamente)
        - bookmark_id o parameters del query
        """
        params = {"project_id": self.project_id, **params}
        url = f"{self._base_url}/api/2.0/insights"
        return self._request("GET", url, params=params)

    def segmentation(
        self,
        event: str,
        from_date: str,
        to_date: str,
        on: str | None = None,
        where: str | None = None,
        unit: str = "day",
    ) -> dict:
        """
        Consulta Segmentation API (desglose por propiedad).
        Doc: https://developer.mixpanel.com/reference/segmentation

        Args:
            event: Nombre del evento
            from_date: Fecha inicio (YYYY-MM-DD)
            to_date: Fecha fin (YYYY-MM-DD)
            on: Propiedad para segmentar (e.g. 'properties["form-name"]')
            where: Filtro de propiedad (e.g. 'properties["form-name"] == "FUR Speech"')
            unit: Unidad de tiempo (minute, hour, day, week, month)
        """
        params = {
            "project_id": self.project_id,
            "event": event,
            "from_date": from_date,
            "to_date": to_date,
            "unit": unit,
        }
        if on:
            params["on"] = on
        if where:
            params["where"] = where

        url = f"{self._base_url}/api/2.0/segmentation"
        return self._request("GET", url, params=params)

    def export(
        self,
        from_date: str,
        to_date: str,
        event: str | None = None,
        where: str | None = None,
    ) -> list[dict]:
        """
        Exporta eventos crudos.
        Doc: https://developer.mixpanel.com/reference/raw-event-export

        Nota: retorna JSONL (un JSON por linea), no JSON estandar.
        """
        params = {
            "project_id": self.project_id,
            "from_date": from_date,
            "to_date": to_date,
        }
        if event:
            params["event"] = f'["{event}"]'
        if where:
            params["where"] = where

        url = f"{self._data_url}/api/2.0/export"

        for attempt in range(self.max_retries):
            try:
                resp = self._session.get(url, params=params, timeout=60)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                    logger.warning("Rate limited (export). Reintentando en %ds...", retry_after)
                    time.sleep(retry_after)
                    continue

                resp.raise_for_status()

                # JSONL: cada linea es un JSON
                import json
                events = []
                for line in resp.text.strip().split("\n"):
                    if line:
                        events.append(json.loads(line))
                return events

            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("Error de conexion (export). Reintentando en %ds...", wait, e)
                    time.sleep(wait)
                else:
                    raise

        raise requests.exceptions.RetryError(
            f"Max reintentos ({self.max_retries}) alcanzado para export"
        )

    def funnels(self, funnel_id: int, from_date: str, to_date: str, unit: str = "day") -> dict:
        """
        Consulta Funnels API.
        Doc: https://developer.mixpanel.com/reference/funnels
        """
        params = {
            "project_id": self.project_id,
            "funnel_id": funnel_id,
            "from_date": from_date,
            "to_date": to_date,
            "unit": unit,
        }
        url = f"{self._base_url}/api/2.0/funnels"
        return self._request("GET", url, params=params)

    # --- Utilidades ---

    def ping(self) -> bool:
        """
        Verifica la conexion a Mixpanel haciendo un query minimo.
        Retorna True si la conexion es exitosa, False si falla.
        """
        try:
            from datetime import date, timedelta
            today = date.today()
            yesterday = today - timedelta(days=1)
            self.segmentation(
                event="$ignore",
                from_date=yesterday.isoformat(),
                to_date=today.isoformat(),
            )
            return True
        except requests.exceptions.HTTPError as e:
            # 400 es esperado si el evento no existe, pero la auth fue exitosa
            if e.response is not None and e.response.status_code == 400:
                return True
            # 401/403 significa credenciales invalidas
            logger.error("Error de autenticacion: %s", e)
            return False
        except Exception as e:
            logger.error("Error de conexion: %s", e)
            return False
