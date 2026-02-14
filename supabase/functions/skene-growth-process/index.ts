// Skene Growth: Cloud action executor (called by processor via pg_net)

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

interface ProcessorPayload {
  source: string;
  event_log_id: number;
  loop_key: string;
  idempotency_key: string;
  recipient: string;
  enriched_payload: Record<string, unknown>;
  action_type: string;
  action_config: Record<string, unknown>;
}

Deno.serve(async (req) => {
  try {
    const body: ProcessorPayload = await req.json();
    if (body.source !== "processor") {
      return new Response(JSON.stringify({ error: "Expected source=processor" }), {
        headers: { "Content-Type": "application/json" },
        status: 400,
      });
    }

    const { loop_key, idempotency_key, recipient, enriched_payload, action_type } = body;
    if (!recipient) {
      return new Response(JSON.stringify({ error: "Missing recipient" }), {
        headers: { "Content-Type": "application/json" },
        status: 400,
      });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    if (action_type === "email") {
      // MVP: log only. Integrate Resend/SendGrid when ready.
      console.log("[skene] would send email to", recipient, "loop:", loop_key);
    }

    return new Response(JSON.stringify({ ok: true, loop_key }), {
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
