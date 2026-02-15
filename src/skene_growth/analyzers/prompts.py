"""
Prompt templates for PLG analysis.

These are basic, open-source prompts designed for general use.
Premium prompts with higher quality output can override these
in closed-source implementations.
"""

# Tech Stack Detection Prompt
TECH_STACK_PROMPT = """
Analyze the provided files (configuration files and source files) to detect the technology stack used in this project.

IMPORTANT: When determining the **Language**, prioritize actual source files over configuration files.
For example, if you see Python source files (.py) but only a package.json config file,
the language is Python, not JavaScript.
Look at file extensions and code syntax in source files to determine the primary language.

Focus on identifying:
1. **Framework**: The primary web/app framework (e.g., Next.js, FastAPI, Rails, Django)
2. **Language**: The main programming language (e.g., Python, TypeScript, Go) - DETERMINE FROM SOURCE FILES,
   not just config files
3. **Database**: Database technology if detectable (e.g., PostgreSQL, MongoDB, Supabase, Redis)
4. **Auth**: Authentication method or library (e.g., JWT, OAuth, NextAuth, Clerk)
5. **Deployment**: Deployment platform or method (e.g., Vercel, AWS, Docker, Kubernetes, Netlify)
6. **Package Manager**: Package manager used (e.g., npm, yarn, pnpm, poetry, cargo)
7. **Hosting**: Hosting platform (e.g., vercel, netlify, aws, heroku, render)
8. **Billing**: Primary payment/billing provider (e.g., stripe, paddle, lemonsqueezy) - return lowercase
9. **Email**: Email service provider (e.g., resend, sendgrid, postmark, mailgun) - return lowercase
10. **Analytics**: Analytics provider (e.g., posthog, mixpanel, amplitude, segment) - return lowercase
11. **Services**: Other third-party services and integrations used in the project

For **Billing**, look for:
- Package.json dependencies: "stripe", "@paddle/paddle-js", "lemonsqueezy"
- Import statements: import Stripe from 'stripe', import Paddle
- Environment variables: STRIPE_API_KEY, PADDLE_API_KEY

For **Email**, look for:
- Dependencies: "resend", "@sendgrid/mail", "postmark", "nodemailer"
- Import statements: import { Resend }, import sgMail
- Environment variables: RESEND_API_KEY, SENDGRID_API_KEY

For **Analytics**, look for:
- Dependencies: "posthog-js", "mixpanel", "@amplitude/analytics-browser"
- Import statements: import posthog, import mixpanel
- Environment variables: POSTHOG_API_KEY, MIXPANEL_TOKEN

For **Services**, look for other SaaS integrations:
- Monitoring: Sentry, DataDog, New Relic, LogRocket
- Communication: Twilio, Plivo
- Search: Algolia, Elasticsearch, Typesense
- Storage: AWS S3, Cloudflare R2, Cloudinary
- Other integrations

Return your analysis as JSON matching this structure:
{
    "framework": "string or null",
    "language": "string (required)",
    "database": "string or null",
    "auth": "string or null",
    "deployment": "string or null",
    "package_manager": "string or null",
    "hosting": "string or null",
    "billing": "string or null (lowercase: 'stripe', 'paddle', etc.)",
    "email": "string or null (lowercase: 'resend', 'sendgrid', etc.)",
    "analytics": "string or null (lowercase: 'posthog', 'mixpanel', etc.)",
    "services": ["array of other service names"]
}

Be conservative - only include values you're confident about. Use null for uncertain fields.
Return an empty array for services if none are detected.
For billing, email, and analytics, return only the provider name in lowercase (e.g., "stripe" not "Stripe API").
"""

# Growth Hub Detection Prompt
GROWTH_HUB_PROMPT = """
Analyze the provided source files and identify features with growth potential.

A "growth hub" is a feature or area of the codebase that:
- Enables viral growth (sharing, invitations, referrals)
- Drives user engagement (notifications, gamification, progress tracking)
- Facilitates user onboarding (tutorials, tooltips, guided flows)
- Supports monetization (payments, subscriptions, upgrades)
- Enables data-driven decisions (analytics, dashboards, reporting)

For each growth hub you identify, provide:
1. **feature_name**: A clear name for the feature
2. **file_path**: The primary file where this feature is implemented
3. **detected_intent**: What growth purpose does this feature serve?
4. **confidence_score**: How confident are you (0.0 to 1.0)?
5. **entry_point**: URL path or function name users interact with (if identifiable)
6. **growth_potential**: List of specific improvements that could boost growth

Return your analysis as a JSON array of growth hubs.
Focus on quality over quantity - identify the most impactful growth opportunities.
"""

