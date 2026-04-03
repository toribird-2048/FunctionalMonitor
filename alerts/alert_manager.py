from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager
from pydantic import BaseModel
from main import AlertUi
import json
import os
import uvicorn
from weather.weather_service import WeatherService

weather_service = WeatherService()

class AlertUpdate(BaseModel):
    type: AlertUi.AlertType
    is_active: bool

class AlertManager:
    STATUS_FILE = "alerts/alerts.json"
    @classmethod
    def update(cls, alert_type: AlertUi.AlertType, is_active: bool):
        current_alerts = {}
        if os.path.exists(cls.STATUS_FILE):
            try:
                with open(cls.STATUS_FILE, "r") as f:
                    current_alerts = json.load(f)
            except:
                pass
        current_alerts[alert_type.name] = is_active
    
        try:
            with open(cls.STATUS_FILE, "w") as f:
                json.dump(current_alerts, f, indent=4)
        except IOError:
            return {"status": "error", "message": "Failed to write file"}

        return {"status": "ok", "updated": alert_type.name, "alert_active": current_alerts[alert_type.name]}



def update_alert_umbrella():
    """
    現在天気取得による傘警告に使用
    """
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
    AlertManager.update(AlertUi.AlertType.UMBRELLA_REQUIRED, is_umbrella_required)

not_http_alert_updaters = [update_alert_umbrella]
async def not_http_alert_loop():
    while True:
        print("定期アラートチェック開始...")
        for updater in not_http_alert_updaters:
            try:
                print(f"updater:{updater.__name__}を開始...")
                await asyncio.to_thread(updater)
                print(f"updater:{updater.__name__}を終了。1時間待機します。")
            except Exception as e:
                print(f"updater:{updater.__name__}の実行中にエラーが発生。\nエラー：{e}")
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(not_http_alert_loop())
    print("バックグラウンドタスクを開始しました。")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("バックグラウンドタスクを正常に終了しました。")

app = FastAPI(lifespan=lifespan)


@app.post("/alert")
async def update_alert_http(data: AlertUpdate):
    """
    現在スマホとiPadの低充電警告用
    """
    return AlertManager.update(data.type, data.is_active)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
