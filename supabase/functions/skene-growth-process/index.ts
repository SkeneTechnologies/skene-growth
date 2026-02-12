// Skene Growth: process loop events from DB triggers
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
