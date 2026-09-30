"""Holds the Data Classes for Visual Crossing Wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ForecastDailyData:
    """Class to hold daily forecast data.

    Units are metric: temperatures in Celsius, precipitation in mm, snow in cm,
    pressure in mb, wind speed in km/h, wind bearing in degrees, solar radiation
    in W/m2 and solar energy in MJ/m2. Sunrise and sunset are local times of the
    forecast location and moon phase is a fraction between 0 and 1.
    """

    datetime: datetime
    temperature: float | None
    temp_low: float | None
    apparent_temperature: float | None
    condition: str | None
    icon: str | None
    cloud_cover: float | None
    dew_point: float | None
    humidity: float | None
    precipitation_probability: float | None
    precipitation: float | None
    pressure: float | None
    wind_bearing: float | None
    wind_speed: float | None
    wind_gust: float | None
    uv_index: float | None
    snow: float | None = None
    snow_depth: float | None = None
    precipitation_type: list[str] | None = None
    precipitation_cover: float | None = None
    solarradiation: float | None = None
    solarenergy: float | None = None
    severe_risk: float | None = None
    sunrise: str | None = None
    sunset: str | None = None
    moon_phase: float | None = None


@dataclass(slots=True)
class ForecastHourlyData:
    """Class to hold hourly forecast data.

    Units are the same as for ForecastDailyData, plus visibility in km.
    """

    datetime: datetime
    temperature: float | None
    apparent_temperature: float | None
    condition: str | None
    cloud_cover: float | None
    icon: str | None
    dew_point: float | None
    humidity: float | None
    precipitation: float | None
    precipitation_probability: float | None
    pressure: float | None
    wind_bearing: float | None
    wind_gust_speed: float | None
    wind_speed: float | None
    uv_index: float | None
    snow: float | None = None
    snow_depth: float | None = None
    precipitation_type: list[str] | None = None
    solarradiation: float | None = None
    solarenergy: float | None = None
    severe_risk: float | None = None
    visibility: float | None = None


@dataclass(slots=True)
class ForecastData:
    """Class to hold current conditions and the daily and hourly forecasts.

    Units are the same as for ForecastHourlyData.
    """

    datetime: datetime
    apparent_temperature: float | None
    condition: str | None
    cloud_cover: float | None
    dew_point: float | None
    humidity: float | None
    icon: str | None
    precipitation: float | None
    precipitation_probability: float | None
    pressure: float | None
    solarradiation: float | None
    temperature: float | None
    visibility: float | None
    uv_index: float | None
    wind_bearing: float | None
    wind_gust_speed: float | None
    wind_speed: float | None
    location_name: str
    description: str
    snow: float | None = None
    snow_depth: float | None = None
    precipitation_type: list[str] | None = None
    solarenergy: float | None = None
    sunrise: str | None = None
    sunset: str | None = None
    moon_phase: float | None = None
    forecast_daily: list[ForecastDailyData] | None = None
    forecast_hourly: list[ForecastHourlyData] | None = None

    def __post_init__(self) -> None:
        """Normalise the location name."""
        self.location_name = str(self.location_name).capitalize()

    @property
    def update_time(self) -> str:
        """Last updated, as an ISO 8601 string."""
        return datetime.now().isoformat()
