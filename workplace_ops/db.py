"""SQLite storage and seeded fictional data."""
import os
import sqlite3
from pathlib import Path
from .fixtures import DEVICES, TICKETS, ENGINEERS, MEETINGS


def db_path():
    return Path(os.environ.get('WORKPLACE_DB_PATH', 'artifacts/workplace_ops.db')).resolve()


def connect(path):
    conn = sqlite3.connect(str(path), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def initialize(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY, model TEXT NOT NULL, platform TEXT NOT NULL,
            os TEXT NOT NULL, owner TEXT NOT NULL, encrypted INTEGER NOT NULL,
            compliant INTEGER NOT NULL, patch_status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
            device_id TEXT REFERENCES devices(id), priority TEXT NOT NULL,
            assigned_to TEXT, status TEXT NOT NULL DEFAULT 'open'
        );
        CREATE TABLE IF NOT EXISTS engineers (
            name TEXT PRIMARY KEY, team TEXT NOT NULL, on_duty INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY, ticket_id TEXT NOT NULL UNIQUE REFERENCES tickets(id),
            team TEXT NOT NULL, owner TEXT, reason TEXT NOT NULL,
            advice TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL, reviewed_by TEXT, reviewed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
            actor TEXT NOT NULL, action TEXT NOT NULL, subject TEXT NOT NULL,
            detail TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY, subject TEXT NOT NULL, organizer TEXT NOT NULL,
            provider TEXT NOT NULL, recurring INTEGER NOT NULL,
            external_attendees INTEGER NOT NULL, user_migrated INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS provisioning_requests (
            id TEXT PRIMARY KEY, device_id TEXT NOT NULL UNIQUE REFERENCES devices(id),
            status TEXT NOT NULL CHECK(status IN ('pending', 'blocked', 'approved')),
            created_at TEXT NOT NULL, reviewed_by TEXT, reviewed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS evidence_runs (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, sha256 TEXT NOT NULL,
            snapshot_path TEXT NOT NULL, manifest_path TEXT NOT NULL
        );
        ''')
        if not conn.execute('SELECT 1 FROM devices LIMIT 1').fetchone():
            conn.executemany('INSERT INTO devices VALUES (?,?,?,?,?,?,?,?)', DEVICES)
        if not conn.execute('SELECT 1 FROM tickets LIMIT 1').fetchone():
            conn.executemany('INSERT INTO tickets(id,title,description,device_id,priority) VALUES (?,?,?,?,?)', TICKETS)
        if not conn.execute('SELECT 1 FROM engineers LIMIT 1').fetchone():
            conn.executemany('INSERT INTO engineers VALUES (?,?,?)', ENGINEERS)
        if not conn.execute('SELECT 1 FROM meetings LIMIT 1').fetchone():
            conn.executemany('INSERT INTO meetings VALUES (?,?,?,?,?,?,?)', MEETINGS)
