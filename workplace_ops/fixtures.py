"""Fictional seed records — no organization or person data."""
DEVICES = [
    ('MAC-001', 'MacBook Pro', 'jamf', 'macOS 15', 'morgan@example.test', 1, 1, 'current'),
    ('MAC-002', 'MacBook Air', 'jamf', 'macOS 14', 'blair@example.test', 0, 0, 'overdue'),
    ('WIN-001', 'ThinkPad T14', 'intune', 'Windows 11', 'alex@example.test', 1, 1, 'current'),
    ('WIN-002', 'Surface Laptop', 'intune', 'Windows 11', 'dana@example.test', 1, 0, 'overdue'),
    ('MAC-003', 'Mac mini', 'jamf', 'macOS 15', 'sam@example.test', 1, 1, 'current'),
]
TICKETS = [
    ('T-1001', 'Mac encryption is disabled', 'Escalated from helpdesk after FileVault check.', 'MAC-002', 'high'),
    ('T-1002', 'Windows device missing security patches', 'Update deployment failed and device is not compliant.', 'WIN-002', 'high'),
    ('T-1003', 'Unable to complete MFA enrollment', 'Employee cannot sign in after authentication change.', 'WIN-001', 'medium'),
    ('T-1004', 'Conference meeting invite no longer works', 'Teams link from recurring meeting is obsolete after Zoom migration.', 'MAC-001', 'medium'),
    ('T-1005', 'Request for a new software tool', 'Employee requests access to diagramming software.', 'MAC-003', 'low'),
]
ENGINEERS = [
    ('Morgan (on duty)', 'endpoint', 1),
    ('Alex (on duty)', 'identity', 1),
    ('Sam (on duty)', 'collaboration', 1),
]
MEETINGS = [
    ('M-100', 'Weekly operations sync', 'morgan@example.test', 'teams', 1, 0, 1),
    ('M-101', 'External customer check-in', 'dana@example.test', 'teams', 1, 1, 0),
    ('M-102', 'Monthly finance review', 'alex@example.test', 'teams', 1, 0, 0),
    ('M-103', 'Product walkthrough', 'sam@example.test', 'zoom', 0, 1, 1),
]
