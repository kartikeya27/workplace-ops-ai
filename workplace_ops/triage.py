"""Rules first: reproducible ticket triage and explainable context."""
RULES = [
    ('identity', ('mfa', 'login', 'log in', 'sign in', 'authentication', 'password', 'okta', 'duo')),
    ('collaboration', ('zoom', 'teams', 'meeting', 'conference', 'calendar')),
    ('endpoint', ('patch', 'update', 'encryption', 'filevault', 'compliant', 'intune', 'jamf', 'device', 'mac', 'windows')),
]
KNOWLEDGE = {
    'identity': ('KB-ID-02', 'Check identity provider status, authentication logs and MFA registration. Do not reset accounts automatically.'),
    'collaboration': ('KB-COL-01', 'Verify meeting organizer, recurrence and link provider. Escalate changes to calendar owner.'),
    'endpoint': ('KB-MDM-03', 'Check source MDM, encryption, last patch state and device compliance before suggesting remediation.'),
    'general': ('KB-GEN-01', 'Request clarifying details, business impact and approval before making changes.'),
}


def classify(title, description):
    lower = (title + ' ' + description).lower()
    for team, terms in RULES:
        matches = [term for term in terms if term in lower]
        if matches:
            return team, 'Matched keywords: ' + ', '.join(matches[:4])
    return 'general', 'No scoped rule matched; human queue is required'


def recommendation(team, device):
    article_id, article = KNOWLEDGE[team]
    facts = []
    if device:
        facts = [f"MDM: {device['platform']}", f"Encrypted: {bool(device['encrypted'])}",
                 f"Compliant: {bool(device['compliant'])}", f"Patch: {device['patch_status']}"]
    return {'knowledge_id': article_id, 'guidance': article, 'device_facts': facts,
            'model_used': False, 'mode': 'deterministic_explainable_demo'}
