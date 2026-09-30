# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - 2026-09-30

### Breaking changes

- An HTTP error status other than 400, 401, 429 or 500 now raises `VisualCrossingException`. Before, the sync call returned `None` and the async call raised a JSON decode error.
- `ForecastData`, `ForecastDailyData` and `ForecastHourlyData` are now dataclasses. Constructor arguments and attribute names are unchanged, but attributes can now be assigned to, and two objects with the same values compare as equal.

### Fixed

- Calling `async_fetch_data()` more than once without passing a `session` no longer fails with `RuntimeError: Session is closed`.
- All timestamps are now correct in UTC, whatever the host's timezone. Before, times were only right when the host was in the same timezone as the forecast location.
- The timestamp of the current conditions no longer uses the host's date, which could be wrong around midnight.
- The temporary aiohttp session is now closed when a request fails.
- The API key is now URL-encoded in the request.

### Changed

- `VisualCrossingBadRequest`, `VisualCrossingUnauthorized`, `VisualCrossingTooManyRequests` and `VisualCrossingInternalServerError` now inherit from `VisualCrossingException`, so one `except` catches them all.
- Requests now time out after 30 seconds.
- The API key is hidden in the debug log.
- The docstrings now state the actual metric units: wind speed is km/h, not m/s.

### Development

- Added a pytest test suite in `tests/`.
- Fixed the misspelled `GIT_EDITOR` variable in the devcontainer.
- Fixed `.devcontainer/package_helper`, which pointed at the wrong paths and the removed `setup.py`.

## [1.0.2] - 2026-07-07

### Changed

- Replaced `setup.py` with `pyproject.toml`.

## [1.0.1] - 2026-07-07

### Added

- All remaining fields from the API are now available:
  - Current conditions: `snow`, `snow_depth`, `precipitation_type`, `solarenergy`, `sunrise`, `sunset` and `moon_phase`.
  - Daily forecast: the same fields, plus `precipitation_cover`, `solarradiation` and `severe_risk`.
  - Hourly forecast: `snow`, `snow_depth`, `precipitation_type`, `solarradiation`, `solarenergy`, `severe_risk` and `visibility`.

### Changed

- The publish workflow uses trusted publishing, and can now also be started manually.
- Updated the documentation.

## [1.0.0] - 2026-07-07

### Fixed

- Each `VisualCrossing` instance now gets its own API object (and session), unless one is passed in.
- Added the missing `self` on the base class's `async_fetch_data`, and corrected several type annotations.

### Changed

- The development environment now uses Python 3.14.
- Linting fixes and updated comments.

[1.1.0]: https://github.com/briis/pyVisualCrossing/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/briis/pyVisualCrossing/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/briis/pyVisualCrossing/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/briis/pyVisualCrossing/compare/v0.1.16...v1.0.0
