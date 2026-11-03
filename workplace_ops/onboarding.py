"""Local-only, deterministic Mac/Windows employee onboarding state machine.

No MDM, IAM, app installer, or privilege system integrations. All mutations are
limited to fictional records in SQLite. Reviewer labels are not authentication.
"""
import json
import uuid
from datetime import datetime, timedelta, timezone

from .db import connect
from .service import event, now, provisioning_readiness

APPLICATIONS = {
    'mac': ('Zoom', 'Browser', 'Security Agent', 'VPN Client'),
    'windows': ('Zoom', 'Browser', 'Security Agent', 'VPN Client'),
}
EXTRA_APPS = {
    'standard': (),
    'engineering': ('VS Code', 'Git', 'Docker Desktop'),
    'support': ('Remote Support Console', 'Endpoint Diagnostics'),
}
ELEVATED_PROFILES = {'engineering', 'support'}
PRIVILEGE_TTL_MINUTES = 30


def _audit(conn, run_id, actor, action, details):
    detail = json.dumps(details, sort_keys=True)
    conn.execute('''INSERT INTO onboarding_events(run_id,occurred_at,actor,action,detail)
                    VALUES (?,?,?,?,?)''', (run_id, now(), actor, action, detail))
    event(conn, actor, 'ONBOARDING_' + action, run_id, detail)


def _device(conn, device_id):
    return conn.execute('SELECT * FROM devices WHERE id=?', (device_id,)).fetchone()


def _get(conn, run_id):
    return conn.execute('SELECT * FROM onboarding_runs WHERE id=?', (run_id,)).fetchone()


def _serialize(conn, record):
    result = dict(record)
    result['identity_plan'] = json.loads(result.pop('identity_json') or 'null')
    result['application_plan'] = json.loads(result.pop('applications_json') or 'null')
    result['privilege_request'] = json.loads(result.pop('privilege_json') or 'null')
    result['timeline'] = [
        {'time': row['occurred_at'], 'actor': row['actor'], 'action': row['action'],
         'details': json.loads(row['detail'])}
        for row in conn.execute('''SELECT occurred_at,actor,action,detail
                                   FROM onboarding_events WHERE run_id=? ORDER BY id''', (record['id'],))
    ]
    expires = result.get('privilege_expires_at')
    result['simulated_privilege_currently_valid'] = bool(
        result['privilege_decision'] == 'approved' and expires
        and datetime.fromisoformat(expires) > datetime.now(timezone.utc)
    )
    result['dry_run'] = True
    result['external_writes'] = 0
    return result


def list_runs(path):
    with connect(path) as conn:
        runs = conn.execute('SELECT * FROM onboarding_runs ORDER BY created_at DESC, id').fetchall()
        return [_serialize(conn, run) for run in runs]


def get_run(path, run_id):
    with connect(path) as conn:
        run = _get(conn, run_id)
        return _serialize(conn, run) if run else None


