"""FastAPI application factory for a safe, local, fictional demonstration."""
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .db import db_path, initialize
from . import service, ai, onboarding

ROOT = Path(__file__).resolve().parent.parent

class Approval(BaseModel):
    reviewer: str = Field(min_length=2, max_length=80, pattern=r'^[a-zA-Z0-9 ._()-]+$')


class OnboardingCreate(BaseModel):
    employee_id: str = Field(pattern=r'^EMP-[0-9]{4}$', max_length=8)
    device_id: str = Field(min_length=3, max_length=30, pattern=r'^[A-Za-z0-9-]+$')
    profile: Literal['standard', 'engineering', 'support']


class PrivilegeDecision(BaseModel):
    reviewer: str = Field(min_length=2, max_length=80, pattern=r'^[a-zA-Z0-9 ._()-]+$')
    decision: Literal['approve', 'deny']

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

    @app.get('/api/ai/diagnostics')
    def ai_diagnostics():
        return ai.diagnostics()

    @app.get('/api/provisioning/requests')
    def provisioning_requests():
        return service.list_provisioning_requests(path)

    @app.get('/api/provisioning/devices/{device_id}/readiness')
    def provisioning_readiness(device_id: str):
        result = service.provisioning_readiness(path, device_id)
        if result is None:
            raise HTTPException(404, 'Device not found')
        return result

    @app.post('/api/provisioning/devices/{device_id}/request')
    def provisioning_request(device_id: str):
        result = service.propose_provisioning(path, device_id)
        if result is None:
            raise HTTPException(404, 'Device not found')
        return result

    @app.post('/api/provisioning/requests/{request_id}/approve')
    def provisioning_approve(request_id: str, body: Approval):
        try:
            result = service.approve_provisioning(path, request_id, body.reviewer)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if result is None:
            raise HTTPException(404, 'Provisioning request not found')
        return result

    @app.post('/api/onboarding')
    def create_onboarding(body: OnboardingCreate):
        try:
            result = onboarding.create_run(path, body.employee_id, body.device_id, body.profile)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if result is None:
            raise HTTPException(404, 'Device not found')
        return result

    @app.get('/api/onboarding')
    def onboarding_runs():
        return onboarding.list_runs(path)

    @app.get('/api/onboarding/{run_id}')
    def onboarding_detail(run_id: str):
        result = onboarding.get_run(path, run_id)
        if result is None:
            raise HTTPException(404, 'Onboarding run not found')
        return result

    @app.post('/api/onboarding/{run_id}/advance')
    def onboarding_advance(run_id: str):
        try:
            result = onboarding.advance(path, run_id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if result is None:
            raise HTTPException(404, 'Onboarding run not found')
        return result

    @app.post('/api/onboarding/{run_id}/privilege-decision')
    def onboarding_privilege_decision(run_id: str, body: PrivilegeDecision):
        try:
            result = onboarding.decide_privilege(path, run_id, body.reviewer, body.decision)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if result is None:
            raise HTTPException(404, 'Onboarding run not found')
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
