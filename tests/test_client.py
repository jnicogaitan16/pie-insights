"""
Tests para src/client.py — MixpanelClient.

Usa mocks de requests para no depender de credenciales reales.
Para test de conexion real, usar: python -m src.healthcheck
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.client import MixpanelClient


# --- Fixtures ---

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Limpia env vars de Mixpanel para que no interfieran con tests."""
    for var in (
        "MIXPANEL_PROJECT_ID",
        "MIXPANEL_API_SECRET",
        "MIXPANEL_SERVICE_ACCOUNT_USERNAME",
        "MIXPANEL_SERVICE_ACCOUNT_PASSWORD",
    ):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def client():
    """Cliente con credenciales de test (API Secret)."""
    return MixpanelClient(
        project_id="test-project-123",
        api_secret="fake-secret-for-testing",
    )


@pytest.fixture
def client_sa():
    """Cliente con credenciales de Service Account."""
    return MixpanelClient(
        project_id="test-project-123",
        service_account_user="sa-user",
        service_account_pass="sa-pass",
    )


# --- Tests de inicializacion ---

class TestInit:
    def test_init_with_api_secret(self, client):
        assert client.project_id == "test-project-123"
        assert client._auth_method == "api_secret"

    def test_init_with_service_account(self, client_sa):
        assert client_sa._auth_method == "service_account"

    def test_init_without_project_id_raises(self):
        with pytest.raises(ValueError, match="MIXPANEL_PROJECT_ID"):
            MixpanelClient(api_secret="secret")

    def test_init_without_credentials_raises(self):
        with pytest.raises(ValueError, match="Se requiere"):
            MixpanelClient(project_id="test")

    def test_auth_header_api_secret(self, client):
        headers = client._build_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_auth_header_service_account(self, client_sa):
        headers = client_sa._build_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")


# --- Tests de segmentation ---

class TestSegmentation:
    @patch("src.client.requests.Session.request")
    def test_segmentation_basic(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"values": {"Page View": {"2026-09-01": 42}}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        result = client.segmentation(
            event="Page View",
            from_date="2026-09-01",
            to_date="2026-09-07",
        )

        assert "data" in result
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args
        assert call_kwargs[1]["params"]["event"] == "Page View"
        assert call_kwargs[1]["params"]["project_id"] == "test-project-123"

    @patch("src.client.requests.Session.request")
    def test_segmentation_with_filter(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"values": {}}}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        client.segmentation(
            event="Page View",
            from_date="2026-09-01",
            to_date="2026-09-07",
            where='properties["form-name"] == "FUR Speech"',
            on='properties["form-name"]',
        )

        call_kwargs = mock_request.call_args
        assert "where" in call_kwargs[1]["params"]
        assert "on" in call_kwargs[1]["params"]


# --- Tests de export ---

class TestExport:
    @patch("src.client.requests.Session.get")
    def test_export_parses_jsonl(self, mock_get, client):
        events_jsonl = "\n".join([
            json.dumps({"event": "Page View", "properties": {"distinct_id": "u1"}}),
            json.dumps({"event": "Page View", "properties": {"distinct_id": "u2"}}),
        ])
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = events_jsonl
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.export(
            from_date="2026-09-01",
            to_date="2026-09-07",
            event="Page View",
        )

        assert len(result) == 2
        assert result[0]["event"] == "Page View"

    @patch("src.client.requests.Session.get")
    def test_export_empty_response(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.export(
            from_date="2026-09-01",
            to_date="2026-09-07",
        )
        assert result == []


# --- Tests de retry ---

class TestRetry:
    @patch("src.client.time.sleep")
    @patch("src.client.requests.Session.request")
    def test_retry_on_429(self, mock_request, mock_sleep, client):
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "1"}

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = {"data": {}}
        success.raise_for_status = MagicMock()

        mock_request.side_effect = [rate_limited, success]

        result = client.segmentation(
            event="test", from_date="2026-09-01", to_date="2026-09-07"
        )

        assert result == {"data": {}}
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch("src.client.time.sleep")
    @patch("src.client.requests.Session.request")
    def test_retry_on_connection_error(self, mock_request, mock_sleep, client):
        import requests as req

        mock_request.side_effect = [
            req.exceptions.ConnectionError("timeout"),
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={"ok": True}),
                raise_for_status=MagicMock(),
            ),
        ]

        result = client._request("GET", "https://example.com")
        assert result == {"ok": True}
        assert mock_request.call_count == 2


# --- Tests de ping ---

class TestPing:
    @patch("src.client.requests.Session.request")
    def test_ping_success(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        assert client.ping() is True

    @patch("src.client.requests.Session.request")
    def test_ping_auth_error_returns_false(self, mock_request, client):
        import requests as req

        mock_response = MagicMock()
        mock_response.status_code = 401
        error = req.exceptions.HTTPError(response=mock_response)
        mock_request.side_effect = error

        assert client.ping() is False

    @patch("src.client.requests.Session.request")
    def test_ping_400_means_auth_ok(self, mock_request, client):
        """Un 400 significa que la auth funciono pero el evento no existe — OK."""
        import requests as req

        mock_response = MagicMock()
        mock_response.status_code = 400
        error = req.exceptions.HTTPError(response=mock_response)
        mock_request.side_effect = error

        assert client.ping() is True
