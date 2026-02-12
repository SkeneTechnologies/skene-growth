"""
Deploy utilities for building Supabase migrations from growth loop telemetry.

Builds migration files that create:
- Idempotent triggers on telemetry-defined tables (public schema)
- Edge function invocation via pg_net

And generates the edge function that processes loop events with enrichment
and action-creation logic.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


def _trigger_name(table: str, operation: str, loop_id: str) -> str:
    """Generate a safe trigger name."""
    safe_loop = re.sub(r"[^a-z0-9_]", "_", loop_id.lower())
    return f"skene_growth_trg_{table}_{operation}_{safe_loop}"


def _function_name(table: str, operation: str, loop_id: str) -> str:
    """Generate a safe function name for the trigger."""
    safe_loop = re.sub(r"[^a-z0-9_]", "_", loop_id.lower())
    return f"skene_growth_fn_{table}_{operation}_{safe_loop}"


def _build_trigger_function_sql(
    *,
    loop_id: str,
    action_name: str,
    table: str,
    operation: str,
    properties: list[str],
) -> str:
    """
    Build SQL for the trigger function that invokes the edge function via pg_net.

    Uses TG_OP to get INSERT/UPDATE/DELETE. For INSERT/UPDATE, uses NEW;
    for DELETE, uses OLD. Extracts properties from the row and sends as JSON.
    """
    fn_name = _function_name(table, operation, loop_id)

    # Map TG_OP to which row to use
    row_var = "NEW" if operation in ("INSERT", "UPDATE") else "OLD"

    # Build JSON object from properties (keys single-quoted, values from row)
    props_exprs = []
    for p in properties:
        safe_col = p.replace('"', '""')
        safe_key = p.replace("'", "''")
        props_exprs.append(f"'{safe_key}', {row_var}.\"{safe_col}\"")
    props_json = "jsonb_build_object(" + ", ".join(props_exprs) + ")"

    # db_id: use 'id' if in properties, else first column
    db_id_expr = 'id'
    if "id" in [c.lower() for c in properties]:
        db_id_col = next((c for c in properties if c.lower() == "id"), properties[0])
        db_id_expr = f'{row_var}."{db_id_col}"'
    else:
        db_id_col = properties[0] if properties else "id"
        db_id_expr = f'{row_var}."{db_id_col}"'

    body = f"""
SELECT net.http_post(
    url := current_setting('app.settings.supabase_url', true) || '/functions/v1/skene-growth-process',
    headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || current_setting('app.settings.supabase_anon_key', true)
    ),
    body := jsonb_build_object(
        'loop_id', '{loop_id}',
        'action_name', '{action_name}',
        'table', '{table}',
        'operation', TG_OP,
        'event_seq', nextval('skene_growth.event_seq'),
        'db_id', {db_id_expr}::text,
        'payload', {props_json}
    )
) AS request_id;
RETURN NULL;
"""
    return f"""
CREATE OR REPLACE FUNCTION {fn_name}()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
{body}
$$;
""".strip()


def _build_trigger_sql(table: str, operation: str, loop_id: str) -> str:
    """Build DROP + CREATE TRIGGER SQL (idempotent)."""
    trg_name = _trigger_name(table, operation, loop_id)
    fn_name = _function_name(table, operation, loop_id)

    timing = "AFTER"
    return f"""
DROP TRIGGER IF EXISTS {trg_name} ON public.{table};
CREATE TRIGGER {trg_name}
  {timing} {operation} ON public.{table}
  FOR EACH ROW
  EXECUTE FUNCTION {fn_name}();
"""


def extract_supabase_telemetry(loop_def: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract telemetry items with type 'supabase' from a loop definition.
    """
    telemetry = loop_def.get("requirements", {}).get("telemetry", [])
    return [
        t
        for t in telemetry
        if isinstance(t, dict) and t.get("type") == "supabase"
    ]


def build_migration_sql(
    loops: list[dict[str, Any]],
    *,
    supabase_url_placeholder: str = "https://YOUR_PROJECT.supabase.co",
) -> str:
    """
    Build a complete Supabase migration SQL from growth loop definitions.

    Creates:
    - skene_growth schema and event_seq sequence
    - skene_growth.actions table for storing created actions
    - pg_net extension (if available)
    - One trigger function + trigger per telemetry item (table, operation)
    - Idempotent: DROP TRIGGER IF EXISTS before CREATE
    """
    seen: set[tuple[str, str, str]] = set()
    fn_parts: list[str] = []
    trg_parts: list[str] = []

    for loop_def in loops:
        loop_id = loop_def.get("loop_id", "growth_loop")
        for t in extract_supabase_telemetry(loop_def):
            table = t.get("table")
            operation = (t.get("operation") or "INSERT").upper()
            action_name = t.get("action_name", "action")
            properties = t.get("properties") or ["id"]

            if not table:
                continue
            key = (table, operation, loop_id)
            if key in seen:
                continue
            seen.add(key)

            fn_sql = _build_trigger_function_sql(
                loop_id=loop_id,
                action_name=action_name,
                table=table,
                operation=operation,
                properties=properties,
            )

            fn_parts.append(fn_sql)

            trg_sql = _build_trigger_sql(table, operation, loop_id)
            trg_parts.append(trg_sql)

    migration = f"""-- Skene Growth: auto-generated migration from telemetry definitions
-- Generated at {datetime.now().isoformat()}

-- Ensure pg_net extension for async HTTP calls to Edge Functions
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- skene_growth schema and objects
CREATE SCHEMA IF NOT EXISTS skene_growth;

CREATE SEQUENCE IF NOT EXISTS skene_growth.event_seq;

CREATE TABLE IF NOT EXISTS skene_growth.actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  loop_id text NOT NULL,
  action_name text NOT NULL,
  db_id text NOT NULL,
  enriched_payload jsonb DEFAULT '{{}}',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE skene_growth.actions IS 'Growth loop actions created by skene-growth-process edge function';

-- Trigger functions
"""
    migration += "\n\n".join(fn_parts)
    migration += "\n\n-- Triggers\n"
    migration += "\n".join(trg_parts)

    migration += """

-- Configure these for pg_net HTTP calls (or use Vault in production):
-- ALTER DATABASE postgres SET app.settings.supabase_url = 'https://YOUR_PROJECT.supabase.co';
-- ALTER DATABASE postgres SET app.settings.supabase_anon_key = 'YOUR_ANON_KEY';
"""

    return migration.strip()


