# Onboarding Audit - Local Heuristics

The onboarding audit is a local-first analysis tool that detects 50 PLG onboarding anti-patterns using pure Python heuristics. No API key or LLM required.

## Features

- **⚡ Fast**: Completes in <20 seconds for most projects
- **🔒 Local**: No external API calls, works completely offline
- **🎯 Actionable**: Severity-ranked issues with file paths and detailed explanations
- **📊 Comprehensive**: Detects 50 patterns across onboarding, UX, performance, and growth

## Usage

### Standalone Audit Command

```bash
# Basic audit
skene-growth audit .

# Save JSON report
skene-growth audit . -o audit-report.json

# Exclude folders
skene-growth audit . --exclude tests --exclude vendor

# JSON output only
skene-growth audit . --json
```

### Integrated with Analyze Command

The onboarding audit automatically runs as a fallback when no API key is provided:

```bash
# This will run onboarding audit if no API key is set
skene-growth analyze .

# Or explicitly request it
skene-growth analyze . --onboarding-audit
```

## Patterns Detected

The audit scans for 50 PLG onboarding anti-patterns across 5 categories:

### Core Onboarding (P01-P20)

**Critical Issues:**
- **P01**: Immediate Value Absence - Empty dashboard without demo data
- **P03**: Empty Canvas - Missing seed/demo data files
- **P07**: No Shadow Environment - Missing demo database layer
- **P10**: Aha Moment Delay - Value hidden behind multiple interactions
- **P20**: Pre-Value Authentication - Auth required before product preview

**High Friction:**
- **P02**: Configuration Upfront - API keys requested before feature usage
- **P06**: Static Tutorial Dependency - Blocking modals/tutorials
- **P08**: Contextless Data Collection - Data collected before needed
- **P12**: No Progress Persistence - Onboarding state not saved
- **P15**: Value-Gated Configuration - Features locked behind integration setup
- **P17**: Explanation Over Demonstration - Text-heavy onboarding
- **P19**: Onboarding Drift Detection - No analytics instrumentation

**Quick Wins:**
- **P04**: Linear Onboarding Lock - Forced sequential steps
- **P05**: Feature Discovery Delay - Core features hidden deep
- **P09**: Single Path Onboarding - No personalization
- **P11**: Irreversible Early Decisions - Permanent choices
- **P13**: Tooltip Overload - Too many tooltips
- **P14**: Sandbox Without Context - Generic demo data
- **P16**: No Micro-Commitments - Missing progress tracking
- **P18**: No Contextual Help - Complex forms without guidance

### Signup & Friction (P21-P29)

- **P21**: Password Strength Overkill - Excessive password requirements
- **P22**: Email Verification Blocker - Email verification blocks access
- **P23**: Multi-Step Signup Overload - Too many signup steps
- **P24**: No Social Login - Missing OAuth options
- **P25**: CAPTCHA on Signup - CAPTCHA adds friction
- **P26**: Credit Card Before Trial - Payment required for trial
- **P27**: No Guest Checkout - Can't try without account
- **P28**: Forced Profile Photo - Mandatory avatar upload
- **P29**: Newsletter Auto-Optin - Pre-checked marketing consent

### UX & Feedback (P30-P38)

- **P30**: No Keyboard Shortcuts - Missing power user features
- **P31**: Loading State Absence - No async operation feedback
- **P32**: Error Message Hostility - Unfriendly error messages
- **P33**: Success Feedback Silence - Missing success confirmations
- **P34**: No Undo Capability - Can't reverse destructive actions
- **P35**: Delete Confirmation Missing - No confirmation dialogs
- **P36**: Session Timeout Aggressive - Short session timeouts
- **P37**: Notification Permission Spam - Early permission requests
- **P38**: Location Permission Upfront - Location access before needed

### Performance (P39-P44)

- **P39**: Mobile Responsiveness Broken - No responsive patterns
- **P40**: Slow Page Transitions - No link prefetching
- **P41**: Large Bundle Size - No code splitting
- **P42**: No Offline Support - Missing service worker/PWA
- **P43**: Third-Party Script Bloat - Too many external scripts
- **P44**: Unoptimized Images - No image optimization

### Growth Mechanics (P45-P50)

- **P45**: Missing Meta Tags - No social sharing meta tags
- **P46**: No Referral Mechanism - Missing referral system
- **P47**: Share Buttons Missing - No social share functionality
- **P48**: Invite Flow Complex - Overly complex team invites
- **P49**: No Exit Intent Capture - No exit intent handling
- **P50**: Pricing Page Hidden - Pricing not discoverable

## Scoring

The audit generates a Progressive Revelation Score (0-100):

- **82+ (Best-in-class PLG)**: Excellent onboarding experience
- **65-81 (Good)**: Solid foundation with room for improvement
- **50-64 (Needs Work)**: Multiple friction points to address
- **Below 50 (Critical)**: Significant barriers to user activation

