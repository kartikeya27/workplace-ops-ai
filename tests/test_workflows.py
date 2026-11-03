import json
from workplace_ops.db import connect
from workplace_ops.service import verify_evidence


def test_routing_identity_collaboration_and_fallback(client, app_and_db):
    assert client.post('/api/tickets/T-1003/triage').json()['proposal']['team'] == 'identity'
    assert client.post('/api/tickets/T-1004/triage').json()['proposal']['team'] == 'collaboration'
    general = client.post('/api/tickets/T-1005/triage').json()['proposal']
    assert general['team'] == 'general'
    assert general['owner'] is None
    assert client.post(f"/api/proposals/{general['id']}/approve", json={'reviewer':'Reviewer'}).status_code == 409


def test_patch_plan_is_targeted_and_sends_nothing(client):
    plan = client.get('/api/patches/plan').json()
    assert plan['affected_count'] == 2
    assert plan['real_messages_sent'] == 0
    assert {n['device_id'] for n in plan['notifications']} == {'MAC-002', 'WIN-002'}


def test_meeting_plan_is_safe_and_not_a_false_provider_switch(client):
    plan = client.get('/api/meetings/plan').json()
    assert plan['dry_run'] is True
    assert plan['real_calendar_changes'] == 0
    assert plan['affected_count'] == 2
    assert 'cannot be switched' in plan['warning']
    assert all(item['requires_owner_approval'] for item in plan['actions'])


def test_evidence_hash_passes_then_detects_mutation(client, app_and_db):
    _, db = app_and_db
    response = client.post('/api/evidence/runs')
    assert response.status_code == 200
    run = response.json()
    assert run['device_count'] == 5
    assert client.get(f"/api/evidence/runs/{run['run_id']}/verify").json()['verified'] is True
    with connect(db) as conn:
        file = conn.execute('SELECT snapshot_path FROM evidence_runs WHERE id=?', (run['run_id'],)).fetchone()[0]
    with open(file, 'a', encoding='utf-8') as handle:
        handle.write('\nTAMPERED')
    assert verify_evidence(db, run['run_id'])['verified'] is False
    assert client.get('/api/evidence/runs/nonexistent/verify').status_code == 404


def test_read_only_planning_does_not_add_audit_events(client):
    client.get('/api/patches/plan')
    client.get('/api/meetings/plan')
    assert client.get('/api/audit/events').json() == []
