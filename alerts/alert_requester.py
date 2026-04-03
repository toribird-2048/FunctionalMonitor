from constants import AlertType
from weather.weather_service import WeatherService
import time
import requests
from datetime import datetime, timezone, timedelta

weather_service = WeatherService()
alert_manager_url = "http://localhost:8000/alert"
JST = timezone(timedelta(hours=+9))

ACTIVE_HOUR_RANGE= range(6,9)

def send_request(alert_type: AlertType, is_active: bool):
    data = {
        "type": alert_type.name,
        "is_active": is_active
    }
    try:
        response = requests.post(alert_manager_url, json=data, timeout=5)
        response.raise_for_status()
        print("Success:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"Error sending alert: {e}")


def update_alert_umbrella():
    """
    現在天気取得による傘警告に使用
    """
    now = datetime.now(JST)
    if now.hour not in ACTIVE_HOUR_RANGE:
        print(f"現在時刻 {now.hour}時はアクティブ時間外です。自動的に傘アラートは解除されます。")
        send_request(AlertType.UMBRELLA_REQUIRED, False)
        return
    home_weather_7 = weather_service.fetch_weather(WeatherService.Locations.HOME)
    home_weather_8 = weather_service.fetch_weather(WeatherService.Locations.HOME, hour=8)    
    school_weather_7 = weather_service.fetch_weather(WeatherService.Locations.SCHOOL)
    school_weather_8 = weather_service.fetch_weather(WeatherService.Locations.SCHOOL, hour=8)
    weathers = [weather for weather in (home_weather_7, home_weather_8, school_weather_7, school_weather_8) if weather is not None]
    if not weathers:
        print("weather data could not be retrieved.")
        return

    is_umbrella_required = False
    for weather in weathers:
        if "雨" in weather.weather_text or "霧" in weather.weather_text or "雪" in weather.weather_text:
            is_umbrella_required = True
            break
    send_request(AlertType.UMBRELLA_REQUIRED, is_umbrella_required)

alert_updaters = [update_alert_umbrella]

if __name__ == "__main__":
    while True:
        now = datetime.now(JST)
        print("定期アラートチェック開始...")
        for updater in alert_updaters:
            try:
                print(f"updater:{updater.__name__}を開始...")
                updater()
                print(f"updater:{updater.__name__}を終了。")
            except Exception as e:
                print(f"updater:{updater.__name__}の実行中にエラーが発生。\nエラー：{e}")
        print("15分後に再チェックします。")
        time.sleep(900)

