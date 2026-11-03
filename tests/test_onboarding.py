"""Complete fake-employee lifecycle; never reaches an external system."""


def create(client, employee='EMP-1001', device='MAC-001', profile='engineering'):
    return client.post('/api/onboarding', json={
        'employee_id': employee, 'device_id': device, 'profile': profile})


def advance(client, run_id):
    return client.post(f'/api/onboarding/{run_id}/advance')


def test_mac_engineering_happy_path_and_idempotence(client):
    first = create(client)
    assert first.status_code == 200
    run = first.json()['run']
    run_id = run['id']
    assert run['status'] == 'created'
    assert run['external_writes'] == 0
    again = create(client).json()
    assert again['already_exists'] is True
    assert again['run']['id'] == run_id
    assert len(client.get('/api/onboarding').json()) == 1
    stages = ['readiness_verified', 'identity_simulated', 'apps_planned',
              'apps_simulated', 'awaiting_privilege_approval']
    for status in stages:
        response = advance(client, run_id)
        assert response.status_code == 200
        assert response.json()['run']['status'] == status
    record = response.json()['run']
    assert record['identity_plan']['mfa_required'] is True
    assert 'profile-engineering' in record['identity_plan']['groups']
    assert record['identity_plan']['real_accounts_created'] == 0
    assert any(app['name'] == 'Docker Desktop' and app['state'] == 'simulated_installed'
               for app in record['application_plan']['apps'])
    assert record['application_plan']['real_installations'] == 0
    assert record['privilege_request']['requested_minutes'] == 30
    assert advance(client, run_id).status_code == 409
    decide = f'/api/onboarding/{run_id}/privilege-decision'
    accepted = client.post(decide, json={'reviewer': 'Demo Reviewer', 'decision': 'approve'})
    assert accepted.status_code == 200
    final = accepted.json()['run']
    assert final['status'] == 'completed'
    assert final['privilege_decision'] == 'approved'
    assert final['simulated_privilege_currently_valid'] is True
    assert final['privilege_request']['actual_privilege_grants'] == 0
    assert final['external_writes'] == 0
    assert advance(client, run_id).json()['already_complete'] is True
    assert client.post(decide, json={'reviewer': 'Demo Reviewer', 'decision': 'approve'}).json()['already_decided']
    assert client.post(decide, json={'reviewer': 'Demo Reviewer', 'decision': 'deny'}).status_code == 409
    assert len(final['timeline']) == 8
    assert client.get(f'/api/onboarding/{run_id}').json()['timeline'][-1]['action'] == 'COMPLETED'
    assert any(e['action'] == 'ONBOARDING_PRIVILEGE_APPROVED' for e in client.get('/api/audit/events').json())


def test_standard_windows_does_not_request_privilege(client):
    record = create(client, 'EMP-1002', 'WIN-001', 'standard').json()['run']
    for _ in range(5):
        record = advance(client, record['id']).json()['run']
    assert record['status'] == 'completed'
    assert record['privilege_request'] is None
    assert record['privilege_decision'] is None
    assert record['application_plan']['platform'] == 'windows'
    assert all(app['name'] != 'Docker Desktop' for app in record['application_plan']['apps'])
    assert any(event['action'] == 'COMPLETED' for event in record['timeline'])
    assert client.post(f"/api/onboarding/{record['id']}/privilege-decision",
                       json={'reviewer': 'Demo Reviewer', 'decision': 'approve'}).status_code == 409


def test_blocked_device_stops_before_identity(client):
    record = create(client, 'EMP-1003', 'MAC-002', 'engineering').json()['run']
    result = advance(client, record['id']).json()['run']
    assert result['status'] == 'blocked'
    assert result['identity_plan'] is None
    assert result['application_plan'] is None
    assert result['timeline'][-1]['details']['failed_checks'] == [
        'disk_encryption', 'mdm_compliance', 'patch_currency']
    assert advance(client, record['id']).status_code == 409


def test_denied_privilege_completes_with_limited_access(client):
    record = create(client, 'EMP-1004', 'MAC-003', 'support').json()['run']
    for _ in range(5):
        record = advance(client, record['id']).json()['run']
    result = client.post(f"/api/onboarding/{record['id']}/privilege-decision",
                         json={'reviewer': 'Support Lead', 'decision': 'deny'}).json()['run']
    assert result['status'] == 'completed_limited'
    assert result['privilege_decision'] == 'denied'
    assert result['simulated_privilege_currently_valid'] is False
    assert result['privilege_expires_at'] is None


def test_bad_inputs_conflicts_and_missing(client):
    assert create(client, 'PERSON-A').status_code == 422
    assert create(client, 'EMP-1010', 'MISSING').status_code == 404
    assert client.post('/api/onboarding', json={
        'employee_id': 'EMP-1011', 'device_id': 'MAC-001', 'profile': 'root'}).status_code == 422
    record = create(client).json()['run']
    assert create(client, 'EMP-1020', 'MAC-001').status_code == 409
    assert create(client, 'EMP-1001', 'WIN-001').status_code == 409
    assert create(client, 'EMP-1001', 'MAC-001', 'standard').status_code == 409
    assert client.get('/api/onboarding/missing').status_code == 404
    assert advance(client, 'missing').status_code == 404
    assert client.post('/api/onboarding/missing/privilege-decision', json={
        'reviewer': 'Reviewer', 'decision': 'approve'}).status_code == 404
    assert client.post(f"/api/onboarding/{record['id']}/privilege-decision", json={
        'reviewer': '<script>', 'decision': 'approve'}).status_code == 422
    assert client.post(f"/api/onboarding/{record['id']}/privilege-decision", json={
        'reviewer': 'Reviewer', 'decision': 'approve'}).status_code == 409


def test_readiness_rechecked_before_identity_step(client, app_and_db):
    from workplace_ops.db import connect
    _, db = app_and_db
    record = create(client).json()['run']
    advance(client, record['id'])
    with connect(db) as conn:
        conn.execute("UPDATE devices SET compliant=0 WHERE id='MAC-001'")
    result = advance(client, record['id']).json()['run']
    assert result['status'] == 'blocked'
    assert result['identity_plan'] is None


def test_completed_approval_expiry_is_derived_from_timestamp(client, app_and_db):
    from workplace_ops.db import connect
    _, db = app_and_db
    record = create(client).json()['run']
    for _ in range(5):
        advance(client, record['id'])
    client.post(f"/api/onboarding/{record['id']}/privilege-decision", json={
        'reviewer': 'Demo Reviewer', 'decision': 'approve'})
    with connect(db) as conn:
        conn.execute("UPDATE onboarding_runs SET privilege_expires_at='2020-01-01T00:00:00+00:00' WHERE id=?",
                     (record['id'],))
    detail = client.get(f"/api/onboarding/{record['id']}").json()
    assert detail['simulated_privilege_currently_valid'] is False
