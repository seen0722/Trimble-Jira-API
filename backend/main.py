from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from . import services
import logging
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Gate (Mass Production) Endpoints - 'OS_FCS'
@app.get("/api/gate/history")
def get_gate_history():
    try:
        data = services.get_history(label_filter="OS_FCS")
        return data
    except Exception as e:
        logging.error(f"Error fetching gate history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gate/breakdown")
def get_gate_breakdown():
    try:
        data = services.get_breakdown(label_filter="OS_FCS")
        return data
    except Exception as e:
        logging.error(f"Error fetching gate breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gate/bugs")
def get_gate_bugs():
    try:
        data = services.get_bugs_list(label_filter="OS_FCS", include_closed=True)
        return data
    except Exception as e:
        logging.error(f"Error fetching gate bugs: {e}")
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

# Store last generated report for download
last_generated_report = {"content": None, "filename": None}

@app.get("/api/weekly-report/stream")
def stream_weekly_report(provider: str = "openai"):
    """Stream weekly report generation with progress updates via SSE."""
    def event_generator():
        global last_generated_report
        try:
            from report_service import generate_realtime_report
            
            for update in generate_realtime_report(provider=provider):
                if update.get("type") == "complete":
                    # Store for download endpoint
                    last_generated_report["content"] = update.get("content")
                    last_generated_report["filename"] = update.get("filename")
                yield f"data: {json.dumps(update)}\n\n"
        except Exception as e:
            logging.error(f"Error in report stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.get("/api/weekly-report/download")
def download_weekly_report():
    """Download the last generated weekly report as a file."""
    from fastapi.responses import Response
    
    if not last_generated_report["content"]:
        raise HTTPException(status_code=404, detail="No report generated yet. Please generate first.")
    
    filename = last_generated_report["filename"] or "weekly_report.md"
    
    return Response(
        content=last_generated_report["content"],
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
