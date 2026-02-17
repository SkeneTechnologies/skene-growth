// Skene Growth: Secure proxy to centralized cloud API (called by processor via pg_net)

import { HmacSha256 } from "https://deno.land/std@0.224.0/crypto/crypto.ts";
import { encodeHex } from "https://deno.land/std@0.224.0/encoding/hex.ts";

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

async function signPayload(payload: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const key = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(payload));
  return encodeHex(new Uint8Array(signature));
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

    if (!body.recipient) {
      return new Response(JSON.stringify({ error: "Missing recipient" }), {
        headers: { "Content-Type": "application/json" },
        status: 400,
      });
    }

    // Get configuration from environment
    const SKENE_PROXY_SECRET = Deno.env.get("SKENE_PROXY_SECRET");
    const SKENE_CLOUD_ENDPOINT = Deno.env.get("SKENE_CLOUD_ENDPOINT") || "https://skene.ai/api/v1/cloud";
    const SUPABASE_PROJECT_REF = Deno.env.get("SUPABASE_PROJECT_REF") || "unknown";

    if (!SKENE_PROXY_SECRET) {
      console.error("[skene] SKENE_PROXY_SECRET not set. Deployment service must configure this secret.");
      return new Response(JSON.stringify({ error: "Configuration error" }), {
        headers: { "Content-Type": "application/json" },
        status: 500,
      });
    }

    // Sign the payload for verification by cloud API
    const timestamp = Date.now().toString();
    const payloadString = JSON.stringify(body);
    const signaturePayload = `${timestamp}.${payloadString}`;
    const signature = await signPayload(signaturePayload, SKENE_PROXY_SECRET);

    // Forward to centralized cloud API
    const cloudResponse = await fetch(SKENE_CLOUD_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Skene-Signature": signature,
        "X-Skene-Timestamp": timestamp,
        "X-Skene-Project-Ref": SUPABASE_PROJECT_REF,
      },
      body: payloadString,
    });

    if (!cloudResponse.ok) {
      const errorText = await cloudResponse.text();
      console.error("[skene] Cloud API error:", cloudResponse.status, errorText);
      return new Response(
        JSON.stringify({ 
          error: "Cloud execution failed", 
          status: cloudResponse.status 
        }),
        {
          headers: { "Content-Type": "application/json" },
          status: cloudResponse.status,
        }
      );
    }

    const result = await cloudResponse.json();
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    });

  } catch (err) {
    console.error("[skene] Proxy error:", err);
    return new Response(JSON.stringify({ error: String(err) }), {
      headers: { "Content-Type": "application/json" },
      status: 500,
    });
  }
});
