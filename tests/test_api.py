def test_home_health_and_seed(client):
    assert client.get('/').status_code == 200
    assert client.get('/api/health').json()['external_writes_enabled'] is False
    assert client.get('/api/summary').json()['devices'] == 5
    assert len(client.get('/api/tickets').json()) == 5
    assert len(client.get('/api/devices').json()) == 5
    assert client.get('/docs').status_code == 200


def test_ticket_triage_approval_and_idempotence(client):
    first = client.post('/api/tickets/T-1001/triage')
    assert first.status_code == 200
    data = first.json()
    assert data['proposal']['team'] == 'endpoint'
    assert data['proposal']['owner'] == 'Morgan (on duty)'
    assert data['explanation']['model_used'] is False
    assert any('Encrypted: False' in x for x in data['explanation']['device_facts'])
    assert len(client.get('/api/proposals').json()) == 1
    again = client.post('/api/tickets/T-1001/triage').json()
    assert again['already_exists'] is True
    assert again['proposal']['id'] == data['proposal']['id']
    proposal_id = data['proposal']['id']
    approved = client.post(f'/api/proposals/{proposal_id}/approve', json={'reviewer':'Demo Reviewer'}).json()
    assert approved['status'] == 'approved'
    assert client.post(f'/api/proposals/{proposal_id}/approve', json={'reviewer':'Demo Reviewer'}).json()['already_approved']
    ticket = next(t for t in client.get('/api/tickets').json() if t['id'] == 'T-1001')
    assert ticket['assigned_to'] == 'Morgan (on duty)'
    events = client.get('/api/audit/events').json()
    assert [e['action'] for e in events] == ['SIMULATED_ASSIGNMENT_APPROVED', 'TRIAGE_PROPOSED']


def test_ticket_not_found_and_bad_reviewer(client):
    assert client.post('/api/tickets/T-UNKNOWN/triage').status_code == 404
    p = client.post('/api/tickets/T-1002/triage').json()['proposal']['id']
    assert client.post(f'/api/proposals/{p}/approve', json={'reviewer':'<script>'}).status_code == 422
    assert client.post('/api/proposals/invalid-id/approve', json={'reviewer':'Reviewer'}).status_code == 404


def test_deterministic_agent_handoff_is_explicit(client):
    response = client.post('/api/tickets/T-1001/ai-summary')
    assert response.status_code == 200
    result = response.json()
    assert result['model_used'] is False
    assert result['needs_human_review'] is True
    assert 'read_local_mdm_fixture' in result['trace']
    assert client.get('/api/ai/config').json()['approval_required']
    assert client.post('/api/tickets/T-NONEXISTENT/ai-summary').status_code == 404
