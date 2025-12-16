from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import services
import logging

app = FastAPI(title="Jira Dashboard API")

# Configure CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Jira Dashboard API is running"}

@app.get("/api/history")
def get_history():
    try:
        data = services.get_history()
        return data
    except Exception as e:
        logging.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/breakdown")
def get_breakdown():
    try:
        data = services.get_breakdown()
        return data
    except Exception as e:
        logging.error(f"Error fetching breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bugs")
def get_bugs():
    try:
        data = services.get_bugs_list()
        return data
    except Exception as e:
        logging.error(f"Error fetching bugs list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/snapshot")
def trigger_snapshot():
    try:
        result = services.trigger_snapshot()
        if "error" in result:
             raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logging.error(f"Error processing snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
