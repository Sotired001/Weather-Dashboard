import pytest
import json
from app import app, get_weather_data, get_forecast_data

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Advanced Weather Dashboard" in response.data

def test_get_weather_data_mock(requests_mock):
    """Test get_weather_data with mocked API response."""
    station = 'KBWI'
    mock_response = [{
        "icaoId": "KBWI",
        "name": "Baltimore-Washington International Thurgood Marsha",
        "reportTime": "2025-10-21 18:54:00",
        "temp": 15.0,
        "dewp": 8.0,
        "wspd": 10,
        "wgst": None,
        "wdir": 320,
        "visib": "10+",
        "altim": 1018.0,
        "cover": "SCT",
        "fltCat": "VFR",
        "lat": 39.17,
        "lon": -76.67,
        "rawOb": "KBWI 211854Z 32010KT 10SM SCT050 15/08 A3006 RMK AO2 SLP179 T01500083"
    }]

    requests_mock.get(f"https://aviationweather.gov/api/data/metar?ids={station}&format=json", json=mock_response)

    data = get_weather_data(station)

    assert data is not None
    assert data['station'] == 'KBWI'
    assert data['temperature_c'] == 15.0
    assert data['flight_category'] == 'VFR'

def test_get_forecast_data_mock(requests_mock):
    """Test get_forecast_data with mocked API response."""
    lat, lon = 39.17, -76.67
    mock_response = {
        "daily": {
            "time": ["2025-10-21", "2025-10-22", "2025-10-23", "2025-10-24", "2025-10-25", "2025-10-26", "2025-10-27"],
            "temperature_2m_max": [70.0, 72.0, 68.0, 65.0, 66.0, 69.0, 71.0],
            "temperature_2m_min": [50.0, 52.0, 48.0, 45.0, 46.0, 49.0, 51.0]
        }
    }

    requests_mock.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone=auto&forecast_days=7", json=mock_response)

    data = get_forecast_data(lat, lon)

    assert data is not None
    assert len(data['days']) == 7
    assert len(data['avg_temps']) == 7
    assert data['max_temps'][0] == 70.0
