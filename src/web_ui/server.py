"""
FastAPI Web UI Server for Academic Agent v2.3+

Provides web interface with live updates via WebSocket.

Run:
    python -m src.web_ui.server --port 8000
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App
app = FastAPI(title="Academic Agent Web UI", version="2.3")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State
class ResearchSession:
    """Represents an active research session"""
    def __init__(self, session_id: str, query: str, mode: str):
        self.session_id = session_id
        self.query = query
        self.mode = mode
        self.status = "running"
        self.current_phase = 1
        self.progress = 0
        self.papers_found = 0
        self.pdfs_downloaded = 0
        self.results = []
        self.log_messages = []
        self.start_time = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "query": self.query,
            "mode": self.mode,
            "status": self.status,
            "current_phase": self.current_phase,
            "progress": self.progress,
            "papers_found": self.papers_found,
            "pdfs_downloaded": self.pdfs_downloaded,
            "start_time": self.start_time.isoformat()
        }

# Global state
active_sessions: Dict[str, ResearchSession] = {}
websocket_connections: Set[WebSocket] = set()

# Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for conn in dead_connections:
            self.active_connections.remove(conn)

manager = ConnectionManager()

# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Serve main HTML page"""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    else:
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Academic Agent v2.3</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>🎓 Academic Agent v2.3 - Web UI</h1>
    <p>Frontend not found. Please create static/index.html</p>
</body>
</html>
        """)

@app.post("/api/start-research")
async def start_research(data: dict):
    """Start a new research session (idempotent — safe to call multiple times)"""
    query = data.get("query")
    mode = data.get("mode", "quick")

    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    # Use provided session_id if given (from coordinator), else generate UUID
    session_id = data.get("session_id") or str(uuid.uuid4())

    # I-12 fix: Idempotent registration — if already registered, return existing session
    # without overwriting state or broadcasting another session_started event.
    if session_id in active_sessions:
        existing = active_sessions[session_id]
        logger.info(f"Session {session_id} already registered — returning existing (I-12 dedup)")
        return {"session_id": session_id, "status": "already_registered",
                "session": existing.to_dict()}

    session = ResearchSession(session_id, query, mode)
    active_sessions[session_id] = session

    # Broadcast update so all connected UIs pick up the new session_id (I-10 fix)
    await manager.broadcast({
        "type": "session_started",
        "session": session.to_dict()
    })

    logger.info(f"Started session {session_id}: {query} ({mode})")

    return {"session_id": session_id, "status": "started"}

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Get session status"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()

@app.post("/api/update/{session_id}")
async def update_session(session_id: str, data: dict):
    """Update session progress (called by research workflow)"""
    session = active_sessions.get(session_id)
    if not session:
        # Auto-create session when coordinator sends updates before /api/start-research
        query = data.get("query", "Unknown")
        mode = data.get("mode", "standard")
        session = ResearchSession(session_id, query, mode)
        active_sessions[session_id] = session
        logger.info(f"Auto-created session {session_id} from update")

    # Update session
    if "current_phase" in data:
        session.current_phase = data["current_phase"]
    if "progress" in data:
        session.progress = data["progress"]
    if "papers_found" in data:
        session.papers_found = data["papers_found"]
    if "pdfs_downloaded" in data:
        session.pdfs_downloaded = data["pdfs_downloaded"]
    if "status" in data:
        session.status = data["status"]
    if "log_message" in data:
        session.log_messages.append({
            "timestamp": datetime.now().isoformat(),
            "message": data["log_message"]
        })

    # Broadcast update
    await manager.broadcast({
        "type": "session_update",
        "session_id": session_id,
        "data": data
    })

    return {"status": "updated"}

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """Get session results"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load results from file
    results_file = Path(f"runs/{session_id}/research_results_{session_id}.json")
    if results_file.exists():
        return json.loads(results_file.read_text())
    else:
        return {"error": "Results not yet available"}

@app.get("/api/sessions/latest")
async def get_latest_session():
    """
    I-11 fix: Return the most recently started active session.
    Used by the UI on reconnect/reload to re-attach to a running session
    instead of showing 'Waiting for session...' forever.
    """
    if not active_sessions:
        return {"session": None}

    # Return the session with the most recent start_time
    latest = max(active_sessions.values(), key=lambda s: s.start_time)
    return {"session": latest.to_dict()}


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "sessions": [s.to_dict() for s in active_sessions.values()],
        "count": len(active_sessions)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live updates. On connect, sends current session state for reconnect (I-11)."""
    await manager.connect(websocket)
    try:
        # I-11 fix: Send current session state immediately on connect so a reloaded
        # UI can re-attach to the running session without waiting for the next update.
        if active_sessions:
            latest = max(active_sessions.values(), key=lambda s: s.start_time)
            await websocket.send_json({
                "type": "session_current",
                "session": latest.to_dict(),
                "log_messages": latest.log_messages[-50:]  # last 50 log entries
            })

        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "active_sessions": len(active_sessions),
        "websocket_connections": len(manager.active_connections)
    }

# ============================================
# Helper Functions
# ============================================

async def send_update(session_id: str, update_type: str, data: dict):
    """Send update to all connected clients"""
    await manager.broadcast({
        "type": update_type,
        "session_id": session_id,
        "data": data
    })

# ============================================
# Main
# ============================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Academic Agent Web UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Web UI Server on http://{args.host}:{args.port}")
    logger.info("Press Ctrl+C to stop")

    uvicorn.run(
        "src.web_ui.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
