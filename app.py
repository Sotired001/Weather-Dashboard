"""
Advanced Weather Dashboard
A Flask-based web application that displays real-time aviation weather data
and 7-day temperature forecasts for airports worldwide.

Author: Created with Claude Code
APIs Used:
- Aviation Weather API (METAR data)
- Open-Meteo API (7-day forecasts)
"""

from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Popular airports for quick selection in the UI
POPULAR_AIRPORTS = [
    {'code': 'KBWI', 'name': 'Baltimore-Washington Intl'},
    {'code': 'KJFK', 'name': 'New York JFK'},
    {'code': 'KLAX', 'name': 'Los Angeles Intl'},
    {'code': 'KORD', 'name': 'Chicago O\'Hare'},
    {'code': 'KATL', 'name': 'Atlanta Hartsfield'},
    {'code': 'KDFW', 'name': 'Dallas/Fort Worth'},
    {'code': 'KDEN', 'name': 'Denver Intl'},
    {'code': 'KSFO', 'name': 'San Francisco Intl'},
    {'code': 'KMIA', 'name': 'Miami Intl'},
    {'code': 'KBOS', 'name': 'Boston Logan'},
    {'code': 'KSEA', 'name': 'Seattle-Tacoma'},
    {'code': 'KLAS', 'name': 'Las Vegas McCarran'},
    {'code': 'KPHX', 'name': 'Phoenix Sky Harbor'},
    {'code': 'KIAH', 'name': 'Houston Intercontinental'},
    {'code': 'KMCO', 'name': 'Orlando Intl'},
]

def get_forecast_data(lat, lon):
    """Fetches 7-day forecast from Open-Meteo API (free, no key required)"""
    try:
        # Open-Meteo API - completely free, no API key needed
        api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone=auto&forecast_days=7"

        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if 'daily' in data:
            daily = data['daily']

            # Get day names
            days = []
            for date_str in daily['time']:
                date_obj = datetime.fromisoformat(date_str)
                days.append(date_obj.strftime('%a'))  # Mon, Tue, etc.

            # Calculate average from min and max
            max_temps = daily['temperature_2m_max']
            min_temps = daily['temperature_2m_min']
            avg_temps = [(max_t + min_t) / 2 for max_t, min_t in zip(max_temps, min_temps)]

            return {
                'days': days,
                'max_temps': max_temps,
                'min_temps': min_temps,
                'avg_temps': avg_temps,
                'source': 'Open-Meteo Forecast'
            }

        return None
    except Exception as e:
        print(f"Forecast API Error: {e}")
        return None

def get_weather_data(station_code="KBWI"):
    """Fetches and processes weather data from the API."""
    api_url = f"https://aviationweather.gov/api/data/metar?ids={station_code}&format=json"

    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        report = data[0]

        # Determine weather description from cloud cover
        description = 'Clear'
        weather_icon = '☀️'
        if 'cover' in report:
            cover_map = {
                'SKC': ('Clear Sky', '☀️'),
                'CLR': ('Clear', '☀️'),
                'FEW': ('Few Clouds', '🌤️'),
                'SCT': ('Scattered Clouds', '⛅'),
                'BKN': ('Broken Clouds', '🌥️'),
                'OVC': ('Overcast', '☁️')
            }
            description, weather_icon = cover_map.get(report['cover'], (report['cover'], '🌤️'))

        # Get flight category for visual indicator
        flight_cat = report.get('fltCat', 'UNKNOWN')

        # Calculate temperatures in both units
        temp_c = report.get('temp')
        temp_f = (temp_c * 9/5) + 32 if temp_c is not None else None
        dewp_c = report.get('dewp')
        dewp_f = (dewp_c * 9/5) + 32 if dewp_c is not None else None

        # Calculate relative humidity if we have temp and dewpoint
        humidity = None
        if temp_c is not None and dewp_c is not None:
            humidity = round(100 * (pow(10, (7.5 * dewp_c / (237.7 + dewp_c))) / pow(10, (7.5 * temp_c / (237.7 + temp_c)))))

        weather_info = {
            'station': report.get('icaoId'),
            'station_name': report.get('name'),
            'time': report.get('reportTime'),
            'temperature_c': round(temp_c, 1) if temp_c else None,
            'temperature_f': round(temp_f, 1) if temp_f else None,
            'dewpoint_c': round(dewp_c, 1) if dewp_c else None,
            'dewpoint_f': round(dewp_f, 1) if dewp_f else None,
            'humidity': humidity,
            'wind_speed': report.get('wspd'),
            'wind_gust': report.get('wgst'),
            'wind_direction': report.get('wdir'),
            'visibility': report.get('visib'),
            'pressure': report.get('altim'),
            'description': description,
            'icon': weather_icon,
            'flight_category': flight_cat,
            'clouds': report.get('clouds', []),
            'raw_report': report.get('rawOb'),
            'lat': report.get('lat'),
            'lon': report.get('lon')
        }
        return weather_info
    except requests.exceptions.Timeout:
        print("API Request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return None
    except json.JSONDecodeError:
        print("Failed to decode JSON from response.")
        return None

@app.route('/')
def home():
    # Get station code from URL parameter or default to KBWI
    station_code = request.args.get('station', 'KBWI').upper()
    weather_data = get_weather_data(station_code)

    # If API fails, use mock data so the page still loads
    if weather_data is None:
        weather_data = {
            'station': station_code,
            'station_name': f'{station_code} - Data Unavailable',
            'time': '2025-10-20T16:50:00Z',
            'temperature_c': 15,
            'temperature_f': 59,
            'wind_speed': 10,
            'description': 'Partly cloudy',
            'icon': '⛅',
            'raw_report': 'Mock data - API unavailable',
            'error': True
        }

    # Get real forecast data if we have lat/lon from weather data
    forecast_data = None
    if weather_data and 'lat' in weather_data and 'lon' in weather_data:
        forecast_data = get_forecast_data(weather_data['lat'], weather_data['lon'])

    # Use forecast data if available, otherwise fallback to mock data
    if forecast_data:
        days = forecast_data['days']
        daily_avg_temps = [round(temp, 1) for temp in forecast_data['avg_temps']]
        daily_min_temps = [round(temp, 1) for temp in forecast_data['min_temps']]
        daily_max_temps = [round(temp, 1) for temp in forecast_data['max_temps']]
        forecast_source = forecast_data['source']
    else:
        # Fallback mock data
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        daily_avg_temps = [68.2, 69.5, 77.8, 78.0, 77.2, 80.2, 64.8]
        daily_min_temps = [55.1, 58.3, 64.2, 65.8, 63.5, 68.9, 52.4]
        daily_max_temps = [81.3, 80.7, 91.4, 90.2, 90.9, 91.5, 77.2]
        forecast_source = "Sample Data"

    return render_template('index.html',
                         weather=weather_data,
                         days=days,
                         avg_temps=daily_avg_temps,
                         min_temps=daily_min_temps,
                         max_temps=daily_max_temps,
                         popular_airports=POPULAR_AIRPORTS,
                         current_station=station_code,
                         forecast_source=forecast_source)

@app.route('/api/weather/<station_code>')
def api_weather(station_code):
    """API endpoint to get weather data for any station"""
    weather_data = get_weather_data(station_code.upper())
    if weather_data:
        return jsonify(weather_data)
    else:
        return jsonify({'error': 'Station not found or API unavailable'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)