# Manifest Generation Prompt
MANIFEST_PROMPT = """
Generate a complete growth manifest by combining the analysis results.

You have been provided with:
- Tech stack analysis (detected technologies)
- Growth hub analysis (features with growth potential)

Your task is to:
1. Create a cohesive project summary
2. Include the tech stack and growth hubs from the analysis
3. Identify GTM (Go-to-Market) gaps - missing features that could drive growth

For GTM gaps, consider what's missing:
- User onboarding flows
- Viral/sharing mechanisms
- Analytics and insights
- Monetization capabilities
- Engagement features
- Community features

Return a complete growth manifest as JSON with:
- project_name: Inferred from the codebase
- description: Brief project description
- tech_stack: From the tech stack analysis
- growth_hubs: From the growth hub analysis
- gtm_gaps: Your identified gaps with priority (high/medium/low)
"""

# Product Overview Extraction Prompt
PRODUCT_OVERVIEW_PROMPT = """
Analyze the provided documentation files to extract product overview information.

Focus on identifying:
1. **Tagline**: A short one-liner (under 15 words) that captures what the product does
2. **Value Proposition**: What problem does this solve? Why should someone use it? (2-3 sentences)
3. **Target Audience**: Who is this product for? (e.g., developers, marketers, enterprises)

Look for this information in:
- README.md introductions and first paragraphs
- Package description fields (package.json description, pyproject.toml)
- About/Overview sections
- Marketing copy in documentation

Return your analysis as JSON:
{
    "tagline": "string or null",
    "value_proposition": "string or null",
    "target_audience": "string or null"
}

Be concise but informative. Write from the perspective of explaining the product to someone new.
Use null for fields you cannot confidently determine from the provided files.
"""

# Features Documentation Prompt
FEATURES_PROMPT = """
Analyze the source files to document user-facing features.

For each major feature, provide:
1. **name**: Human-readable feature name (not code identifiers)
2. **description**: User-facing description of what it does (1-2 sentences, non-technical)
3. **file_path**: Primary implementation file
4. **usage_example**: Short code snippet or usage example (if identifiable)
5. **category**: Feature category (e.g., "Authentication", "API", "Data Management", "UI")

Focus on:
- Features users interact with directly
- Core functionality, not internal utilities or helpers
- Clear, non-technical descriptions where possible
- The value each feature provides to users

Return as a JSON array of features:
[
    {
        "name": "Feature Name",
        "description": "What this feature does for users",
        "file_path": "path/to/file.py",
        "usage_example": "optional code example",
        "category": "Category"
    }
]

Prioritize the most important 5-10 features. Quality over quantity.
"""

# Documentation Manifest Generation Prompt
DOCS_MANIFEST_PROMPT = """
Generate a complete documentation manifest by combining all analysis results.

You have been provided with:
- Tech stack analysis (detected technologies)
- Product overview (tagline, value proposition, target audience)
- Features documentation (user-facing feature descriptions)
- Growth hub analysis (features with growth potential)

Your task is to:
1. Create a cohesive DocsManifest combining all sections
2. Infer a project_name from the codebase structure or package files
3. Write a brief description summarizing the project
4. Include all provided analysis data
5. Identify GTM (Go-to-Market) gaps - missing features that could drive growth

For GTM gaps, consider what's missing:
- User onboarding flows
- Viral/sharing mechanisms
- Analytics and insights
- Monetization capabilities
- Engagement features

Return a complete manifest as JSON with:
- version: "2.0"
- project_name: Inferred from the codebase
- description: Brief project description
- tech_stack: From the tech stack analysis
- product_overview: From the product overview analysis
- features: From the features documentation
- growth_hubs: From the growth hub analysis
- gtm_gaps: Your identified gaps with priority (high/medium/low)
"""

