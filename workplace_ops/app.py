"""FastAPI application factory for a safe, local, fictional demonstration."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .db import db_path, initialize
from . import service, ai

ROOT = Path(__file__).resolve().parent.parent

class Approval(BaseModel):
    reviewer: str = Field(min_length=2, max_length=80, pattern=r'^[a-zA-Z0-9 ._()-]+$')


def create_app(database_path=None):
    path = Path(database_path).resolve() if database_path else db_path()
    initialize(path)
    app = FastAPI(title='WorkplaceOps AI (fictional local demo)', version='0.1.0',
                  description='No real MDM, identity, email or calendar access. All data and actions are simulated.')
    app.mount('/static', StaticFiles(directory=ROOT/'web'), name='static')

    @app.get('/', include_in_schema=False)
    def home():
        return FileResponse(ROOT/'web'/'index.html')

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'mode': 'fictional-local-only', 'external_writes_enabled': False}

    @app.get('/api/ai/config')
    def ai_config():
        return {'mode': ai.mode(), 'external_model_api_used': False, 'approval_required': True}

    @app.post('/api/tickets/{ticket_id}/ai-summary')
    def ai_summary(ticket_id: str):
        try:
            result = ai.summarize(path, ticket_id)
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        if result is None:
            raise HTTPException(404, 'Ticket not found')
        return result

    @app.get('/api/summary')
    def summary():
        return service.summary(path)

    @app.get('/api/devices')
    def devices():
        return service.list_devices(path)

    @app.get('/api/tickets')
    def tickets():
        return service.list_tickets(path)

    @app.post('/api/tickets/{ticket_id}/triage')
    def triage(ticket_id: str):
        result = service.propose_triage(path, ticket_id)
        if result is None:
            raise HTTPException(404, 'Ticket not found')
        return result

    @app.get('/api/proposals')
    def proposals():
        return service.list_proposals(path)

    @app.post('/api/proposals/{proposal_id}/approve')
    def approve(proposal_id: str, body: Approval):
        try:
            result = service.approve(path, proposal_id, body.reviewer)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if result is None:
            raise HTTPException(404, 'Proposal not found')
        return result

    @app.get('/api/patches/plan')
    def patch_plan():
        return service.patch_plan(path)

    @app.get('/api/meetings/plan')
    def meeting_plan():
        return service.meeting_plan(path)

    @app.post('/api/evidence/runs')
    def evidence():
        return service.create_evidence(path)

    @app.get('/api/evidence/runs/{run_id}/verify')
    def verify(run_id: str):
        result = service.verify_evidence(path, run_id)
        if result is None:
            raise HTTPException(404, 'Evidence run not found')
        return result

    @app.get('/api/audit/events')
    def events():
        return service.list_events(path)

    return app

app = create_app()
