from fastapi import FastAPI
from pydantic import BaseModel
from main import AlertUi
import json
import os
import uvicorn
import asyncio
import tempfile

app = FastAPI()
STATUS_FILE = "alerts/alerts.json"

file_lock = asyncio.Lock()

class AlertUpdate(BaseModel):
    type: AlertUi.AlertType
    is_active: bool

@app.post("/alert")
async def update_alert(data: AlertUpdate):
    async with file_lock:
        current_alerts = {}
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r") as f:
                    current_alerts = json.load(f)
            except:
                pass
        current_alerts[data.type.name] = data.is_active
        
        try:
            with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(STATUS_FILE)) as tf:
                json.dump(current_alerts, tf, indent=4)
                temp_name = tf.name
            os.replace(temp_name, STATUS_FILE)
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return {"status": "ok", "updated": data.type.name, "alert_active": data.is_active}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)