"""Tests for the Visual Crossing API wrapper."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
import pytest

from pyVisualCrossing import (
    VisualCrossing,
    VisualCrossingBadRequest,
    VisualCrossingException,
    VisualCrossingTooManyRequests,
    VisualCrossingUnauthorized,
)
from pyVisualCrossing import api as vc_api
from pyVisualCrossing.api import (
    UTC,
    VisualCrossingAPI,
    VisualCrossingAPIBase,
    _fetch_data,
)


def _epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def _sample(now: datetime) -> dict[str, Any]:
    """Return a minimal API response with one past and two future hours."""
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hours = [
        {
            "datetime": "x",
            "datetimeEpoch": _epoch(now - timedelta(hours=1)),
            "temp": 1.0,
        },
        {
            "datetime": "x",
            "datetimeEpoch": _epoch(now + timedelta(hours=1)),
            "temp": 2.0,
        },
        {
            "datetime": "x",
            "datetimeEpoch": _epoch(now + timedelta(hours=2)),
            "temp": 3.0,
            "visibility": 24.1,
        },
    ]
    return {
        "address": "copenhagen",
        "timezone": "Europe/Copenhagen",
        "description": "Cooling down.",
        "currentConditions": {
            "datetime": "x",
            "datetimeEpoch": _epoch(now),
            "temp": 5.5,
            "windgust": 12.0,
            "snow": 1.5,
            "moonphase": 0.25,
        },
        "days": [
            {
                "datetime": "x",
                "datetimeEpoch": _epoch(day),
                "tempmax": 8.0,
                "tempmin": 2.0,
                "precipcover": 50.0,
                "sunrise": "07:22:16",
                "hours": hours,
            }
        ],
    }


class FakeAPI(VisualCrossingAPIBase):
    """Returns canned data instead of calling the service."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.session = None
        self.calls: list[tuple] = []

    def fetch_data(self, *args: Any) -> dict[str, Any]:
        self.calls.append(args)
        return self.data

    async def async_fetch_data(self, *args: Any) -> dict[str, Any]:
        self.calls.append(args)
        return self.data


def test_parse() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    result = _fetch_data(_sample(now))

    assert result.datetime == now
    assert result.temperature == 5.5
    assert result.wind_gust_speed == 12.0
    assert result.visibility is None
    assert result.location_name == "Copenhagen"
    assert result.description == "Cooling down."
    assert result.snow == 1.5
    assert result.moon_phase == 0.25
    assert result.sunset is None

    assert len(result.forecast_daily) == 1
    assert result.forecast_daily[0].temperature == 8.0
    assert result.forecast_daily[0].temp_low == 2.0
    assert result.forecast_daily[0].precipitation_cover == 50.0
    assert result.forecast_daily[0].sunrise == "07:22:16"

    # Hours in the past are skipped
    assert [h.temperature for h in result.forecast_hourly] == [2.0, 3.0]
    assert result.forecast_hourly[1].visibility == 24.1
    assert all(h.datetime.tzinfo is UTC for h in result.forecast_hourly)


def test_parse_none() -> None:
    assert _fetch_data(None) is None


def test_options_are_sanitised() -> None:
    fake = FakeAPI(_sample(datetime.now(UTC)))
    VisualCrossing("key", 1.0, 2.0, days=30, language="xx", api=fake).fetch_data()
    assert fake.calls == [("key", 1.0, 2.0, 14, "en")]


def test_default_api_not_shared() -> None:
    first = VisualCrossing("key", 1.0, 2.0)
    second = VisualCrossing("key", 1.0, 2.0)
    assert first._api is not second._api


@pytest.fixture
async def server(monkeypatch: pytest.MonkeyPatch):
    """Serve canned responses with the HTTP status set in server.state."""
    requests: list[web.Request] = []
    state = {"status": 200}

    async def handler(request: web.Request) -> web.Response:
        requests.append(request)
        status = state["status"]
        if status != 200:
            return web.Response(status=status, text="error")
        return web.json_response(_sample(datetime.now(UTC)))

    app = web.Application()
    app.router.add_get("/{tail:.*}", handler)
    srv = TestServer(app)
    await srv.start_server()
    monkeypatch.setattr(vc_api, "VISUALCROSSING_BASE_URL", str(srv.make_url("/")))
    srv.requests = requests
    srv.state = state
    yield srv
    await srv.close()


async def test_async_without_session_can_be_called_twice(server) -> None:
    """A temporary session must not be kept around closed on the API object."""
    client = VisualCrossing("secret key&x", 1.0, 2.0)
    assert (await client.async_fetch_data()).temperature == 5.5
    assert (await client.async_fetch_data()).temperature == 5.5
    assert client._api.session is None
    # The API key is URL encoded
    assert server.requests[0].query["key"] == "secret key&x"


async def test_async_with_session_leaves_it_open(server) -> None:
    async with aiohttp.ClientSession() as session:
        client = VisualCrossing("key", 1.0, 2.0, session=session)
        await client.async_fetch_data()
        assert not session.closed


@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (400, VisualCrossingBadRequest),
        (401, VisualCrossingUnauthorized),
        (429, VisualCrossingTooManyRequests),
        (503, VisualCrossingException),
    ],
)
async def test_async_errors(server, status: int, exc: type[Exception]) -> None:
    server.state["status"] = status
    with pytest.raises(exc):
        await VisualCrossingAPI().async_fetch_data("key", 1.0, 2.0, 1, "en")


@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (401, VisualCrossingUnauthorized),
        (503, VisualCrossingException),
    ],
)
async def test_sync_errors(server, status: int, exc: type[Exception]) -> None:
    server.state["status"] = status
    with pytest.raises(exc):
        # Run the blocking call in a thread so the test server can answer.
        await asyncio.to_thread(
            VisualCrossingAPI().fetch_data, "key", 1.0, 2.0, 1, "en"
        )


async def test_sync_success(server) -> None:
    data = await asyncio.to_thread(
        VisualCrossingAPI().fetch_data, "key", 1.0, 2.0, 1, "en"
    )
    assert data["address"] == "copenhagen"
