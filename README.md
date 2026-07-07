# Python Wrapper for Visual Crossing Weather API

This Python Wrapper retrives data from the [Visual Crossing](https://www.visualcrossing.com/) API. Visual Crossing has an extensive Weather API for both historical and forecast weather data, and they have a Free Tier API Key which enables up to 1000 calls per day.

In order to get started you must create an Account with Visual Crossing and then create an API Key. You do this by accessing [this website](https://www.visualcrossing.com/weather-data-editions) and clicking on the **Free** plan. Then follow the instructions to create and account and store your key in a safe place.

## Usage

Install the module by using this command in a terminal: `pip install pyVisualCrossing`

And then see `test_module.py` for a usage example.

## Parameters

```python
# Initialise the module
vcapi = VisualCrossing(
    api_key,
    latitude,
    longitude,
    days=7,
    language="da"
)
```

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| `api_key` | Yes      | `None`  | This is the API Key you signed up for from Visual Crossing. See above for instructions |
| `latitude` | Yes     | `None`  | Latitude for the location position |
| `longitude` | Yes     | `None`  | Longitude for the location position |
| `days` | No     | `14`  | Numbers of days to retrieve forecast for. 14 days means today plus the next 14 days. On the Free plan, this is the maximum number of days |
| `language` | No     | `en`  | The language in which text strings should be returned. Se below for list of valid languages. |
| `session` | No     | `None`  | An `aiohttp.ClientSession` to reuse for the async function. If not supplied, a session is created and closed automatically. |

For an in-depth description of the Visual Crossing API, go [here](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/)

## Fetching Data

Once initialised, call either the synchronous or the async method to retrieve data. Both return a single `ForecastData` object (or `None` if the request failed), holding the current conditions plus a daily and an hourly forecast list.

```python
# Synchronous
data = vcapi.fetch_data()

# Async
data = await vcapi.async_fetch_data()

print(data.temperature)
for day in data.forecast_daily:
    print(day.datetime, day.temperature, day.condition)

for hour in data.forecast_hourly:
    print(hour.datetime, hour.temperature, hour.condition)
```

## Exceptions

If the API request fails, one of these exceptions (all importable from `pyVisualCrossing`) is raised:

| Exception | Description |
| --------- | ----------- |
| `VisualCrossingBadRequest` | The request was invalid (invalid dates, bad location parameter, etc.) |
| `VisualCrossingUnauthorized` | The API key is incorrect, or the account is inactive or disabled |
| `VisualCrossingTooManyRequests` | Too many daily requests for the current plan |
| `VisualCrossingInternalServerError` | Visual Crossing's servers encountered an unexpected error |
| `VisualCrossingException` | Generic base exception for failing to access the API |

## Data

### Current Conditions (`ForecastData`)

| Property | Description |
| -------- | ----------- |
| `datetime` | Valid time (UTC) |
| `temperature` | Air temperature |
| `apparent_temperature` | Feels-like temperature |
| `dew_point` | Dew point |
| `condition` | Weather condition text |
| `icon` | Weather condition icon id |
| `cloud_cover` | Cloud coverage (%) |
| `humidity` | Humidity (%) |
| `precipitation` | Precipitation |
| `precipitation_probability` | Probability of precipitation (%) |
| `pressure` | Sea level pressure |
| `solarradiation` | Solar radiation (W/m2) |
| `visibility` | Visibility |
| `uv_index` | UV index |
| `wind_bearing` | Wind bearing (degrees) |
| `wind_speed` | Wind speed |
| `wind_gust_speed` | Wind gust speed |
| `location_name` | Name of the location |
| `description` | Weather description |
| `update_time` | Timestamp of when the data was fetched |
| `forecast_daily` | List of `ForecastDailyData` |
| `forecast_hourly` | List of `ForecastHourlyData` |

### Daily Forecast (`ForecastDailyData`)

| Property | Description |
| -------- | ----------- |
| `datetime` | Valid date (UTC) |
| `temperature` | Max air temperature for the day |
| `temp_low` | Min air temperature for the day |
| `apparent_temperature` | Feels-like temperature |
| `condition` | Weather condition text |
| `icon` | Weather condition icon id |
| `cloud_cover` | Cloud coverage (%) |
| `dew_point` | Dew point |
| `humidity` | Humidity (%) |
| `precipitation` | Precipitation |
| `precipitation_probability` | Probability of precipitation (%) |
| `pressure` | Sea level pressure |
| `uv_index` | UV index |
| `wind_bearing` | Wind bearing (degrees) |
| `wind_speed` | Wind speed |
| `wind_gust` | Wind gust speed |

### Hourly Forecast (`ForecastHourlyData`)

Only hours later than the current time are included.

| Property | Description |
| -------- | ----------- |
| `datetime` | Valid date and time (UTC) |
| `temperature` | Air temperature |
| `apparent_temperature` | Feels-like temperature |
| `condition` | Weather condition text |
| `icon` | Weather condition icon id |
| `cloud_cover` | Cloud coverage (%) |
| `dew_point` | Dew point |
| `humidity` | Humidity (%) |
| `precipitation` | Precipitation |
| `precipitation_probability` | Probability of precipitation (%) |
| `pressure` | Sea level pressure |
| `uv_index` | UV index |
| `wind_bearing` | Wind bearing (degrees) |
| `wind_speed` | Wind speed |
| `wind_gust_speed` | Wind gust speed |

## Languages
Available languages include: **ar** (Arabic), **bg** (Bulgiarian), **cs** (Czech), **da** (Danish), **de** (German), **el** (Greek Modern), **en** (English), **es** (Spanish), **fa** (Farsi), **fi** (Finnish), **fr** (French), **he** (Hebrew), **hu**, (Hungarian), **it** (Italian), **ja** (Japanese), **ko** (Korean), **nl** (Dutch), **pl** (Polish), **pt** (Portuguese), **sr** (Serbian), **sv** (Swedish), **tr** (Turkish), **uk** (Ukranian), **vi** (Vietnamese) and **zh** (Chinese).

## Metrics
All records are returned using the *Metric* unit system. There is no conversion possible at the moment.

| Weather variable	                   | Measurement Unit         |
| -----------------------------------  | ------------------------ |
| Datetime	                           | UTC datetime             |
| Temperature, Heat Index & Wind Chill | Degrees Celcius          |
| Precipitation	                       | Millimeters              |
| snow	                               | Centimeters              |
| Wind & Wind Gust	                   | Kilometers Per Hour      |
| Visibility	                       | Kilometers               |
| Pressure	                           | Millibars (Hectopascals) |
| Solar Radiation	                   | W/m2                     |
| Solar Energy	                       | MJ/m2                    |

## Icons
We use the Iconset *icons2*, which gives a more detailed description of the conditions.

| Icon id	            | Weather Conditions |
| --------------------  | ---------------------------- |
| snow	                | Amount of snow is greater than zero |
| snow-showers-day	    | Periods of snow during the day |
| snow-showers-night    | Periods of snow during the night |
| thunder-rain	        | Thunderstorms throughout the day or night |
| thunder-showers-day   | Possible thunderstorms throughout the day |
| thunder-showers-night | Possible thunderstorms throughout the night |
| rain                  | Amount of rainfall is greater than zero |
| showers-day           | Rain showers during the day |
| showers-night         | Rain showers during the night |
| fog                   | Visibility is low (lower than one kilometer or mile) |
| wind                  | Wind speed is high (greater than 30 kph or mph) |
| cloudy                | Cloud cover is greater than 90% cover |
| partly-cloudy-day     | Cloud cover is greater than 20% cover during day time. |
| partly-cloudy-night   | Cloud cover is greater than 20% cover during night time. |
| clear-day             | Cloud cover is less than 20% cover during day time |
| clear-night           | Cloud cover is less than 20% cover during night time |

## TODO

- Add all available items to the Data Structure
