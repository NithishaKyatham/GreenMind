"""
Portable primary-key helper.

We store UUIDs as CHAR(36) strings rather than using Postgres's native UUID
type, because the project must also run on SQLite for local development
(per project spec: PostgreSQL primary, SQLite optional fallback). A native
Postgres UUID column would fail on SQLite.
"""
import uuid


def gen_uuid() -> str:
    return str(uuid.uuid4())
