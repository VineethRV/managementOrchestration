import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from model_agent import ModelAgent
from agents import AgentManagementHelper
from coordinator import GlobalCoordinator
from typing import Dict
from personality_config import AGENT_PERSONALITIES
from dotenv import load_dotenv
app = FastAPI(title='Bottom-up Groq Agent System')
global model
load_dotenv()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173','http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

model = None

@app.on_event('startup')
async def startup_event():
    global model
    load_dotenv()
    model = ModelAgent()#api_key_env=os.getenv("GROQ_API_KEY"))  

# simple websocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        to_remove = []
        for conn in list(self.active_connections):
            try:
                await conn.send_text(message)
            except Exception:
                to_remove.append(conn)
        for r in to_remove:
            self.disconnect(r)

manager = ConnectionManager()

@app.websocket('/ws/logs')
async def websocket_logs(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(ws)

@app.post('/api/run')
async def run_pipeline(payload: Dict):
    spec = payload.get('spec')
    if not spec:
        return JSONResponse({'error': 'spec required'}, status_code=400)
    # create model instance (safe to reuse)
    # Build subgoals
    subgoals = {
        'frontend': f'Build frontend for: {spec}',
        'backend': f'Build backend for: {spec}',
        'database': f'Build database for: {spec}'
    }
    role_results = {}
    # run each manager sequentially, send logs to websocket clients
    for role, goal in subgoals.items():
        await manager.broadcast(f'Starting role: {role}')
        agents_info = AGENT_PERSONALITIES[role]
        helper = AgentManagementHelper(role, agents_info, goal, model)
        merged = helper.run_once()
        role_results[role] = merged
        await manager.broadcast(f'Completed role: {role} (len={len(merged)})')
    await manager.broadcast('Integrating roles...')
    coordinator = GlobalCoordinator(model)
    integrated = coordinator.integrate(role_results)
    # write files to generated_project
    outdir = './data/generated_project'
    os.makedirs(outdir, exist_ok=True)
    for path, contents in (integrated.items() if isinstance(integrated, dict) else {'_raw': integrated} .items()):
        safe = os.path.join(outdir, path)
        folder = os.path.dirname(safe)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(safe, 'w', encoding='utf-8') as f:
            f.write(contents)
    # make zip
    zip_path = './data/generated_project.zip'
    import zipfile
    with zipfile.ZipFile(zip_path, 'w') as z:
        for root, _, files in os.walk(outdir):
            for fn in files:
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, outdir)
                z.write(full, arcname=arc)
    await manager.broadcast('Pipeline complete. ZIP ready.')
    metrics = None
    try:
        metrics = model.get_metrics()
    except Exception:
        metrics = {'conversation': 0, 'coding': 0}
    return {'status': 'done', 'zip': zip_path, 'metrics': metrics}


@app.get('/api/metrics')
def get_metrics():
    try:
        return {'metrics': model.get_metrics()}
    except Exception:
        return {'metrics': {'conversation': 0, 'coding': 0}}



