"""Tests cover simulated endpoints only; no device actions."""

def test_ready_and_blocked(client):
    good = client.get('/api/provisioning/devices/MAC-001/readiness')
    assert good.status_code == 200
    assert good.json()['ready'] is True
    assert good.json()['real_device_changes'] == 0
    bad = client.get('/api/provisioning/devices/MAC-002/readiness')
    assert bad.status_code == 200
    assert bad.json()['ready'] is False
    assert [c['check'] for c in bad.json()['checks'] if not c['passed']] == [
        'disk_encryption', 'mdm_compliance', 'patch_currency']
    assert client.get('/api/provisioning/devices/DOES-NOT-EXIST/readiness').status_code == 404


def test_request_approval_idempotence(client):
    response = client.post('/api/provisioning/devices/WIN-001/request')
    assert response.status_code == 200
    proposal = response.json()['request']
    assert proposal['status'] == 'pending'
    duplicate = client.post('/api/provisioning/devices/WIN-001/request').json()
    assert duplicate['already_exists'] is True
    assert duplicate['request']['id'] == proposal['id']
    assert len(client.get('/api/provisioning/requests').json()) == 1
    url = f"/api/provisioning/requests/{proposal['id']}/approve"
    approved = client.post(url, json={'reviewer':'Demo Reviewer'}).json()
    assert approved['real_device_changes'] == 0
    assert approved['status'] == 'approved'
    assert client.post(url, json={'reviewer':'Demo Reviewer'}).json()['already_approved']
    assert client.get('/api/audit/events').json()[0]['action'] == 'SIMULATED_PROVISIONING_APPROVED'


def test_blocked_request_cannot_be_approved(client):
    record = client.post('/api/provisioning/devices/MAC-002/request').json()['request']
    assert record['status'] == 'blocked'
    result = client.post(f"/api/provisioning/requests/{record['id']}/approve",
                         json={'reviewer':'Demo Reviewer'})
    assert result.status_code == 409
    assert client.post('/api/provisioning/requests/missing/approve',json={'reviewer':'Demo Reviewer'}).status_code == 404
    assert client.post('/api/provisioning/devices/missing/request').status_code == 404