def create_run(path, employee_id, device_id, profile):
    """A device and employee can each participate in one fictional local run."""
    with connect(path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        if _device(conn, device_id) is None:
            return None
        previous = conn.execute('''SELECT * FROM onboarding_runs
                    WHERE employee_id=? OR device_id=?''', (employee_id, device_id)).fetchone()
        if previous:
            if (previous['employee_id'], previous['device_id'], previous['profile']) != (employee_id, device_id, profile):
                raise ValueError('Employee or device is already assigned to a different onboarding run')
            return {'run': _serialize(conn, previous), 'already_exists': True}
        run_id = str(uuid.uuid4())
        created = now()
        conn.execute('''INSERT INTO onboarding_runs
            (id,employee_id,device_id,profile,status,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?)''',
            (run_id, employee_id, device_id, profile, 'created', created, created))
        _audit(conn, run_id, 'system', 'CREATED',
               {'employee_id': employee_id, 'device_id': device_id, 'profile': profile})
        return {'run': _serialize(conn, _get(conn, run_id)), 'already_exists': False}


def _set(conn, run_id, status, **fields):
    allowed = {'identity_json', 'applications_json', 'privilege_json', 'privilege_decision',
               'privilege_expires_at'}
    if set(fields) - allowed:
        raise ValueError('Unsupported update field')
    changes = {'status': status, 'updated_at': now(), **fields}
    clauses = ', '.join(f'{key}=?' for key in changes)
    conn.execute(f'UPDATE onboarding_runs SET {clauses} WHERE id=?', (*changes.values(), run_id))


def advance(path, run_id):
    """Execute exactly one local simulation step per call. Never skip approval."""
    with connect(path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        record = _get(conn, run_id)
        if record is None:
            return None
        stage = record['status']
        if stage in ('blocked', 'awaiting_privilege_approval'):
            raise ValueError('Workflow is blocked or awaiting explicit privilege approval')
        if stage in ('completed', 'completed_limited'):
            return {'run': _serialize(conn, record), 'already_complete': True}
        ready = provisioning_readiness(path, record['device_id'])
        if not ready or not ready['ready']:
            _set(conn, run_id, 'blocked')
            _audit(conn, run_id, 'system', 'READINESS_BLOCKED',
                   {'failed_checks': [c['check'] for c in ready['checks'] if not c['passed']] if ready else ['missing_device']})
        elif stage == 'created':
            _set(conn, run_id, 'readiness_verified')
            _audit(conn, run_id, 'system', 'READINESS_VERIFIED',
                   {'passed_checks': [c['check'] for c in ready['checks']]})
        elif stage == 'readiness_verified':
            identity_plan = {
                'provider': 'simulated_enterprise_idp',
                'user_principal': record['employee_id'].lower() + '@example.invalid',
                'groups': ['all-employees', f"profile-{record['profile']}"],
                'mfa_required': True, 'state': 'simulated_provisioned',
                'real_accounts_created': 0,
            }
            _set(conn, run_id, 'identity_simulated', identity_json=json.dumps(identity_plan))
            _audit(conn, run_id, 'system', 'IDENTITY_SIMULATED',
                   {'groups': identity_plan['groups'], 'mfa_required': True})
        elif stage == 'identity_simulated':
            device = _device(conn, record['device_id'])
            platform = 'mac' if 'jamf' in device['platform'].lower() or device['id'].upper().startswith('MAC') else 'windows'
            apps = list(APPLICATIONS[platform]) + list(EXTRA_APPS[record['profile']])
            plan = {'platform': platform, 'apps': [{'name': a, 'state': 'planned'} for a in apps],
                    'execution': 'dry_run', 'real_installations': 0}
            _set(conn, run_id, 'apps_planned', applications_json=json.dumps(plan))
            _audit(conn, run_id, 'system', 'APPLICATIONS_PLANNED', {'apps': apps, 'platform': platform})
        elif stage == 'apps_planned':
            plan = json.loads(record['applications_json'])
            plan['apps'] = [{**app, 'state': 'simulated_installed'} for app in plan['apps']]
            plan['execution'] = 'simulated_only'
            _set(conn, run_id, 'apps_simulated', applications_json=json.dumps(plan))
            _audit(conn, run_id, 'system', 'APPLICATIONS_SIMULATED',
                   {'app_count': len(plan['apps']), 'real_installations': 0})
        elif stage == 'apps_simulated':
            if record['profile'] in ELEVATED_PROFILES:
                privilege = {'scope': 'approved_tool_installation',
                             'requested_minutes': PRIVILEGE_TTL_MINUTES,
                             'state': 'awaiting_manual_approval', 'actual_privilege_grants': 0}
                _set(conn, run_id, 'awaiting_privilege_approval', privilege_json=json.dumps(privilege))
                _audit(conn, run_id, 'system', 'PRIVILEGE_REVIEW_REQUIRED',
                       {'scope': privilege['scope'], 'requested_minutes': PRIVILEGE_TTL_MINUTES})
            else:
                _set(conn, run_id, 'completed')
                _audit(conn, run_id, 'system', 'COMPLETED',
                       {'privilege': 'not_requested', 'real_external_writes': 0})
        else:
            raise ValueError('Unexpected onboarding state')
        return {'run': _serialize(conn, _get(conn, run_id)), 'already_complete': False}


def decide_privilege(path, run_id, reviewer, decision):
    """Approval is explicit and simulated. A label is NOT verified authorization."""
    with connect(path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        record = _get(conn, run_id)
        if record is None:
            return None
        existing = record['privilege_decision']
        if existing:
            if existing != ('approved' if decision == 'approve' else 'denied'):
                raise ValueError('Privilege decision is final; conflicting retry rejected')
            return {'run': _serialize(conn, record), 'already_decided': True}
        if record['status'] != 'awaiting_privilege_approval':
            raise ValueError('No pending privilege request; complete preceding workflow stages first')
        privilege = json.loads(record['privilege_json'])
        approved = decision == 'approve'
        privilege['state'] = 'simulated_approved' if approved else 'denied'
        privilege['reviewed_by'] = reviewer
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=PRIVILEGE_TTL_MINUTES)).isoformat(timespec='seconds') if approved else None
        _set(conn, run_id, 'completed' if approved else 'completed_limited',
             privilege_json=json.dumps(privilege),
             privilege_decision='approved' if approved else 'denied',
             privilege_expires_at=expiry)
        _audit(conn, run_id, reviewer, 'PRIVILEGE_APPROVED' if approved else 'PRIVILEGE_DENIED',
               {'scope': privilege['scope'], 'expires_at': expiry, 'real_privileges_granted': 0})
        _audit(conn, run_id, 'system', 'COMPLETED',
               {'privilege': 'simulated_approved' if approved else 'denied', 'real_external_writes': 0})
        return {'run': _serialize(conn, _get(conn, run_id)), 'already_decided': False}