Score calculation:
```
Score = 100 - (Critical × 15) - (High × 8) - (Medium × 4)
```

## Output Formats

### Visual Report (Default)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                                                                              ║
║                   █▀█ █▄ █ █▄▄ █▀█ ▄▀█ █▀█ █▀▄ █ █▄ █ █▀▀                    ║
║                   █▄█ █ ▀█ █▄█ █▄█ █▀█ █▀▄ █▄▀ █ █ ▀█ █▄█                    ║
║                                                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

                   Free heuristics scan (no API key)                  
        For advanced AI analytics: skene-growth analyze --api-key YOUR_KEY      

REPORT                   ONBOARDING AUDIT
────────────────────────────────────────────────────────────────────────────────
SCAN                     4 ISSUES DETECTED
────────────────────────────────────────────────────────────────────────────────
SCORE                    58/100
────────────────────────────────────────────────────────────────────────────────
STATUS                   NEEDS IMPROVEMENT
────────────────────────────────────────────────────────────────────────────────
CRITICAL                 2 CRITICAL ISSUES
                         → NO SEED/DEMO DATA FILES DETECTED
────────────────────────────────────────────────────────────────────────────────
HIGH FRICTION            1 HIGH FRICTION POINTS
                         → NO ANALYTICS TRACKING DETECTED FOR ONBOARDING
────────────────────────────────────────────────────────────────────────────────
QUICK WINS               1 OPPORTUNITIES
                         → NO MICRO-COMMITMENT TRACKING DETECTED
────────────────────────────────────────────────────────────────────────────────
OUTCOME                  MULTIPLE FRICTION POINTS
                         FIX CRITICAL + HIGH ISSUES
                         REBUILD ONBOARDING FLOW
────────────────────────────────────────────────────────────────────────────────

================================================================================

                               DETECTED PATTERNS                                

================================================================================

▼ CRITICAL ISSUES (2)

  [P03] No seed/demo data files detected
  → New users will see empty state instead of live demo environment

  [P07] No shadow/demo database environment detected
  → Users need live simulation environment for immediate value experience

────────────────────────────────────────────────────────────────────────────────

▼ HIGH ISSUES (1)

  [P19] No analytics tracking detected for onboarding optimization
  → Cannot measure time-to-value or identify drop-off points without
  → instrumentation

────────────────────────────────────────────────────────────────────────────────

▼ MEDIUM ISSUES (1)

  [P16] No micro-commitment tracking detected
  → Small wins create momentum - add granular progress indicators

────────────────────────────────────────────────────────────────────────────────
```

### JSON Report

```json
{
  "scan_type": "onboarding_audit",
  "total_issues": 4,
  "issues": [
    {
      "id": "P03",
      "severity": "CRITICAL",
      "message": "No seed/demo data files detected",
      "file": "",
      "details": "New users will see empty state instead of live demo environment"
    }
  ]
}
```

## How It Works

The scanner uses regex patterns and file tree analysis to detect anti-patterns:

1. **File Discovery**: Scans codebase for relevant files (components, routes, configs)
2. **Pattern Matching**: Applies regex patterns to detect common issues
3. **Heuristic Analysis**: Uses file structure and code patterns to infer problems
4. **Severity Classification**: Groups issues by impact on user activation

### Ignored Directories

The scanner automatically ignores common non-production directories:
- `node_modules`, `dist`, `build`, `.next`
- `__tests__`, `test`, `tests`, `coverage`
- `__pycache__`, `venv`, `.venv`, `vendor`

## Integration

The onboarding scanner is integrated into the skene-growth CLI and can be used:

1. As a standalone audit tool
2. As a fallback when no API key is provided
3. As an explicit option in the analyze command

## Limitations

This audit uses heuristics and pattern matching:

- May have false positives (detects patterns that aren't actually issues)
- May miss patterns that use non-standard naming or structure
- Cannot understand business logic or user intent
- Works best with standard web app architectures (React, Vue, Next.js, etc.)

For deeper analysis, use the full LLM-powered `analyze` command with an API key.

## Examples

### Example 1: Clean Codebase

```bash
$ skene-growth audit ./my-saas-app

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                                                                              ║
║                   █▀█ █▄ █ █▄▄ █▀█ ▄▀█ █▀█ █▀▄ █ █▄ █ █▀▀                    ║
║                   █▄█ █ ▀█ █▄█ █▄█ █▀█ █▀▄ █▄▀ █ █ ▀█ █▄█                    ║
║                                                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

                   Free heuristics scan (no API key)                  
        For advanced AI analytics: skene-growth analyze --api-key YOUR_KEY      

