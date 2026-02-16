# Troubleshooting

> **Complete troubleshooting guide for skene-growth and the full Skene Growth Stack**

## Table of Contents

1. [FAQ (Frequently Asked Questions)](#faq-frequently-asked-questions)
2. [Error Code Reference](#error-code-reference)
3. [Scanner Issues (skene-growth CLI)](#scanner-issues-skene-growth-cli)
4. [Full Stack Issues](#full-stack-issues)
5. [Common Pitfalls](#common-pitfalls)
6. [Getting Help](#getting-help)

---

## FAQ (Frequently Asked Questions)

### General Questions

#### Q: What's the difference between skene-growth and the full Skene stack?

**A:** `skene-growth` is the CLI scanner (Layer 0) that analyzes codebases. The full stack includes:
- Layer 0: Scanner (skene-growth)
- Layers 1-5: Infrastructure (state machine, audit trail, orchestration)
- Layers 6-7: Growth features (billing, gamification, lifecycle)
- Layer 8: Apps (Admin Console, Slack Bot, Smart Email)

**Use scanner alone for:** Quick analysis, growth plans, implementation prompts

**Use full stack for:** Automated monitoring, Slack bot, real-time dashboards, team collaboration

See: [User Guide](../../docs/USER_GUIDE.md) for complete overview.

---

#### Q: Why isn't the scanner finding my framework?

**A:** Common causes:

1. **Monorepo detection:** Scanner may find multiple frameworks (React + Vue in different packages)
   - **Solution:** Analyze specific subdirectory: `uvx skene-growth analyze ./packages/web-app`

2. **Custom/uncommon framework:** Scanner trained on popular frameworks (Next.js, React, Vue, Angular, etc.)
   - **Solution:** Provide context: `uvx skene-growth analyze . --context "Framework: Remix"`

3. **Old framework version:** May be detected as wrong framework
   - **Solution:** Check manifest tech stack, provide feedback if wrong

---

#### Q: How do I speed up analysis?

**A:** Multiple strategies:

**1. Use faster model:**
```bash
uvx skene-growth analyze . --model gpt-4o-mini  # 3x faster
```

**2. Exclude large directories:**
```bash
uvx skene-growth analyze . --exclude node_modules,dist,.next,coverage
```

**3. Analyze smaller scope:**
```bash
uvx skene-growth analyze ./src  # Only analyze src/ directory
```

**4. Use local LLM:**
```bash
uvx skene-growth config
# Select: 5. Ollama
# Model: llama3.1
uvx skene-growth analyze .  # Instant, free (but less accurate)
```

See: [Best Practices - Large Codebase Strategies](../../docs/BEST_PRACTICES.md#large-codebase-strategies)

---

#### Q: Can I run this without an API key?

**A:** Yes, two options:

**1. Free audit (sample preview):**
```bash
uvx skene-growth audit .  # No API key needed
```
Shows example analysis to understand output format.

**2. Local LLM (Ollama):**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.1

# Configure skene-growth
uvx skene-growth config
# Select: 5. Ollama
# Model: llama3.1

# Analyze (free)
uvx skene-growth analyze .
```

See: [Best Practices - API Cost Management](../../docs/BEST_PRACTICES.md#api-cost-management)

---

#### Q: What's the difference between skene-growth and skene-flow?

**A:** Historical naming:

- **skene-flow** = Old name for the full TypeScript stack (now just "Skene")
- **skene-growth** = Python CLI scanner (Layer 0)
- **Skene Growth Stack** = Complete system (all 8 layers)

**Current naming:**
- Use `skene-growth` when referring to the CLI scanner
- Use "Skene" when referring to the full system

---

#### Q: How do I share results with my team?

**A:** Three approaches:

**1. Commit to git (recommended):**
```bash
git add skene-context/
git commit -m "Growth analysis: Added Stripe integration"
git push
```

**2. Share files directly:**
```bash
# Copy to shared location
cp skene-context/growth-plan.md ~/Dropbox/Team/growth-plan-2026-02-16.md
```

**3. Use full stack (Slack bot):**
```bash
# Start full stack (sidecar + gateway + Slack bot)
# Team queries bot: "@skenebot show me growth opportunities"
```

See: [Team Collaboration Guide](../../docs/TEAM_COLLABORATION.md)

---

### Technical Questions

#### Q: Why does analysis keep timing out?

**A:** Likely token limit exceeded. Solutions:

**1. Increase token limit:**
```bash
# Edit .skene-growth.config
[analysis]
tool_output_limit = 50000  # Default: 30000
```

**2. Exclude large files:**
```bash
uvx skene-growth analyze . --exclude node_modules,dist
```

**3. Use pagination (if available):**
Check if your LLM provider has pagination support.

---

#### Q: What does "--onboarding" flag do?

**A:** Changes plan focus:

**Without --onboarding:**
- General growth opportunities
- Focus: acquisition, referral, monetization
- Example priorities: "Add referral program", "Implement upsell flow"

**With --onboarding:**
- Activation and onboarding focus
- Focus: reducing time-to-value, increasing activation rate
- Example priorities: "Add product tour", "Implement progress checklist"

**Use --onboarding when:**
- Product has high early churn (> 40% in first 7 days)
- Activation rate is low (< 30%)
- Onboarding is complex (> 5 steps)

See: [Best Practices - Command Usage Patterns](../../docs/BEST_PRACTICES.md#command-usage-patterns)

---

#### Q: How do I update an existing analysis?

**A:** Re-run analyze:

```bash
# Save old manifest for comparison
cp skene-context/growth-manifest.json skene-context/archive/growth-manifest-$(date +%Y%m%d).json

# Re-analyze
uvx skene-growth analyze .

# Compare changes
diff skene-context/archive/growth-manifest-20260201.json skene-context/growth-manifest.json
```

**When to re-analyze:**
- After major feature launches
- Monthly (keep manifests fresh)
- When tech stack changes

See: [Daily Workflows - Code Change Analysis](../../docs/DAILY_WORKFLOWS.md#code-change-analysis-workflow)

---

#### Q: Can I customize the growth plan output?

**A:** Limited customization currently available:

**Focus area:**
```bash
uvx skene-growth plan --onboarding  # Activation focus
uvx skene-growth plan  # General growth focus
```

**Provide context:**
```bash
# Create product-context.md
echo "Product: B2B SaaS for finance teams" > skene-context/product-context.md
echo "Target audience: CFOs at mid-market companies" >> skene-context/product-context.md

# Use in analysis
uvx skene-growth analyze . --context skene-context/product-context.md
```

See: [Best Practices - Growth Plan Quality](../../docs/BEST_PRACTICES.md#growth-plan-quality)

---

## Error Code Reference

### Scanner Errors (skene-growth)

#### ERROR_001: Invalid API Key

**Full error:**
```
Error: Invalid API key provided
Code: ERROR_001
```

**Cause:** API key is incorrect, expired, or for wrong provider

**Solution:**
```bash
# Verify key in config
cat .skene-growth.config

# Or reconfigure
uvx skene-growth config

# Test with explicit key
uvx skene-growth analyze . --api-key "sk-..." --debug
```

---

#### ERROR_002: Manifest Not Found

**Full error:**
```
Error: Growth manifest not found at ./skene-context/growth-manifest.json
Code: ERROR_002
```

**Cause:** `plan` or `build` command run before `analyze`

**Solution:**
```bash
# Run analyze first
uvx skene-growth analyze .

# Then plan
uvx skene-growth plan

# Or specify custom path
uvx skene-growth plan --manifest /path/to/manifest.json
```

---

#### ERROR_003: Token Limit Exceeded

**Full error:**
```
Error: The model's maximum context length is 128000 tokens, but the current request uses 145000 tokens
Code: ERROR_003
```

**Cause:** Codebase too large for model's context window

**Solution:**
```bash
# Option 1: Exclude large directories
uvx skene-growth analyze . --exclude node_modules,dist,.next

# Option 2: Analyze subdirectory
uvx skene-growth analyze ./src

# Option 3: Increase tool output limit
# Edit .skene-growth.config:
[analysis]
tool_output_limit = 50000
```

---

#### ERROR_004: LLM Provider Connection Failed

**Full error:**
```
Error: Failed to connect to LLM provider at http://localhost:1234
Code: ERROR_004
```

**Cause:** Local LLM (LM Studio, Ollama) not running

**Solution:**
```bash
# For LM Studio:
# 1. Open LM Studio
# 2. Load a model
# 3. Start server (should auto-start)

# For Ollama:
ollama serve

# Verify connection
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:1234/v1/models  # LM Studio
```

---

#### ERROR_005: Invalid Model Name

**Full error:**
```
Error: Model 'gpt-5o' not found
Code: ERROR_005
```

**Cause:** Model name is incorrect or unavailable

**Solution:**
```bash
# Valid OpenAI models:
# - gpt-4o
# - gpt-4o-mini
# - gpt-4-turbo

# Check available models:
uvx skene-growth config
# Interactive menu shows valid models per provider
```

---

### Full Stack Errors

#### ERROR_101: Sidecar Connection Refused

**Full error:**
```
Error: Connection refused to sidecar daemon at http://localhost:3003
Code: ERROR_101
```

**Cause:** Sidecar daemon not running

**Solution:**
```bash
# Check if sidecar is running
curl http://localhost:3003/health

# If not, start it
cd /path/to/skene
pnpm sidecar

# Verify
curl http://localhost:3003/health
# Expected: {"status":"ok"}
```

---

#### ERROR_102: Gateway Connection Refused

**Full error:**
```
Error: Connection refused to gateway at http://localhost:3100
Code: ERROR_102
```

**Cause:** Gateway not running or wrong port

**Solution:**
```bash
# Check gateway status
curl http://localhost:3100/health

# If not running, start it
pnpm bot:gateway

# If using custom port, update .env:
GATEWAY_PORT=3100
```

---

#### ERROR_103: Missing Environment Variable

**Full error:**
```
Error: Required environment variable SLACK_BOT_TOKEN is not set
Code: ERROR_103
```

**Cause:** Required environment variable not configured

**Solution:**
```bash
# Check .env file
cat .env | grep SLACK_BOT_TOKEN

# If missing, add it
echo "SLACK_BOT_TOKEN=xoxb-your-token" >> .env

# Verify permissions
ls -la .env
# Should be: -rw------- (600)
```

---

#### ERROR_104: Slack API Error

**Full error:**
```
Error: Slack API error: invalid_auth
Code: ERROR_104
```

**Cause:** Slack bot token is invalid or revoked

**Solution:**
```bash
# Regenerate token in Slack app settings
# Go to: https://api.slack.com/apps
# Select your app > OAuth & Permissions
# Reinstall to workspace
# Copy new token

# Update .env
SLACK_BOT_TOKEN=xoxb-new-token

# Restart bot
pkill -f bot:slack
pnpm bot:slack
```

---

#### ERROR_105: Manifest File Corrupted

**Full error:**
```
Error: Failed to parse growth manifest: Invalid JSON at line 45
Code: ERROR_105
```

**Cause:** Manifest JSON file is corrupted or invalid

**Solution:**
```bash
# Validate JSON
jq . skene-context/growth-manifest.json

# If invalid, regenerate
rm skene-context/growth-manifest.json
uvx skene-growth analyze .

# Or restore from git
git checkout skene-context/growth-manifest.json
```

---

## Scanner Issues (skene-growth CLI)

Solutions for common issues when using skene-growth.

## LM Studio

### Context length error

```
Error code: 400 - {'error': 'The number of tokens to keep from the initial prompt is greater than the context length...'}
```

The model's context length is too small for the analysis. To fix:

1. In LM Studio, unload the current model
2. Go to **Developer > Load**
3. Click on **Context Length: Model supports up to N tokens**
4. Set it to the maximum supported value
5. Reload to apply changes

Reference: [lmstudio-ai/lmstudio-bug-tracker#237](https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/237)

### Connection refused

Ensure:
- LM Studio is running
- A model is loaded and ready
- The server is running on the default port (`http://localhost:1234`)

For a custom port:

```bash
export LMSTUDIO_BASE_URL="http://localhost:8080/v1"
```

## Ollama

### Connection refused

Ensure:
- Ollama is running (`ollama serve`)
- A model is pulled and available (`ollama list`)
- The server is on the default port (`http://localhost:11434`)

Getting started with Ollama:

```bash
# Pull a model
ollama pull llama3.3

# Start the server (usually runs automatically after install)
ollama serve
```

For a custom port:

```bash
export OLLAMA_BASE_URL="http://localhost:8080/v1"
```

## API key issues

### "No API key" or fallback to sample report

If `analyze` runs without an API key, it falls back to showing a sample preview (equivalent to `audit`). Set your key using one of:

```bash
# CLI flag
uvx skene-growth analyze . --api-key "your-key"

# Environment variable
export SKENE_API_KEY="your-key"

# Config file (interactive)
uvx skene-growth config
```

### Wrong provider for API key

Make sure the API key matches the provider. An OpenAI key won't work with `--provider gemini`.

## Provider issues

### Unknown provider

Valid provider names:
- `openai`
- `gemini`
- `anthropic` or `claude`
- `lmstudio`, `lm-studio`, or `lm_studio`
- `ollama`
- `generic`, `openai-compatible`, or `openai_compatible`

### Generic provider: missing base URL

The `generic` provider requires a base URL:

```bash
uvx skene-growth analyze . --provider generic --base-url "http://localhost:8000/v1" --model "your-model"
```

Or set via environment variable:

```bash
export SKENE_BASE_URL="http://localhost:8000/v1"
```

## File not found errors

### Manifest not found (plan/build commands)

The `plan` and `build` commands look for files in `./skene-context/` by default. Make sure you've run `analyze` first:

```bash
uvx skene-growth analyze .   # Creates ./skene-context/growth-manifest.json
uvx skene-growth plan        # Reads from ./skene-context/
```

Or specify paths explicitly:

```bash
uvx skene-growth plan --manifest ./path/to/manifest.json --template ./path/to/template.json
uvx skene-growth plan --context ./my-output-dir
```

### Growth plan not found (build command)

```bash
uvx skene-growth plan    # Creates ./skene-context/growth-plan.md
uvx skene-growth build   # Reads from ./skene-context/

# Or specify explicitly
uvx skene-growth build --plan ./path/to/growth-plan.md
```

## Debug mode

Use `--debug` on any command to log all LLM input and output to `.skene-growth/debug/`:

```bash
uvx skene-growth analyze . --debug
uvx skene-growth plan --debug
uvx skene-growth chat --debug
```

Debug mode can also be enabled via environment variable or config:

```bash
export SKENE_DEBUG=true
```

```toml
# .skene-growth.config
debug = true
```

The debug logs show the full prompts sent to the LLM and the complete responses, which is useful for diagnosing unexpected output or provider-specific issues.

---

## Full Stack Issues

### Sidecar Daemon Not Starting

**Symptoms:**
```bash
pnpm sidecar

# Error: Port 3003 already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :3003

# Kill process
kill -9 <PID>

# Or use different port
SIDECAR_PORT=3005 pnpm sidecar
```

---

**Symptoms:**
```bash
pnpm sidecar

# Error: Manifest not found at ./growth-manifest-self.json
```

**Solution:**
```bash
# Generate manifest first
uvx skene-growth analyze .

# Copy to expected location
cp skene-context/growth-manifest.json ./growth-manifest-self.json

# Or update .env to point to correct path
echo "MANIFEST_PATH=./skene-context/growth-manifest.json" >> .env
```

---

### Gateway Issues

**Symptom: Gateway can't connect to sidecar**

```bash
pnpm bot:gateway

# Error: ECONNREFUSED http://localhost:3003
```

**Solution:**
```bash
# Check sidecar is running
curl http://localhost:3003/health

# If not, start sidecar first
pnpm sidecar

# Then start gateway
pnpm bot:gateway
```

---

**Symptom: High queue depth (slow responses)**

```bash
curl http://localhost:3100/health | jq '.queue_depth'
# Output: 150  ← Too high!
```

**Solution:**
```bash
# Restart gateway to clear queue
pkill -f bot:gateway
pnpm bot:gateway

# If problem persists, check sidecar performance
curl http://localhost:3003/health | jq '.uptime'
# If low uptime, sidecar is crashing - check logs
tail -f .skene/sidecar.log
```

---

### Slack Bot Issues

**Symptom: Bot not responding to @mentions**

```bash
@skenebot status
(no response)
```

**Diagnosis:**
```bash
# 1. Check bot is running
ps aux | grep bot:slack

# 2. Check gateway connection
curl http://localhost:3100/health

# 3. Check bot logs
tail -f .skene/bot.log

# Look for errors like:
# - Invalid Slack token
# - Gateway connection refused
# - Event subscription verification failed
```

**Solution:**
```bash
# Restart bot
pkill -f bot:slack
pnpm bot:slack

# Verify Slack token
cat .env | grep SLACK_BOT_TOKEN
# Should start with: xoxb-
```

---

**Symptom: "Permission denied" on approval**

```bash
Click [Approve & Send]
# Error: Permission denied
```

**Solution:**
```bash
# Option 1: Add user to approvers
# Edit .env:
SLACK_APPROVERS=alice@company.com,bob@company.com,your@email.com

# Restart bot
pkill -f bot:slack
pnpm bot:slack

# Option 2: Disable approval restrictions
# Edit .env, comment out:
# SLACK_APPROVERS=...
```

---

### Admin Console Issues

**Symptom: "Sidecar disconnected" error**

```bash
# Open http://localhost:3002
# Shows: ⚠️ Sidecar disconnected
```

**Solution:**
```bash
# Check sidecar health
curl http://localhost:3003/health

# If unhealthy, check logs
tail -f .skene/sidecar.log

# Restart sidecar if needed
pkill -f sidecar-daemon
pnpm sidecar

# Refresh console
# Should now show: ✅ Sidecar connected
```

---

**Symptom: Dashboard shows stale data**

```bash
# MRR shows: $12,450
# Last updated: 2 hours ago  ← Stale!
```

**Solution:**
```bash
# Clear sidecar cache
curl -X POST http://localhost:3003/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{"toolId":"cache.clear","input":{}}'

# Or restart sidecar (clears cache)
pkill -f sidecar-daemon
pnpm sidecar

# Refresh dashboard
```

---

## Common Pitfalls

### Pitfall #1: Running `plan` Before `analyze`

**Mistake:**
```bash
# First time user
cd /path/to/project
uvx skene-growth plan

# Error: Manifest not found
```

**Why it fails:** `plan` needs a manifest, which is created by `analyze`

**Correct workflow:**
```bash
# 1. Analyze first
uvx skene-growth analyze .

# 2. Then plan
uvx skene-growth plan

# 3. Then build
uvx skene-growth build
```

---

### Pitfall #2: Forgetting to Configure LLM Provider

**Mistake:**
```bash
uvx skene-growth analyze .

# Falls back to sample audit (no API key)
```

**Why it fails:** No API key configured, so scanner can't use LLM

**Correct workflow:**
```bash
# Configure first
uvx skene-growth config

# Follow prompts:
# - Select provider (OpenAI, Gemini, etc.)
# - Enter API key
# - Choose model

# Then analyze
uvx skene-growth analyze .
```

---

### Pitfall #3: Using Wrong Working Directory

**Mistake:**
```bash
cd /Users/alice
uvx skene-growth plan

# Error: Manifest not found at ./skene-context/
```

**Why it fails:** Looking for manifest in home directory, not project directory

**Correct workflow:**
```bash
# Change to project directory
cd /path/to/your/project

# Then run commands
uvx skene-growth plan
```

---

### Pitfall #4: Not Excluding Large Directories

**Mistake:**
```bash
# Analyze entire monorepo (500K lines)
uvx skene-growth analyze .

# Takes 40 minutes, costs $20 in API calls
```

**Why it's inefficient:** Analyzing `node_modules`, `dist`, `.next` wastes tokens

**Correct workflow:**
```bash
# Exclude irrelevant directories
uvx skene-growth analyze . --exclude node_modules,dist,.next,coverage,.git

# Takes 5 minutes, costs $3
```

See: [Best Practices - Large Codebase Strategies](../../docs/BEST_PRACTICES.md#large-codebase-strategies)

---

### Pitfall #5: Committing API Keys to Git

**Mistake:**
```bash
# Edit .skene-growth.config
[llm]
api_key = "sk-proj-abc123..."

# Commit to git
git add .skene-growth.config
git commit -m "Add config"
git push

# 🚨 API key exposed in public repo!
```

**Why it's dangerous:** API keys in git history can be found by bots, leading to unauthorized usage

**Correct workflow:**
```bash
# Add to .gitignore
echo ".skene-growth.config" >> .gitignore
echo ".env" >> .gitignore

# Use environment variable
export SKENE_API_KEY="sk-proj-abc123..."
uvx skene-growth analyze .

# Or config file with env var reference
[llm]
# api_key = "${SKENE_API_KEY}"  # Loaded from environment
```

See: [Best Practices - Security & Compliance](../../docs/BEST_PRACTICES.md#security--compliance)

---

### Pitfall #6: Using `--onboarding` for Mature Products

**Mistake:**
```bash
# Mature B2B SaaS (3 years old, 1000+ users, 70% activation)
uvx skene-growth plan --onboarding

# Gets recommendations for:
# - "Add product tour" (already exists)
# - "Implement progress checklist" (already exists)
# - "Send activation emails" (already doing this)
```

**Why it's suboptimal:** `--onboarding` focuses on activation, but mature products need monetization/retention focus

**Correct workflow:**
```bash
# Use regular plan for mature products
uvx skene-growth plan

# Gets recommendations for:
# - "Add usage-based upsell" (increases revenue)
# - "Implement win-back campaign" (reduces churn)
# - "Build referral leaderboard" (viral growth)
```

See: [Best Practices - Command Usage Patterns](../../docs/BEST_PRACTICES.md#command-usage-patterns)

---

### Pitfall #7: Ignoring Manifest Versioning

**Mistake:**
```bash
# Week 1: Analyze
uvx skene-growth analyze .

# Week 2: Analyze again (overwrites manifest)
uvx skene-growth analyze .

# Week 3: Analyze again (overwrites manifest)
uvx skene-growth analyze .

# No historical comparison possible!
```

**Why it's suboptimal:** Can't track product evolution or measure impact

**Correct workflow:**
```bash
# Week 1: Analyze
uvx skene-growth analyze .

# Week 2: Save old manifest, then analyze
cp skene-context/growth-manifest.json skene-context/archive/manifest-20260209.json
uvx skene-growth analyze .

# Week 3: Save old manifest, then analyze
cp skene-context/growth-manifest.json skene-context/archive/manifest-20260216.json
uvx skene-growth analyze .

# Now can compare:
diff skene-context/archive/manifest-20260209.json \
     skene-context/archive/manifest-20260216.json
```

See: [Best Practices - Manifest Versioning](../../docs/BEST_PRACTICES.md#manifest-versioning-strategy)

---

## Component-Specific Debugging

### Debugging Scanner (skene-growth)

**Enable debug mode:**
```bash
uvx skene-growth analyze . --debug
```

**Check debug logs:**
```bash
ls -la .skene-growth/debug/

# Contains:
# - analyze-YYYYMMDD-HHMMSS.json (full LLM input/output)
# - plan-YYYYMMDD-HHMMSS.json
# - build-YYYYMMDD-HHMMSS.json
```

**Common debug findings:**

**1. Tech stack misdetection:**
```bash
# Open debug log
cat .skene-growth/debug/analyze-20260216-140522.json | jq '.tech_stack_detection'

# Shows LLM reasoning:
# "Detected: React 16"
# Reasoning: "Found import React from 'react' in src/App.js, package.json shows react@16.8.0"

# If wrong, provide context:
uvx skene-growth analyze . --context "Framework: React 18"
```

**2. Missing growth features:**
```bash
# Check what was analyzed
cat .skene-growth/debug/analyze-20260216-140522.json | jq '.files_analyzed'

# If key files missing, check exclusions:
cat .skene-growth.config | grep exclude_dirs
```

---

### Debugging Sidecar Daemon

**Check health:**
```bash
curl http://localhost:3003/health | jq .
```

**Expected healthy response:**
```json
{
  "status": "ok",
  "uptime": 3600,
  "timestamp": "2026-02-16T14:30:00Z",
  "components": {
    "manifest": "loaded",
    "state_machine": "initialized",
    "audit_trail": "running",
    "skills": 62,
    "webhook_server": "running"
  }
}
```

**Check logs:**
```bash
tail -f .skene/sidecar.log

# Look for errors:
# - ERROR: Failed to load manifest
# - ERROR: State machine transition failed
# - ERROR: Webhook processing error
```

**Test specific tool:**
```bash
curl -X POST http://localhost:3003/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{"toolId":"analytics.get-mrr","input":{}}' | jq .
```

---

### Debugging Gateway

**Check health:**
```bash
curl http://localhost:3100/health | jq .
```

**Expected healthy response:**
```json
{
  "status": "ok",
  "sidecar": "connected",
  "queue_depth": 0,
  "uptime": 1800
}
```

**Check queue depth:**
```bash
# High queue depth = slow processing
curl http://localhost:3100/health | jq '.queue_depth'

# If > 100, restart gateway
pkill -f bot:gateway
pnpm bot:gateway
```

**Check logs:**
```bash
tail -f .skene/gateway.log

# Look for:
# - ERROR: Sidecar connection lost
# - WARNING: Queue depth high (> 100)
# - ERROR: Message routing failed
```

---

### Debugging Slack Bot

**Check logs:**
```bash
tail -f .skene/bot.log

# Look for:
# - ERROR: Invalid Slack token
# - ERROR: Event verification failed
# - WARNING: Approval timeout
```

**Test bot connection:**
```bash
# In Slack:
@skenebot status

# If no response, check:
# 1. Bot is running (ps aux | grep bot:slack)
# 2. Gateway is connected (curl http://localhost:3100/health)
# 3. Slack token is valid (cat .env | grep SLACK_BOT_TOKEN)
```

**Enable Slack debug mode:**
```bash
# Edit .env:
LOG_LEVEL=debug

# Restart bot
pkill -f bot:slack
pnpm bot:slack

# Now logs show all Slack events
tail -f .skene/bot.log | grep slack
```

---

## Getting help

### Self-Service Resources

- **Documentation:** [docs/](../../docs/) - User guides, workflows, best practices
- **FAQ:** This file (see above)
- **Use Cases:** [docs/overview/USE_CASES.md](../../docs/overview/USE_CASES.md) - Working code examples

### Community Support

- **GitHub Issues:** [github.com/SkeneTechnologies/skene/issues](https://github.com/SkeneTechnologies/skene/issues)
- **GitHub Discussions:** [github.com/SkeneTechnologies/skene/discussions](https://github.com/SkeneTechnologies/skene/discussions)

### When Creating an Issue

**Include:**
1. **Command run:** `uvx skene-growth analyze . --model gpt-4o`
2. **Error message:** Full error output (copy-paste)
3. **Environment:**
   - OS: macOS 14.3 / Ubuntu 22.04 / Windows 11
   - Python version: `python --version`
   - skene-growth version: `uvx skene-growth --version`
4. **Debug logs:** Attach `.skene-growth/debug/*.json` (if available)
5. **What you expected:** "Should generate manifest in 5 minutes"
6. **What actually happened:** "Timeout after 20 minutes"

**Example good issue:**
```
Title: Analysis timeout with gpt-4o on large monorepo

Command: uvx skene-growth analyze . --model gpt-4o --debug

Error:
---
Error: Request timeout after 300 seconds
Code: ERROR_003
---

Environment:
- OS: macOS 14.3
- Python: 3.11.5
- skene-growth: 0.2.0

Expected: Analysis completes in 5-10 minutes
Actual: Timeout after 5 minutes

Debug log attached: analyze-20260216-140522.json

Codebase size: ~150K lines (TypeScript monorepo)
```

---

## Quick Diagnostic Checklist

**Scanner not working?**
- [ ] API key configured? (`cat .skene-growth.config`)
- [ ] Correct provider? (`uvx skene-growth config`)
- [ ] Model available? (`--model gpt-4o` exists)
- [ ] Excluded large dirs? (`--exclude node_modules,dist`)
- [ ] Debug mode enabled? (`--debug`)

**Full stack not working?**
- [ ] Sidecar running? (`curl http://localhost:3003/health`)
- [ ] Gateway running? (`curl http://localhost:3100/health`)
- [ ] Manifest exists? (`ls -la growth-manifest-self.json`)
- [ ] Environment vars set? (`cat .env`)
- [ ] Ports available? (`lsof -i :3003,3100`)

**Slack bot not working?**
- [ ] Bot token valid? (`cat .env | grep SLACK_BOT_TOKEN`)
- [ ] Bot invited to channel? (`/invite @skenebot`)
- [ ] Gateway connected? (`curl http://localhost:3100/health`)
- [ ] Event subscriptions enabled? (Check Slack app settings)
- [ ] Bot is running? (`ps aux | grep bot:slack`)

---

**Also see:**
- [Getting Started Guide](../../docs/GETTING_STARTED.md) - Initial setup
- [Best Practices](../../docs/BEST_PRACTICES.md) - Avoid common mistakes
- [Daily Workflows](../../docs/DAILY_WORKFLOWS.md) - Usage patterns

---

**Built with Claude Code** 🚀
