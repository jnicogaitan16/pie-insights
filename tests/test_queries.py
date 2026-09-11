"""
Tests para src/queries/events.py y src/queries/segmentation.py.

Usa mocks de API responses.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.client import MixpanelClient
from src.queries.events import (
    count_events,
    count_unique_users,
    count_unique_schools,
    full_event_summary,
    BOT_CITIES,
)
from src.queries.segmentation import segment_by_property, segment_users_by_property


# --- Fixtures ---

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in (
        "MIXPANEL_PROJECT_ID",
        "MIXPANEL_API_SECRET",
        "MIXPANEL_SERVICE_ACCOUNT_USERNAME",
        "MIXPANEL_SERVICE_ACCOUNT_PASSWORD",
    ):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def client():
    return MixpanelClient(
        project_id="test-123",
        api_secret="fake-secret",
    )


# --- Mock data ---

SAMPLE_EXPORT_EVENTS = [
    {
        "event": "FUR Speech Import Completed",
        "properties": {
            "distinct_id": "user-1",
            "rbd": "12345",
            "$city": "Santiago",
            "time": 1725235200,  # 2024-09-02
        },
    },
    {
        "event": "FUR Speech Import Completed",
        "properties": {
            "distinct_id": "user-2",
            "rbd": "12345",
            "$city": "Bogota",
            "time": 1725235200,
        },
    },
    {
        "event": "FUR Speech Import Completed",
        "properties": {
            "distinct_id": "user-3",
            "rbd": "67890",
            "$city": "Maipu",
            "time": 1725321600,  # 2024-09-03
        },
    },
    # Bot event — should be filtered
    {
        "event": "FUR Speech Import Completed",
        "properties": {
            "distinct_id": "bot-1",
            "rbd": "99999",
            "$city": "Dulles",
            "time": 1725235200,
        },
    },
    # Another bot
    {
        "event": "FUR Speech Import Completed",
        "properties": {
            "distinct_id": "bot-2",
            "$city": "Boydton",
            "time": 1725235200,
        },
    },
]


# --- Tests count_events ---

class TestCountEvents:
    @patch("src.client.requests.Session.request")
    def test_count_events_basic(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "values": {
                    "FUR Speech Import Completed": {
                        "2026-09-01": 5,
                        "2026-09-02": 3,
                        "2026-09-03": 8,
                    }
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        result = count_events(
            client, "FUR Speech Import Completed", "2026-09-01", "2026-09-03"
        )

        assert result["event"] == "FUR Speech Import Completed"
        assert result["total"] == 16
        assert len(result["by_date"]) == 3

    @patch("src.client.requests.Session.request")
    def test_count_events_no_data(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"values": {}}}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        result = count_events(client, "Nonexistent Event", "2026-09-01", "2026-09-03")
        assert result["total"] == 0


# --- Tests count_unique_users ---

class TestCountUniqueUsers:
    @patch("src.client.requests.Session.get")
    def test_unique_users_filters_bots(self, mock_get, client):
        jsonl = "\n".join(json.dumps(e) for e in SAMPLE_EXPORT_EVENTS)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = jsonl
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = count_unique_users(
            client, "FUR Speech Import Completed", "2026-09-01", "2026-09-03"
        )

        assert result["unique_users"] == 3  # user-1, user-2, user-3 (no bots)
        assert result["bot_events_filtered"] == 2
        assert result["total_events"] == 3
        assert "bot-1" not in result["user_ids"]

    @patch("src.client.requests.Session.get")
    def test_unique_users_empty(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = count_unique_users(
            client, "FUR Speech Import Completed", "2026-09-01", "2026-09-03"
        )
        assert result["unique_users"] == 0


# --- Tests count_unique_schools ---

class TestCountUniqueSchools:
    @patch("src.client.requests.Session.get")
    def test_unique_schools(self, mock_get, client):
        jsonl = "\n".join(json.dumps(e) for e in SAMPLE_EXPORT_EVENTS)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = jsonl
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = count_unique_schools(
            client, "FUR Speech Import Completed", "2026-09-01", "2026-09-03"
        )

        assert result["unique_schools"] == 2  # 12345, 67890 (not 99999 from bot)
        assert "12345" in result["rbds"]
        assert "67890" in result["rbds"]
        assert "99999" not in result["rbds"]


# --- Tests full_event_summary ---

class TestFullEventSummary:
    @patch("src.client.requests.Session.get")
    def test_summary_combines_all_metrics(self, mock_get, client):
        jsonl = "\n".join(json.dumps(e) for e in SAMPLE_EXPORT_EVENTS)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = jsonl
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = full_event_summary(
            client, "FUR Speech Import Completed", "2026-09-01", "2026-09-03"
        )

        assert result["total_events"] == 3
        assert result["unique_users"] == 3
        assert result["unique_schools"] == 2
        assert result["bot_events_filtered"] == 2
        assert len(result["by_date"]) > 0


# --- Tests segment_by_property ---

class TestSegmentByProperty:
    @patch("src.client.requests.Session.request")
    def test_segment_basic(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "values": {
                    "FUR Speech": {"2026-09-01": 10, "2026-09-02": 5},
                    "FUR Psychoped": {"2026-09-01": 3, "2026-09-02": 2},
                    "Empty Segment": {"2026-09-01": 0, "2026-09-02": 0},
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        result = segment_by_property(
            client, "Page View", "2026-09-01", "2026-09-02", on="form-name"
        )

        assert result["unique_segments"] == 2  # Empty excluded
        assert result["segments"]["FUR Speech"] == 15
        assert result["segments"]["FUR Psychoped"] == 5
        assert result["total"] == 20

    @patch("src.client.requests.Session.request")
    def test_segment_sends_correct_on_param(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"values": {}}}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        segment_by_property(
            client, "Page View", "2026-09-01", "2026-09-02", on="rbd"
        )

        call_kwargs = mock_request.call_args
        assert call_kwargs[1]["params"]["on"] == 'properties["rbd"]'


# --- Tests segment_users_by_property ---

class TestSegmentUsersByProperty:
    @patch("src.client.requests.Session.get")
    def test_segment_users_by_rbd(self, mock_get, client):
        jsonl = "\n".join(json.dumps(e) for e in SAMPLE_EXPORT_EVENTS)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = jsonl
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = segment_users_by_property(
            client, "FUR Speech Import Completed", "2026-09-01", "2026-09-03", on="rbd"
        )

        assert result["unique_segments"] == 2
        assert result["segments"]["12345"]["events"] == 2
        assert result["segments"]["12345"]["users"] == 2
        assert result["segments"]["67890"]["events"] == 1
        assert result["segments"]["67890"]["users"] == 1
        # Bot RBD 99999 should not appear
        assert "99999" not in result["segments"]


# --- Tests bot filtering ---

class TestBotFiltering:
    def test_bot_cities_defined(self):
        assert "Dulles" in BOT_CITIES
        assert "Boydton" in BOT_CITIES
        assert "Santiago" not in BOT_CITIES
        assert "Bogota" not in BOT_CITIES
