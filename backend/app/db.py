"""
Neon agent run log. One unified table across all four modules (support,
extraction, meeting, chat) rather than four separate tables - the JSONB payload
columns absorb each module's different shape, and the Admin UI (step 12) reads
this as a single cross-module activity feed instead of four disconnected silos.

Every attempt is logged here - including failed ones (most fields NULL) - so a
failed run still shows up rather than silently vanishing. The connection string
already points at a Neon pooled endpoint (the "-pooler" hostname, PgBouncer-
backed), so opening a fresh connection per request is the correct, intended
usage - no extra client-side pool needed on top of it.
"""

import json
import os
from typing import Any

import psycopg


def _connect() -> psycopg.Connection:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("NEON_DATABASE_URL is not set")
    return psycopg.connect(database_url)


def log_agent_run(
    module: str,
    input_payload: dict[str, Any],
    draft: dict[str, Any] | None,
    verdict: str | None,
    critique: str | None,
    final: dict[str, Any] | None,
    citations: list[str],
) -> str:
    """Inserts an agent run and returns its generated id (as a string)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into agent_runs (module, input, draft, verdict, critique, final, citations)
                values (%s, %s, %s, %s, %s, %s, %s)
                returning id
                """,
                (
                    module,
                    json.dumps(input_payload),
                    json.dumps(draft) if draft is not None else None,
                    verdict,
                    critique,
                    json.dumps(final) if final is not None else None,
                    citations,
                ),
            )
            return str(cur.fetchone()[0])


def list_agent_runs(module: str | None = None, limit: int = 50) -> list[dict]:
    query = "select id, module, input, verdict, created_at from agent_runs"
    params: list[Any] = []
    if module:
        query += " where module = %s"
        params.append(module)
    query += " order by created_at desc limit %s"
    params.append(limit)

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_agent_run(run_id: str) -> dict | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, module, input, draft, verdict, critique, final, citations, created_at
                from agent_runs
                where id = %s
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))


# Rate limiting (see rate_limit.py) gets its own small table rather than an
# ip_address column on the run log, since not every limited endpoint writes a run
# row. Created on first use so a fresh Neon project needs no manual migration.
_rate_limit_table_ready = False


def _ensure_rate_limit_table(cur: psycopg.Cursor) -> None:
    global _rate_limit_table_ready
    if _rate_limit_table_ready:
        return
    cur.execute(
        """
        create table if not exists rate_limit_hits (
          id bigserial primary key,
          ip_address text not null,
          created_at timestamptz not null default now()
        )
        """
    )
    cur.execute(
        "create index if not exists rate_limit_hits_ip_created_idx on rate_limit_hits (ip_address, created_at)"
    )
    _rate_limit_table_ready = True


def count_recent_requests(ip_address: str, window_hours: int) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            _ensure_rate_limit_table(cur)
            cur.execute(
                """
                select count(*) from rate_limit_hits
                where ip_address = %s and created_at > now() - make_interval(hours => %s)
                """,
                (ip_address, window_hours),
            )
            return cur.fetchone()[0]


def record_request(ip_address: str) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            _ensure_rate_limit_table(cur)
            cur.execute("insert into rate_limit_hits (ip_address) values (%s)", (ip_address,))
