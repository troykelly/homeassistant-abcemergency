"""Tests for ABC Emergency API client."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from aiohttp import ClientError, ClientResponseError

from custom_components.abcemergency.api import ABCEmergencyClient
from custom_components.abcemergency.const import API_BASE_URL, USER_AGENT
from custom_components.abcemergency.exceptions import (
    ABCEmergencyAPIError,
    ABCEmergencyConnectionError,
)

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp session."""
    return MagicMock(spec=aiohttp.ClientSession)


@pytest.fixture
def api_client(mock_session: MagicMock) -> ABCEmergencyClient:
    """Create an API client with a mock session."""
    return ABCEmergencyClient(mock_session)


@pytest.fixture
def sample_emergency_response() -> dict:
    """Provide a sample emergency search response."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-test123",
                "headline": "Test Bushfire",
                "to": "/emergency/warning/AUREMER-test123",
                "alertLevelInfoPrepared": {
                    "text": "Watch and Act",
                    "level": "severe",
                    "style": "severe",
                },
                "emergencyTimestampPrepared": {
                    "date": "2025-12-06T05:34:00+00:00",
                    "formattedTime": "4:34:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                },
                "eventLabelPrepared": {
                    "icon": "fire",
                    "labelText": "Bushfire",
                },
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "100 ha",
                    "status": "Being controlled",
                    "source": "NSW Rural Fire Service",
                },
                "geometry": {
                    "crs": {
                        "type": "name",
                        "properties": {"name": "EPSG:4326"},
                    },
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [150.0, -33.0]},
                    ],
                },
            }
        ],
        "features": [],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 1,
        "stateCount": 125,
    }


@pytest.fixture
def empty_response() -> dict:
    """Provide an empty emergency search response."""
    return {
        "emergencies": [],
        "features": [],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 0,
        "stateCount": 0,
    }


class TestABCEmergencyClientInit:
    """Test ABCEmergencyClient initialization."""

    def test_init_with_default_url(self, mock_session: MagicMock) -> None:
        """Test client initializes with default API URL."""
        client = ABCEmergencyClient(mock_session)
        assert client._base_url == API_BASE_URL

    def test_init_with_custom_url(self, mock_session: MagicMock) -> None:
        """Test client initializes with custom API URL."""
        custom_url = "https://custom.api.example.com/"
        client = ABCEmergencyClient(mock_session, base_url=custom_url)
        assert client._base_url == "https://custom.api.example.com"

    def test_init_strips_trailing_slash(self, mock_session: MagicMock) -> None:
        """Test client strips trailing slash from URL."""
        client = ABCEmergencyClient(mock_session, base_url="https://api.example.com/")
        assert client._base_url == "https://api.example.com"


class TestGetEmergenciesByState:
    """Test async_get_emergencies_by_state method."""

    async def test_successful_fetch(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
        sample_emergency_response: dict,
    ) -> None:
        """Test successful fetch of emergencies by state."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_emergency_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        result = await api_client.async_get_emergencies_by_state("nsw")

        assert result["stateName"] == "nsw"
        assert len(result["emergencies"]) == 1
        assert result["emergencies"][0]["headline"] == "Test Bushfire"

    async def test_empty_response(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
        empty_response: dict,
    ) -> None:
        """Test handling of empty response."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=empty_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        result = await api_client.async_get_emergencies_by_state("nsw")

        assert result["emergencies"] == []
        assert result["incidentsNumber"] == 0

    async def test_correct_url_and_headers(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
        empty_response: dict,
    ) -> None:
        """Test correct URL and headers are used."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=empty_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        await api_client.async_get_emergencies_by_state("vic")

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "emergencySearch" in call_args[0][0]
        assert "state=vic" in call_args[0][0]
        assert call_args[1]["headers"]["User-Agent"] == USER_AGENT

    async def test_connection_error(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
    ) -> None:
        """Test handling of connection errors."""
        mock_session.get = MagicMock(side_effect=ClientError("Connection failed"))

        with pytest.raises(ABCEmergencyConnectionError):
            await api_client.async_get_emergencies_by_state("nsw")

    async def test_timeout_error(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
    ) -> None:
        """Test handling of timeout errors."""
        mock_session.get = MagicMock(side_effect=TimeoutError())

        with pytest.raises(ABCEmergencyConnectionError):
            await api_client.async_get_emergencies_by_state("nsw")

    async def test_http_error(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
    ) -> None:
        """Test handling of HTTP errors (4xx, 5xx)."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=500,
                message="Internal Server Error",
            )
        )

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with pytest.raises(ABCEmergencyAPIError):
            await api_client.async_get_emergencies_by_state("nsw")

    async def test_json_decode_error(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
    ) -> None:
        """Test handling of JSON decode errors."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("", "", 0))
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with pytest.raises(ABCEmergencyAPIError):
            await api_client.async_get_emergencies_by_state("nsw")


