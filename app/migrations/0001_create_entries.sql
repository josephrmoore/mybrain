CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    silo TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    taxonomy_stage TEXT NOT NULL CHECK(taxonomy_stage IN ('thought','idea','concept','project','product','record')),
    tags TEXT NOT NULL DEFAULT '[]',
    related_ids TEXT NOT NULL DEFAULT '[]',
    is_deleted INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL DEFAULT '{}'
);
