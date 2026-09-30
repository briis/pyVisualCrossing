"""This module contains the code to get weather data from Visual Crossing API.

See: https://www.visualcrossing.com/.
"""

from __future__ import annotations

import abc
from datetime import datetime, timezone
import json
import logging
from typing import Any
import urllib.error
from urllib.parse import urlencode
import urllib.request

import aiohttp

from .const import (
    DEFAULT_LANGUAGE,
    MAX_FORECAST_DAYS,
    REQUEST_TIMEOUT,
    SUPPORTED_LANGUAGES,
    VISUALCROSSING_BASE_URL,
)
from .data import ForecastDailyData, ForecastData, ForecastHourlyData

UTC = timezone.utc

_LOGGER = logging.getLogger(__name__)


class VisualCrossingException(Exception):
    """Exception thrown if failing to access API."""


class VisualCrossingBadRequest(VisualCrossingException):
    """Request is invalid."""


class VisualCrossingUnauthorized(VisualCrossingException):
    """Unauthorized API Key."""


class VisualCrossingTooManyRequests(VisualCrossingException):
    """Too many daily request for the current plan."""


class VisualCrossingInternalServerError(VisualCrossingException):
    """Visual Crossing servers encounter an unexpected error."""


_HTTP_ERRORS: dict[int, tuple[type[VisualCrossingException], str]] = {
    400: (
        VisualCrossingBadRequest,
        "400 BAD_REQUEST Requests is invalid in some way (invalid dates, bad location parameter etc).",
    ),
    401: (
        VisualCrossingUnauthorized,
        "401 UNAUTHORIZED The API key is incorrect or your account status is inactive or disabled.",
    ),
    429: (
        VisualCrossingTooManyRequests,
        "429 TOO_MANY_REQUESTS Too many daily request for the current plan.",
    ),
    500: (
        VisualCrossingInternalServerError,
        "500 INTERNAL_SERVER_ERROR Visual Crossing servers encounter an unexpected error.",
    ),
}


def _raise_for_status(status: int) -> None:
    """Raise the matching exception for a non-200 HTTP status."""
    if status == 200:
        return
    exc_class, message = _HTTP_ERRORS.get(
        status, (VisualCrossingException, f"Unexpected HTTP status {status}")
    )
    raise exc_class(message)


def _build_url(
    api_key: str, latitude: float, longitude: float, days: int, language: str
) -> str:
    """Return the timeline API URL for the given location."""
    query = urlencode(
        {
            "unitGroup": "metric",
            "key": api_key,
            "contentType": "json",
            "iconSet": "icons2",
            "lang": language,
        }
    )
    url = (
        f"{VISUALCROSSING_BASE_URL}{latitude},{longitude}/today/next{days}days?{query}"
    )
    _LOGGER.debug(
        "URL: %s", url.replace(urlencode({"key": api_key}), "key=**REDACTED**")
    )
    return url


class VisualCrossingAPIBase:
    """Baseclass to use as dependency injection pattern for easier automatic testing."""

    session: aiohttp.ClientSession | None = None

    @abc.abstractmethod
    def fetch_data(
        self, api_key: str, latitude: float, longitude: float, days: int, language: str
    ) -> dict[str, Any] | None:
        """Override this."""
        raise NotImplementedError("users must define fetch_data to use this base class")

    @abc.abstractmethod
    async def async_fetch_data(
        self, api_key: str, latitude: float, longitude: float, days: int, language: str
    ) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define async_fetch_data to use this base class"
        )


class VisualCrossingAPI(VisualCrossingAPIBase):
    """Default implementation for Visual Crossing api."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Init the API with or without session."""
        self.session = session

    def fetch_data(
        self, api_key: str, latitude: float, longitude: float, days: int, language: str
    ) -> dict[str, Any]:
        """Get data from API."""
        url = _build_url(api_key, latitude, longitude, days, language)
        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
                return json.load(response)
        except urllib.error.HTTPError as err:
            _raise_for_status(err.code)
            raise

    async def async_fetch_data(
        self, api_key: str, latitude: float, longitude: float, days: int, language: str
    ) -> dict[str, Any]:
        """Get data from API."""
        url = _build_url(api_key, latitude, longitude, days, language)

        if self.session is not None:
            return await self._async_get(self.session, url)

        # No session supplied, so use a temporary one that is always closed.
        async with aiohttp.ClientSession() as session:
            return await self._async_get(session, url)

    @staticmethod
    async def _async_get(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
        """Perform the GET request and return the decoded JSON."""
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        ) as response:
            _raise_for_status(response.status)
            return await response.json(content_type=None)


