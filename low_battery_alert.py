from fastapi import FastAPI
from pydantic import BaseModel
from main import AlertUi
import json
import os
import uvicorn

app = FastAPI()
STATUS_FILE = "alerts.json"

class AlertUpdate(BaseModel):
    type: AlertUi.AlertType
    active: bool

@app.post("/alert")
async def update_alert(data: AlertUpdate):
    current_alerts = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                current_alerts = json.load(f)
        except:
            pass
    current_alerts[data.type.name] = data.active
    
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(current_alerts, f, indent=4)
    except IOError:
        return {"status": "error", "message": "Failed to write file"}

    return {"status": "ok", "updated": data.type.name, "alert_active": current_alerts[data.type.name]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
