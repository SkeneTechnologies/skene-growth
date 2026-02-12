-- Skene Growth: auto-generated migration from telemetry definitions
-- Generated at 2026-02-11T16:42:45.572726

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
  enriched_payload jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE skene_growth.actions IS 'Growth loop actions created by skene-growth-process edge function';

-- Trigger functions
CREATE OR REPLACE FUNCTION skene_growth_fn_api_keys_INSERT_guard_ci_activation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN

SELECT net.http_post(
    url := current_setting('app.settings.supabase_url', true) || '/functions/v1/skene-growth-process',
    headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || current_setting('app.settings.supabase_anon_key', true)
    ),
    body := jsonb_build_object(
        'loop_id', 'guard_ci_activation',
        'action_name', 'guard_integration_activated',
        'table', 'api_keys',
        'operation', TG_OP,
        'event_seq', nextval('skene_growth.event_seq'),
        'db_id', NEW."id"::text,
        'payload', jsonb_build_object('id', NEW."id", 'workspace_id', NEW."workspace_id", 'name', NEW."name", 'created_at', NEW."created_at")
    )
) AS request_id;
RETURN NULL;

$$;

-- Triggers

DROP TRIGGER IF EXISTS skene_growth_trg_api_keys_INSERT_guard_ci_activation ON public.api_keys;
CREATE TRIGGER skene_growth_trg_api_keys_INSERT_guard_ci_activation
  AFTER INSERT ON public.api_keys
  FOR EACH ROW
  EXECUTE FUNCTION skene_growth_fn_api_keys_INSERT_guard_ci_activation();


-- Configure these for pg_net HTTP calls (or use Vault in production):
-- ALTER DATABASE postgres SET app.settings.supabase_url = 'https://YOUR_PROJECT.supabase.co';
-- ALTER DATABASE postgres SET app.settings.supabase_anon_key = 'YOUR_ANON_KEY';