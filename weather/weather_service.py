from datetime import datetime
import requests
import json
from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class WeatherResponse:
    time:str
    temp:float
    weather_code:int
    weather_text:str

class WeatherService:
    class Locations(Enum):
        HOME = "HOME"
        SCHOOL = "SCHOOL"
    MAX_RETRY = 4
    WEATHER_MAP = {
        0: "快晴", 1: "晴", 2: "晴", 3: "くもり",
        45: "霧", 48: "霧氷",
        51: "弱い霧雨", 53: "霧雨", 55: "強い霧雨",
        61: "小雨", 63: "雨", 65: "強い雨",
        80: "にわか雨", 81: "にわか雨", 82: "激しいにわか雨",
        95: "雷雨",
    }
    def __init__(self,
                 home_waypoint:tuple[float, float] = (34.7392, 135.4168),
                 school_waypoint:tuple[float, float] = (34.8481, 135.6279)):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.coords = {
            WeatherService.Locations.HOME: home_waypoint,
            WeatherService.Locations.SCHOOL: school_waypoint
        }


    def fetch_weather(self, location: Locations, hour: int=7) -> None|WeatherResponse:
        """
        hours引数は、今日の0時からどれぐらいかです。
        例：
        今日が4月3日だとすると、
        - 4月3日の7時なら、hour=7
        - 4月4日の7時なら、hour=31
        0 <= hour <= 167
        """
        lat, lon = self.coords[location]
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,weather_code",
            "timezone": "Asia/Tokyo",
        }
        weather_json: dict = {}
        for attempt in range(WeatherService.MAX_RETRY):
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                weather_data = response
                break
            except requests.RequestException:
                print(f"Failed to get weather data. Retrying... ({attempt})")
                if attempt == WeatherService.MAX_RETRY - 1:
                    return None
        try:
            weather_json = weather_data.json()
        except json.JSONDecodeError as e:
            print({str(e)})
            return None
        try:
            code = weather_json["hourly"]["weather_code"][hour]
            return WeatherResponse(
                    time=weather_json["hourly"]["time"][hour],
                    temp=weather_json["hourly"]["temperature_2m"][hour],
                    weather_code=code,
                    weather_text=self.WEATHER_MAP.get(code, f"不明({code})")
            )
        except:
            print(f"Error: Data for hour {hour} not found.")
            return None
        
ws = WeatherService()
print(ws.fetch_weather(WeatherService.Locations.SCHOOL))