class TestGetEmergenciesByGeohash:
    """Test async_get_emergencies_by_geohash method."""

    async def test_successful_fetch_single_geohash(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
        sample_emergency_response: dict,
    ) -> None:
        """Test successful fetch with single geohash."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_emergency_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        result = await api_client.async_get_emergencies_by_geohash(["r65"])

        assert result["stateName"] == "nsw"

    async def test_successful_fetch_multiple_geohashes(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
        sample_emergency_response: dict,
    ) -> None:
        """Test successful fetch with multiple geohashes."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_emergency_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        result = await api_client.async_get_emergencies_by_geohash(["r65", "r66", "r67"])

        assert "emergencies" in result

    async def test_correct_url_format(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
        empty_response: dict,
    ) -> None:
        """Test geohash URL is correctly formatted."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=empty_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        await api_client.async_get_emergencies_by_geohash(["r65"])

        call_args = mock_session.get.call_args
        url = call_args[0][0]
        assert "emergencySearch" in url
        assert "geohashes" in url


class TestGetAllEmergencies:
    """Test async_get_all_emergencies method."""

    async def test_successful_fetch(
        self,
        api_client: ABCEmergencyClient,
        mock_session: MagicMock,
    ) -> None:
        """Test successful fetch of all emergencies."""
        feed_response = {
            "allEmergencies": [
                {
                    "id": "AUREMER-test123",
                    "headline": "Test Fire",
                    "to": "/emergency/warning/AUREMER-test123",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:34:00+00:00",
                        "formattedTime": "4:34:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                    },
                    "eventLabelPrepared": {
                        "icon": "fire",
                        "labelText": "Bushfire",
                    },
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "50 ha",
                        "status": "Under control",
                        "source": "NSW Rural Fire Service",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [150.0, -33.0]},
                        ],
                    },
                }
            ],
            "features": [],
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=feed_response)
        mock_response.raise_for_status = MagicMock()

        mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))

        result = await api_client.async_get_all_emergencies()

        assert len(result["allEmergencies"]) == 1
        assert result["allEmergencies"][0]["id"] == "AUREMER-test123"


class AsyncContextManager:
    """Helper class to create async context manager for mocking."""

    def __init__(self, return_value: AsyncMock) -> None:
        """Initialize the context manager."""
        self.return_value = return_value

    async def __aenter__(self) -> AsyncMock:
        """Enter the context."""
        return self.return_value

    async def __aexit__(self, *args: object) -> None:
        """Exit the context."""
        pass


class TestExceptions:
    """Test exception classes."""

    def test_connection_error_is_abc_error(self) -> None:
        """Test ABCEmergencyConnectionError inherits from ABCEmergencyError."""
        from custom_components.abcemergency.exceptions import (
            ABCEmergencyConnectionError,
            ABCEmergencyError,
        )

        error = ABCEmergencyConnectionError("test")
        assert isinstance(error, ABCEmergencyError)

    def test_api_error_is_abc_error(self) -> None:
        """Test ABCEmergencyAPIError inherits from ABCEmergencyError."""
        from custom_components.abcemergency.exceptions import (
            ABCEmergencyAPIError,
            ABCEmergencyError,
        )

        error = ABCEmergencyAPIError("test")
        assert isinstance(error, ABCEmergencyError)

    def test_abc_error_is_homeassistant_error(self) -> None:
        """Test ABCEmergencyError inherits from HomeAssistantError."""
        from homeassistant.exceptions import HomeAssistantError

        from custom_components.abcemergency.exceptions import ABCEmergencyError

        error = ABCEmergencyError("test")
        assert isinstance(error, HomeAssistantError)