REPORT                   ONBOARDING AUDIT
────────────────────────────────────────────────────────────────────────────────
SCAN                     1 ISSUES DETECTED
────────────────────────────────────────────────────────────────────────────────
SCORE                    96/100
────────────────────────────────────────────────────────────────────────────────
STATUS                   BEST-IN-CLASS PLG
────────────────────────────────────────────────────────────────────────────────
CRITICAL                 NO CRITICAL ISSUES
────────────────────────────────────────────────────────────────────────────────
HIGH FRICTION            NO HIGH FRICTION
────────────────────────────────────────────────────────────────────────────────
QUICK WINS               1 OPPORTUNITIES
                         → NO ANALYTICS INSTRUMENTATION
────────────────────────────────────────────────────────────────────────────────
OUTCOME                  EXCELLENT ONBOARDING
                         MINOR OPTIMIZATIONS
                         MEASURE TIME-TO-VALUE
────────────────────────────────────────────────────────────────────────────────

================================================================================

                               DETECTED PATTERNS                                

================================================================================

▼ MEDIUM ISSUES (1)

  [P19] No analytics tracking detected for onboarding optimization
  → Cannot measure time-to-value or identify drop-off points without
  → instrumentation

────────────────────────────────────────────────────────────────────────────────
```

### Example 2: Multiple Issues

```bash
$ skene-growth audit ./legacy-app -o report.json

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                                                                              ║
║                   █▀█ █▄ █ █▄▄ █▀█ ▄▀█ █▀█ █▀▄ █ █▄ █ █▀▀                    ║
║                   █▄█ █ ▀█ █▄█ █▄█ █▀█ █▀▄ █▄▀ █ █ ▀█ █▄█                    ║
║                                                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

                   Free heuristics scan (no API key)                  
        For advanced AI analytics: skene-growth analyze --api-key YOUR_KEY      

REPORT                   ONBOARDING AUDIT
────────────────────────────────────────────────────────────────────────────────
SCAN                     11 ISSUES DETECTED
────────────────────────────────────────────────────────────────────────────────
SCORE                    11/100
────────────────────────────────────────────────────────────────────────────────
STATUS                   CRITICAL GAPS
────────────────────────────────────────────────────────────────────────────────
CRITICAL                 3 CRITICAL ISSUES
                         → EMPTY STATE DETECTED WITHOUT DEMO/SAMPLE DATA
────────────────────────────────────────────────────────────────────────────────
HIGH FRICTION            5 HIGH FRICTION POINTS
                         → CONFIGURATION REQUESTED UPFRONT BEFORE USAGE
────────────────────────────────────────────────────────────────────────────────
QUICK WINS               3 OPPORTUNITIES
                         → LINEAR ONBOARDING FLOW WITH NO SKIP OPTION
────────────────────────────────────────────────────────────────────────────────
OUTCOME                  CRITICAL BARRIERS DETECTED
                         COMPLETE ONBOARDING REDESIGN
                         IMPLEMENT IMMEDIATE VALUE
────────────────────────────────────────────────────────────────────────────────

================================================================================

                               DETECTED PATTERNS                                

================================================================================

▼ CRITICAL ISSUES (3)

  [P01] Empty state detected without demo/sample data
  → Users see blank canvas on first load - no immediate value

  [P07] No shadow/demo database environment detected
  → Users need live simulation environment for immediate value experience

  [P20] Authentication required before product preview
  → Let users see value before asking for signup commitment

────────────────────────────────────────────────────────────────────────────────

▼ HIGH ISSUES (5)

  [P02] Configuration requested upfront before feature usage
  → Config fields found: api[_\s]*key, webhook[_\s]*url, secret[_\s]*key

  [P06] Blocking tutorial/modal detected
  → Users must consume passive content before interaction

  [P17] 843 chars of explanation vs 2 interactions
  → Show, don't tell - replace text with interactive demos

  ... and 2 more

────────────────────────────────────────────────────────────────────────────────

▼ MEDIUM ISSUES (3)

  [P04] Linear onboarding flow with no skip option detected
  → Users forced through sequential steps without exploration freedom

  [P13] 8 tooltips detected on single screen
  → Cognitive overload - too many competing help messages

  ... and 1 more

────────────────────────────────────────────────────────────────────────────────

JSON report saved to: report.json
```

## Best Practices

1. **Run Early**: Use this audit in the early stages of development
2. **CI Integration**: Add to CI/CD pipeline to catch regressions
3. **Compare Over Time**: Track score improvements across releases
4. **Combine with Analytics**: Validate findings with real user data
5. **Iterate**: Fix critical issues first, then work down severity levels

## Related

- [Full Growth Analysis](../README.md#analyze) - LLM-powered deep analysis
- [Growth Planning](../README.md#plan) - Generate growth strategies
- [Progressive Revelation Principles](https://www.nngroup.com/articles/progressive-disclosure/)