def build_edge_function_index_ts(loops: list[dict[str, Any]]) -> str:
    """
    Build the Deno/TypeScript index for the skene-growth-process edge function.

    Logic:
    - Receives event from trigger (loop_id, action_name, table, operation, db_id, payload, event_seq)
    - Enriches: resolve user_id/workspace_id to email etc via Supabase client
    - Creates action if event_seq % 5 == 0 (heartbeat every 5th event)
    - Each action includes db_id
    """
    return '''// Skene Growth: process loop events from DB triggers
// Auto-generated – enriches payload and creates actions (min: every 5th event)

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

interface TriggerPayload {
  loop_id: string;
  action_name: string;
  table: string;
  operation: string;
  event_seq: number;
  db_id: string;
  payload: Record<string, unknown>;
}

Deno.serve(async (req) => {
  try {
    const event: TriggerPayload = await req.json();
    const { loop_id, action_name, event_seq, db_id, payload } = event;

    // Minimum logic: create action if event_seq is divisible by 5
    const shouldCreateAction = event_seq % 5 === 0;

    if (!shouldCreateAction) {
      return new Response(JSON.stringify({ skipped: true, event_seq }), {
        headers: { "Content-Type": "application/json" },
        status: 200,
      });
    }

    // Enrich: resolve user/workspace to email etc
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const enriched: Record<string, unknown> = { ...payload, db_id };

    // If payload has workspace_id, try to resolve owner email
    const workspaceId = payload?.workspace_id ?? payload?.workspaceId;
    if (workspaceId) {
      const { data: ws } = await supabase
        .from("workspaces")
        .select("owner_id")
        .eq("id", workspaceId)
        .single();
      if (ws?.owner_id) {
        const { data: user } = await supabase.auth.admin.getUserById(ws.owner_id);
        if (user?.user?.email) {
          enriched.email = user.user.email;
          enriched.user_id = ws.owner_id;
        }
      }
    }

    // If payload has user_id directly
    const userId = payload?.user_id ?? payload?.owner_id;
    if (userId && !enriched.email) {
      const { data: user } = await supabase.auth.admin.getUserById(userId);
      if (user?.user?.email) {
        enriched.email = user.user.email;
        enriched.user_id = userId;
      }
    }

    // Insert action with db_id (required)
    const { error } = await supabase.schema("skene_growth").from("actions").insert({
      loop_id,
      action_name,
      db_id,
      enriched_payload: enriched,
    });

    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        headers: { "Content-Type": "application/json" },
        status: 500,
      });
    }

    return new Response(JSON.stringify({ created: true, db_id, loop_id }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), {
      headers: { "Content-Type": "application/json" },
      status: 500,
    });
  }
});
'''


def write_migration(
    migration_sql: str,
    output_dir: Path,
    *,
    migration_name: str = "skene_growth_telemetry",
) -> Path:
    """Write migration SQL to supabase/migrations/ with timestamp filename."""
    migrations_dir = output_dir / "supabase" / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{migration_name}.sql"
    path = migrations_dir / filename
    path.write_text(migration_sql, encoding="utf-8")
    return path


def write_edge_function(index_ts: str, output_dir: Path) -> Path:
    """Write edge function to supabase/functions/skene-growth-process/."""
    fn_dir = output_dir / "supabase" / "functions" / "skene-growth-process"
    fn_dir.mkdir(parents=True, exist_ok=True)
    path = fn_dir / "index.ts"
    path.write_text(index_ts, encoding="utf-8")
    return path


def deploy_loops_to_supabase(
    loops: list[dict[str, Any]],
    output_dir: Path,
    *,
    supabase_url_placeholder: str = "https://YOUR_PROJECT.supabase.co",
) -> tuple[Path, Path]:
    """
    Build migration and edge function for the given growth loops.

    Returns:
        Tuple of (migration_path, edge_function_path)
    """
    migration_sql = build_migration_sql(
        loops,
        supabase_url_placeholder=supabase_url_placeholder,
    )
    edge_ts = build_edge_function_index_ts(loops)

    migration_path = write_migration(migration_sql, output_dir)
    edge_path = write_edge_function(edge_ts, output_dir)

    return migration_path, edge_path