class VisualCrossing:
    """Class that uses the weather API from Visual Crossing to retreive Weather Data."""

    def __init__(
        self,
        api_key: str,
        latitude: float,
        longitude: float,
        days: int = MAX_FORECAST_DAYS,
        language: str = DEFAULT_LANGUAGE,
        session: aiohttp.ClientSession | None = None,
        api: VisualCrossingAPIBase | None = None,
    ) -> None:
        """Return data from Weather API."""
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._days = min(days, MAX_FORECAST_DAYS)
        self._language = (
            language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        )
        self._api = api if api is not None else VisualCrossingAPI()
        self._json_data: dict[str, Any] | None = None

        if session:
            self._api.session = session

    def fetch_data(self) -> ForecastData | None:
        """Return current conditions with daily and hourly forecasts."""
        self._json_data = self._api.fetch_data(
            self._api_key,
            self._latitude,
            self._longitude,
            self._days,
            self._language,
        )
        return _fetch_data(self._json_data)

    async def async_fetch_data(self) -> ForecastData | None:
        """Return current conditions with daily and hourly forecasts."""
        self._json_data = await self._api.async_fetch_data(
            self._api_key,
            self._latitude,
            self._longitude,
            self._days,
            self._language,
        )
        return _fetch_data(self._json_data)


def _to_datetime(item: dict[str, Any]) -> datetime:
    """Return the UTC time of an API record.

    The epoch value is used because the "datetime" strings are local to the
    forecast location, which is not necessarily the timezone of this host.
    """
    return datetime.fromtimestamp(item["datetimeEpoch"], UTC)


def _fetch_data(api_result: dict[str, Any] | None) -> ForecastData | None:
    """Return result from API as ForecastData."""

    # Return nothing if the Request for data fails
    if api_result is None:
        return None

    weather_data = _get_current_data(api_result)
    now = datetime.now(UTC)

    forecast_daily: list[ForecastDailyData] = []
    forecast_hourly: list[ForecastHourlyData] = []

    for item in api_result["days"]:
        forecast_daily.append(
            ForecastDailyData(
                datetime=_to_datetime(item),
                temperature=item.get("tempmax"),
                temp_low=item.get("tempmin"),
                apparent_temperature=item.get("feelslike"),
                condition=item.get("conditions"),
                icon=item.get("icon"),
                cloud_cover=item.get("cloudcover"),
                dew_point=item.get("dew"),
                humidity=item.get("humidity"),
                precipitation_probability=item.get("precipprob"),
                precipitation=item.get("precip"),
                pressure=item.get("pressure"),
                wind_bearing=item.get("winddir"),
                wind_speed=item.get("windspeed"),
                wind_gust=item.get("windgust"),
                uv_index=item.get("uvindex"),
                snow=item.get("snow"),
                snow_depth=item.get("snowdepth"),
                precipitation_type=item.get("preciptype"),
                precipitation_cover=item.get("precipcover"),
                solarradiation=item.get("solarradiation"),
                solarenergy=item.get("solarenergy"),
                severe_risk=item.get("severerisk"),
                sunrise=item.get("sunrise"),
                sunset=item.get("sunset"),
                moon_phase=item.get("moonphase"),
            )
        )

        # Add the hours of this day that are still in the future
        for row in item.get("hours", []):
            hour_time = _to_datetime(row)
            if hour_time <= now:
                continue
            forecast_hourly.append(
                ForecastHourlyData(
                    datetime=hour_time,
                    temperature=row.get("temp"),
                    apparent_temperature=row.get("feelslike"),
                    condition=row.get("conditions"),
                    cloud_cover=row.get("cloudcover"),
                    icon=row.get("icon"),
                    dew_point=row.get("dew"),
                    humidity=row.get("humidity"),
                    precipitation=row.get("precip"),
                    precipitation_probability=row.get("precipprob"),
                    pressure=row.get("pressure"),
                    wind_bearing=row.get("winddir"),
                    wind_gust_speed=row.get("windgust"),
                    wind_speed=row.get("windspeed"),
                    uv_index=row.get("uvindex"),
                    snow=row.get("snow"),
                    snow_depth=row.get("snowdepth"),
                    precipitation_type=row.get("preciptype"),
                    solarradiation=row.get("solarradiation"),
                    solarenergy=row.get("solarenergy"),
                    severe_risk=row.get("severerisk"),
                    visibility=row.get("visibility"),
                )
            )

    weather_data.forecast_daily = forecast_daily
    weather_data.forecast_hourly = forecast_hourly

    return weather_data


def _get_current_data(api_result: dict[str, Any]) -> ForecastData:
    """Return the current conditions from the API result."""
    item = api_result["currentConditions"]

    return ForecastData(
        datetime=_to_datetime(item),
        apparent_temperature=item.get("feelslike"),
        condition=item.get("conditions"),
        cloud_cover=item.get("cloudcover"),
        dew_point=item.get("dew"),
        humidity=item.get("humidity"),
        icon=item.get("icon"),
        precipitation=item.get("precip"),
        precipitation_probability=item.get("precipprob"),
        pressure=item.get("pressure"),
        solarradiation=item.get("solarradiation"),
        temperature=item.get("temp"),
        visibility=item.get("visibility"),
        uv_index=item.get("uvindex"),
        wind_bearing=item.get("winddir"),
        wind_gust_speed=item.get("windgust"),
        wind_speed=item.get("windspeed"),
        location_name=api_result.get("address", ""),
        description=api_result.get("description", ""),
        snow=item.get("snow"),
        snow_depth=item.get("snowdepth"),
        precipitation_type=item.get("preciptype"),
        solarenergy=item.get("solarenergy"),
        sunrise=item.get("sunrise"),
        sunset=item.get("sunset"),
        moon_phase=item.get("moonphase"),
    )