# Technical Debt Analysis Prompt
TECH_DEBT_PROMPT = """
Analyze the provided source code for technical debt indicators and code quality issues.

For each code smell or issue you identify, provide:
1. **name**: Type of code smell (e.g., "Long Function", "Deep Nesting", "Duplicate Code")
2. **severity**: high | medium | low (based on impact and urgency)
3. **file_path**: The file where this issue exists
4. **line_number**: Line number where issue starts (null if not specific)
5. **description**: Clear explanation of the issue and why it matters
6. **refactoring_effort**: quick | moderate | major (estimated effort to fix)
7. **auto_fixable**: true if an automated agent can safely fix this, false for architectural changes

## CODE SMELLS TO DETECT:

**Complexity Issues:**
- Long functions (>50 lines)
- Deep nesting (>4 levels)
- High cyclomatic complexity (>10)
- Too many parameters (>5)
- Large classes (>500 lines)

**Duplication:**
- Duplicate code blocks
- Repeated logic patterns
- Similar functions that could be abstracted

**Maintainability:**
- Magic strings and numbers
- Unclear variable names
- Missing error handling
- Commented-out code
- TODO/FIXME comments

**Architecture:**
- Tight coupling between modules
- Circular dependencies
- Layer boundary violations
- God objects (classes doing too much)

## DEPENDENCY HEALTH:

Check package.json, requirements.txt, Cargo.toml for:
- Outdated packages (check for version patterns)
- Known security vulnerabilities (CVEs)
- Unmaintained dependencies (no updates >2 years)
- Multiple versions of same package

## TESTING GAPS:

Identify:
- Critical code paths without tests
- Low test coverage areas
- Missing integration tests
- Missing edge case tests

## AUTO-FIXABLE CRITERIA:

Mark auto_fixable=true for:
- Formatting issues
- Unused imports
- Simple variable renames
- Magic number extraction
- Dead code removal

Mark auto_fixable=false for:
- Architectural changes
- Complex refactoring
- Breaking API changes
- Logic restructuring

Return as JSON:
{
  "total_debt_score": 0-100,  // Higher = more debt
  "code_smells": [
    {
      "name": "Long Function",
      "severity": "high",
      "file_path": "src/auth.ts",
      "line_number": 42,
      "description": "authenticateUser function is 120 lines...",
      "refactoring_effort": "moderate",
      "auto_fixable": false
    }
  ],
  "architecture_violations": [
    {
      "type": "Circular Dependency",
      "description": "Module A imports B, B imports A",
      "files": ["src/a.ts", "src/b.ts"]
    }
  ],
  "dependency_health": {
    "outdated_count": 5,
    "vulnerabilities": 2,
    "unmaintained": ["package-name@1.0.0"]
  },
  "test_coverage_gaps": [
    "src/payment.ts: No tests for refund logic",
    "src/auth.ts: Missing edge case tests"
  ],
  "refactoring_priority": [
    "src/auth.ts",
    "src/payment.ts"
  ]
}

Focus on high-impact issues. Be specific with file paths and line numbers.
"""

# Dead Code Detection Prompt
DEAD_CODE_PROMPT = """
Analyze the provided source code to identify unused, unreachable, or dead code.

For each finding, provide:
1. **file_path**: The file containing dead code
2. **symbol_name**: Name of the unused function/class/variable
3. **symbol_type**: function | class | variable | import
4. **lines**: Tuple of [start_line, end_line]
5. **confidence**: 0.0-1.0 (how confident are you this is truly unused?)
6. **reason**: Why you believe this code is dead
7. **suggestion**: What to do about it
8. **auto_removable**: true if safe to auto-delete, false if needs review

## DETECTION CRITERIA:

**Unused Functions/Classes:**
- Defined but never called/instantiated
- Not exported or used externally
- Private methods with no callers
- Helper functions with no references

**Unused Variables:**
- Assigned but never read
- Constants that are never used
- Parameters that are never accessed

**Unused Imports:**
- Imported but never referenced in code
- Import * that imports unused names
- Duplicate imports

**Unreachable Code:**
- Code after return/throw statements
- Unreachable branches (if false, etc.)
- Dead catch blocks

**Orphaned Functions:**
- Functions in files that are never imported
- Test helpers that are never used
- Utility functions with no callers

## CONFIDENCE SCORING:

**High confidence (>0.9):**
- Clear AST evidence (no references found)
- Simple, self-contained symbols
- No dynamic imports/reflection

**Medium confidence (0.6-0.9):**
- Appears unused but could have dynamic usage
- Possibly used in tests
- May be part of API surface

**Low confidence (<0.6):**
- Could be used via string/reflection
- Exported from package
- Public API that might be external

## AUTO-REMOVABLE CRITERIA:

Mark auto_removable=true for:
- Unused imports with confidence >0.9
- Private functions/variables with no callers
- Clearly unreachable code

Mark auto_removable=false for:
- Exported symbols (public API)
- Functions that might be called dynamically
- Code with confidence <0.9

Return as JSON:
{
  "total_unreachable": 15,
  "unreachable_code": [
    {
      "file_path": "src/auth.ts",
      "symbol_name": "validateToken",
      "symbol_type": "function",
      "lines": [42, 55],
      "confidence": 0.95,
      "reason": "Function defined but never called in codebase",
      "suggestion": "Remove function or add tests if needed",
      "auto_removable": true
    }
  ],
  "unused_imports": [
    {
      "file_path": "src/utils.ts",
      "symbol_name": "lodash",
      "symbol_type": "import",
      "lines": [3, 3],
      "confidence": 1.0,
      "reason": "Imported but never used",
      "suggestion": "Remove import statement",
      "auto_removable": true
    }
  ],
  "unused_exports": [],
  "orphaned_functions": [],
  "estimated_lines_removed": 125
}

Be conservative with confidence scores. False positives are worse than false negatives.
"""
