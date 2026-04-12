from fastapi import FastAPI
from pydantic import BaseModel
from constants import AlertType
import json
import os
import uvicorn
import asyncio
import tempfile

app = FastAPI()
STATUS_FILE = "alerts/alerts.json"

file_lock = asyncio.Lock()

class AlertUpdate(BaseModel):
    type: AlertType
    is_active: bool

@app.post("/alert")
async def update_alert(data: AlertUpdate):
    async with file_lock:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        current_alerts = {}
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r") as f:
                    current_alerts = json.load(f)
            except:
                pass
        current_alerts[data.type.name] = data.is_active
        temp_path=None
        try:
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(STATUS_FILE),
                text=True
            )

            with os.fdopen(fd, "w") as f:
                json.dump(current_alerts, f, indent=4)
            os.replace(temp_path, STATUS_FILE)
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return {"status": "error", "message": str(e)}

        return {"status": "ok", "updated": data.type.name, "alert_active": data.is_active}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)