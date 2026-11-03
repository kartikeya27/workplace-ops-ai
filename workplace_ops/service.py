"""Domain workflows; all writes are to local synthetic SQLite data only."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .db import connect
from .triage import classify, recommendation


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def rows(conn, sql, params=()):
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def event(conn, actor, action, subject, detail):
    conn.execute('INSERT INTO events(occurred_at,actor,action,subject,detail) VALUES (?,?,?,?,?)',
                 (now(), actor, action, subject, detail))


def list_devices(path):
    with connect(path) as conn:
        return rows(conn, 'SELECT * FROM devices ORDER BY id')


def list_tickets(path):
    with connect(path) as conn:
        return rows(conn, 'SELECT * FROM tickets ORDER BY id')


def summary(path):
    with connect(path) as conn:
        devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
        noncompliant = conn.execute('SELECT COUNT(*) FROM devices WHERE compliant=0').fetchone()[0]
        open_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='open'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM proposals WHERE status='pending'").fetchone()[0]
        return {'devices': devices, 'noncompliant_devices': noncompliant,
                'open_tickets': open_tickets, 'pending_approvals': pending,
                'environment': 'FICTIONAL LOCAL DEMO — NO LIVE INTEGRATIONS'}


def propose_triage(path, ticket_id):
    with connect(path) as conn:
        ticket = conn.execute('SELECT * FROM tickets WHERE id=?', (ticket_id,)).fetchone()
        if not ticket:
            return None
        team, why = classify(ticket['title'], ticket['description'])
        device = (conn.execute('SELECT * FROM devices WHERE id=?', (ticket['device_id'],)).fetchone()
                  if ticket['device_id'] else None)
        owner = conn.execute('SELECT name FROM engineers WHERE team=? AND on_duty=1 ORDER BY name LIMIT 1',
                             (team,)).fetchone()
        suggested_owner = owner['name'] if owner else None
        explanation = recommendation(team, device)
        existing = conn.execute('SELECT * FROM proposals WHERE ticket_id=?', (ticket_id,)).fetchone()
        if existing:
            return {'proposal': dict(existing), 'explanation': explanation, 'already_exists': True}
        proposal_id = str(uuid.uuid4())
        full_reason = why + '; ' + ('on-duty team member found' if suggested_owner else 'fallback: no on-duty team member')
        conn.execute('''INSERT INTO proposals(id,ticket_id,team,owner,reason,advice,created_at)
                        VALUES (?,?,?,?,?,?,?)''',
                     (proposal_id, ticket_id, team, suggested_owner, full_reason, explanation['guidance'], now()))
        event(conn, 'system', 'TRIAGE_PROPOSED', ticket_id, f'{team} / {suggested_owner or "human queue"}')
        proposal = conn.execute('SELECT * FROM proposals WHERE id=?', (proposal_id,)).fetchone()
        return {'proposal': dict(proposal), 'explanation': explanation, 'already_exists': False}


def list_proposals(path):
    with connect(path) as conn:
        return rows(conn, 'SELECT * FROM proposals ORDER BY created_at DESC, ticket_id')


def approve(path, proposal_id, reviewer):
    with connect(path) as conn:
        proposal = conn.execute('SELECT * FROM proposals WHERE id=?', (proposal_id,)).fetchone()
        if not proposal:
            return None
        if proposal['status'] == 'approved':
            return {'proposal_id': proposal_id, 'status': 'approved', 'already_approved': True,
                    'assigned_to': proposal['owner']}
        if proposal['status'] != 'pending':
            raise ValueError('Proposal is not pending')
        if not proposal['owner']:
            raise ValueError('No on-duty owner; route manually rather than auto-assign')
        conn.execute('UPDATE tickets SET assigned_to=?,status=? WHERE id=?',
                     (proposal['owner'], 'assigned', proposal['ticket_id']))
        conn.execute('UPDATE proposals SET status=?,reviewed_by=?,reviewed_at=? WHERE id=?',
                     ('approved', reviewer, now(), proposal_id))
        event(conn, reviewer, 'SIMULATED_ASSIGNMENT_APPROVED', proposal['ticket_id'], proposal['owner'])
        return {'proposal_id': proposal_id, 'status': 'approved', 'already_approved': False,
                'assigned_to': proposal['owner']}


def patch_plan(path):
    with connect(path) as conn:
        affected = rows(conn, "SELECT id,platform,owner,patch_status FROM devices WHERE patch_status!='current' ORDER BY id")
    return {'dry_run': True, 'real_messages_sent': 0, 'affected_count': len(affected),
            'notifications': [{'device_id': d['id'], 'to': d['owner'],
                               'message': f"Action requested: {d['id']} needs an approved patch update. Contact IT for help.",
                               'source': d['platform']} for d in affected]}


def meeting_plan(path):
    with connect(path) as conn:
        meetings = rows(conn, 'SELECT * FROM meetings ORDER BY id')
    actions = []
    for meeting in meetings:
        if meeting['provider'] != 'teams' or meeting['user_migrated']:
            continue
        risk = 'high' if meeting['recurring'] or meeting['external_attendees'] else 'medium'
        actions.append({'meeting_id': meeting['id'], 'subject': meeting['subject'],
                        'organizer': meeting['organizer'], 'risk': risk,
                        'proposal': 'Owner-reviewed recreate/reinvite with Zoom; preserve original until verified',
                        'requires_owner_approval': True})
    return {'dry_run': True, 'real_calendar_changes': 0, 'affected_count': len(actions),
            'warning': 'Existing Microsoft Graph onlineMeetingProvider cannot be switched after activation. '
                       'This is a planning simulation, NOT a direct Teams-to-Zoom calendar conversion.',
            'actions': actions}


def create_evidence(path):
    path = Path(path)
    with connect(path) as conn:
        devices = rows(conn, 'SELECT id,platform,os,encrypted,compliant,patch_status FROM devices ORDER BY id')
    created = now()
    evidence_rows = [{**d, 'controls': {
        'ENCRYPTION': 'pass' if d['encrypted'] else 'fail',
        'MDM_COMPLIANCE': 'pass' if d['compliant'] else 'fail',
        'PATCH_CURRENCY': 'pass' if d['patch_status']=='current' else 'fail',
    }} for d in devices]
    snapshot = {'schema_version': 1, 'collection_time_utc': created,
                'collector': 'fictional_local_mdm_adapter', 'source': 'seeded_SQLite',
                'controls_are_examples_not_a_certification': True, 'devices': evidence_rows}
    payload = (json.dumps(snapshot, indent=2, sort_keys=True) + '\n').encode('utf-8')
    digest = hashlib.sha256(payload).hexdigest()
    run_id = str(uuid.uuid4())
    folder = path.parent / 'evidence' / run_id
    folder.mkdir(parents=True, exist_ok=False)
    snapshot_file = folder / 'snapshot.json'
    manifest_file = folder / 'manifest.json'
    snapshot_file.write_bytes(payload)
    manifest_file.write_text(json.dumps({'run_id': run_id, 'created_at': created,
                                         'snapshot_file': 'snapshot.json', 'sha256': digest,
                                         'algorithm': 'sha256'}, indent=2) + '\n', encoding='utf-8')
    with connect(path) as conn:
        conn.execute('INSERT INTO evidence_runs VALUES (?,?,?,?,?)',
                     (run_id, created, digest, str(snapshot_file), str(manifest_file)))
        event(conn, 'system', 'EVIDENCE_COLLECTED', run_id, f'{len(devices)} fictional device records')
    return {'run_id': run_id, 'created_at': created, 'sha256': digest,
            'device_count': len(devices), 'stored_under': str(folder),
            'immutable_storage': False, 'verified': True}


def verify_evidence(path, run_id):
    with connect(path) as conn:
        record = conn.execute('SELECT * FROM evidence_runs WHERE id=?', (run_id,)).fetchone()
    if not record:
        return None
    file = Path(record['snapshot_path'])
    manifest_path = Path(record['manifest_path'])
    if not file.exists() or not manifest_path.exists():
        return {'run_id': run_id, 'verified': False, 'reason': 'missing file'}
    actual = hashlib.sha256(file.read_bytes()).hexdigest()
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest_ok = manifest['run_id'] == run_id and manifest['sha256'] == record['sha256']
    except (ValueError, KeyError, TypeError):
        manifest_ok = False
    success = actual == record['sha256'] and manifest_ok
    return {'run_id': run_id, 'verified': success, 'expected_sha256': record['sha256'],
            'actual_sha256': actual, 'manifest_consistent': manifest_ok,
            'note': 'A hash detects local modification; this demo does not offer immutable/WORM storage or signatures.'}


def list_events(path):
    with connect(path) as conn:
        return rows(conn, 'SELECT * FROM events ORDER BY id DESC LIMIT 40')


def provisioning_readiness(path, device_id):
    """Read-only, fictional enrollment readiness; never enrolls a real laptop."""
    with connect(path) as conn:
        device = conn.execute('SELECT * FROM devices WHERE id=?', (device_id,)).fetchone()
    if device is None:
        return None
    checks = [
        {'check': 'device_in_local_inventory', 'passed': True,
         'explanation': 'Fictional device record exists; not proof of actual enrollment'},
        {'check': 'disk_encryption', 'passed': bool(device['encrypted']),
         'explanation': 'Illustrative FileVault/BitLocker state from local fixture'},
        {'check': 'mdm_compliance', 'passed': bool(device['compliant']),
         'explanation': 'Simulated MDM compliance flag'},
        {'check': 'patch_currency', 'passed': device['patch_status'] == 'current',
         'explanation': 'Simulated last-patch status'},
    ]
    return {'device_id': device['id'], 'platform': device['platform'],
            'model': device['model'], 'ready': all(c['passed'] for c in checks),
            'checks': checks, 'dry_run': True, 'real_device_changes': 0,
            'note': 'Readiness simulation only: no hardware imaging, enrollment, or privileges changed.'}


def list_provisioning_requests(path):
    with connect(path) as conn:
        return rows(conn, 'SELECT * FROM provisioning_requests ORDER BY created_at DESC, device_id')


def propose_provisioning(path, device_id):
    readiness = provisioning_readiness(path, device_id)
    if readiness is None:
        return None
    with connect(path) as conn:
        existing = conn.execute('SELECT * FROM provisioning_requests WHERE device_id=?', (device_id,)).fetchone()
        if existing:
            return {'request': dict(existing), 'readiness': readiness, 'already_exists': True}
        request_id = str(uuid.uuid4())
        status = 'pending' if readiness['ready'] else 'blocked'
        # A unique constraint plus INSERT OR IGNORE also prevents duplicate requests
        # if two workers evaluate the same fictional device concurrently.
        inserted = conn.execute("""INSERT OR IGNORE INTO provisioning_requests
                    (id,device_id,status,created_at) VALUES (?,?,?,?)""",
                    (request_id, device_id, status, now())).rowcount
        record = conn.execute('SELECT * FROM provisioning_requests WHERE device_id=?', (device_id,)).fetchone()
        if inserted:
            event(conn, 'system', 'PROVISIONING_REVIEW_CREATED', device_id, status)
        return {'request': dict(record), 'readiness': readiness, 'already_exists': not bool(inserted)}


def approve_provisioning(path, request_id, reviewer):
    """Approve only a local simulated readiness record; never changes a device."""
    with connect(path) as conn:
        record = conn.execute('SELECT * FROM provisioning_requests WHERE id=?', (request_id,)).fetchone()
        if record is None:
            return None
        if record['status'] == 'approved':
            return {'request_id': request_id, 'status': 'approved', 'already_approved': True,
                    'real_device_changes': 0}
        if record['status'] != 'pending':
            raise ValueError('Readiness checks failed; blocked device cannot be approved')
        latest = provisioning_readiness(path, record['device_id'])
        if not latest or not latest['ready']:
            raise ValueError('Device is no longer ready; re-evaluate before approval')
        changed = conn.execute("""UPDATE provisioning_requests
             SET status='approved',reviewed_by=?,reviewed_at=?
             WHERE id=? AND status='pending' """, (reviewer, now(), request_id)).rowcount
        if changed:
            event(conn, reviewer, 'SIMULATED_PROVISIONING_APPROVED', record['device_id'], request_id)
        return {'request_id': request_id, 'status': 'approved',
                'already_approved': not bool(changed), 'real_device_changes': 0}
