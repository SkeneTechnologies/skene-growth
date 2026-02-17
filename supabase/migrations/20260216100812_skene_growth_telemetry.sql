-- Skene Growth: allowlisted triggers insert into event_log (Shadow Mirror)
-- Generated at 2026-02-16T10:08:12.501302
-- Depends on: 20260201000000_skene_growth_schema.sql (run skene init first)

-- Trigger functions
CREATE OR REPLACE FUNCTION skene_growth_fn_api_keys_INSERT_guard_ci_activation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, skene_growth
AS $$
BEGIN

BEGIN
  INSERT INTO skene_growth.event_log (entity_id, event_type, metadata)
  VALUES (NEW."id"::uuid, 'api_keys.insert', jsonb_build_object('id', NEW."id", 'workspace_id', NEW."workspace_id", 'name', NEW."name"));
EXCEPTION WHEN invalid_text_representation OR OTHERS THEN
  INSERT INTO skene_growth.event_log (entity_id, event_type, metadata)
  VALUES (NULL, 'api_keys.insert', jsonb_build_object('id', NEW."id", 'workspace_id', NEW."workspace_id", 'name', NEW."name"));
END;
RETURN NULL;

$$;

-- Triggers

DROP TRIGGER IF EXISTS skene_growth_trg_api_keys_INSERT_guard_ci_activation ON public.api_keys;
CREATE TRIGGER skene_growth_trg_api_keys_INSERT_guard_ci_activation
  AFTER INSERT ON public.api_keys
  FOR EACH ROW
  EXECUTE FUNCTION skene_growth_fn_api_keys_INSERT_guard_ci_activation();


-- Seed growth_loops (upsert from loop definitions)

INSERT INTO skene_growth.growth_loops (loop_key, trigger_event, condition_config, action_type, action_config, recipient_path, enabled)
VALUES ('guard_ci_activation_api_keys_insert', 'api_keys.insert', '{}', 'email', '{}', 'email', true)
ON CONFLICT (loop_key) DO UPDATE SET trigger_event = EXCLUDED.trigger_event, enabled = EXCLUDED.enabled;