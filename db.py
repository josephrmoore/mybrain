import sqlite3
import json
import os
import shutil
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "core.db")
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
MAX_BACKUPS = 10

VALID_STAGES = ["thought", "idea", "concept", "project", "product", "record"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_migrations():
    """Applies any .sql files in migrations/ not yet recorded in schema_migrations, in filename order."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    applied = {row["filename"] for row in conn.execute("SELECT filename FROM schema_migrations")}

    if os.path.isdir(MIGRATIONS_DIR):
        migration_files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
        for filename in migration_files:
            if filename in applied:
                continue
            path = os.path.join(MIGRATIONS_DIR, filename)
            with open(path, "r") as f:
                sql = f.read()
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)",
                (filename, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            print(f"Applied migration: {filename}")

    conn.close()


def backup_on_launch():
    """Copies the DB file (if it exists) into backups/ with a timestamped name, then prunes to the last MAX_BACKUPS."""
    if not os.path.exists(DB_PATH):
        return  # nothing to back up on a fresh install

    os.makedirs(BACKUPS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(BACKUPS_DIR, f"core-{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)

    backups = sorted(
        f for f in os.listdir(BACKUPS_DIR) if f.startswith("core-") and f.endswith(".db")
    )
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        os.remove(os.path.join(BACKUPS_DIR, oldest))


def _generate_id(conn):
    """Timestamp-based ID; on same-second collision, appends -01, -02, etc. until unique."""
    base_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = base_id
    suffix = 1
    while conn.execute("SELECT 1 FROM entries WHERE id = ?", (candidate,)).fetchone():
        candidate = f"{base_id}-{suffix:02d}"
        suffix += 1
    return candidate


def create_entry(silo, raw_text, taxonomy_stage, tags=None, metadata=None):
    if taxonomy_stage not in VALID_STAGES:
        raise ValueError(f"Invalid taxonomy_stage: {taxonomy_stage!r}. Must be one of {VALID_STAGES}")

    tags = [t.strip().lower() for t in (tags or [])]
    metadata = metadata or {}

    conn = get_connection()
    try:
        entry_id = _generate_id(conn)
        created_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO entries
                (id, created_at, silo, raw_text, taxonomy_stage, tags, related_ids, is_deleted, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (entry_id, created_at, silo, raw_text, taxonomy_stage, json.dumps(tags), json.dumps([]), json.dumps(metadata)),
        )
        conn.commit()
        return entry_id
    finally:
        conn.close()


def get_entry(entry_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        entry = dict(row)
        entry["tags"] = json.loads(entry["tags"])
        entry["related_ids"] = json.loads(entry["related_ids"])
        entry["metadata"] = json.loads(entry["metadata"])
        entry["is_deleted"] = bool(entry["is_deleted"])
        return entry
    finally:
        conn.close()


def soft_delete_entry(entry_id):
    conn = get_connection()
    try:
        conn.execute("UPDATE entries SET is_deleted = 1 WHERE id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()


def link_entries(id_a, id_b):
    """Writes each entry's id into the other's related_ids, in one transaction."""
    conn = get_connection()
    try:
        row_a = conn.execute("SELECT related_ids FROM entries WHERE id = ?", (id_a,)).fetchone()
        row_b = conn.execute("SELECT related_ids FROM entries WHERE id = ?", (id_b,)).fetchone()
        if row_a is None or row_b is None:
            raise ValueError("Both entries must exist to link them")

        related_a = json.loads(row_a["related_ids"])
        related_b = json.loads(row_b["related_ids"])

        if id_b not in related_a:
            related_a.append(id_b)
        if id_a not in related_b:
            related_b.append(id_a)

        conn.execute("UPDATE entries SET related_ids = ? WHERE id = ?", (json.dumps(related_a), id_a))
        conn.execute("UPDATE entries SET related_ids = ? WHERE id = ?", (json.dumps(related_b), id_b))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
