from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import aiosqlite

app = FastAPI()

DB_PATH = "/opt/powersnitch/logs.db"

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.get("/logs")
async def get_logs(since: Optional[str] = Query(None, description="ISO timestamp filter")):
    try:
        logs = []
        async with aiosqlite.connect(DB_PATH) as db:
            query = "SELECT * FROM events"
            params = []

            if since:
                try:
                    datetime.fromisoformat(since)  # validate format
                    query += " WHERE timestamp >= ?"
                    params.append(since)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid 'since' format. Use ISO timestamp.")

            async with db.execute(query, params) as cursor:
                columns = [column[0] for column in cursor.description]
                async for row in cursor:
                    logs.append(dict(zip(columns, row)))

        return {"logs": logs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
