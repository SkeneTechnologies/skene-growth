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
3. **Database**: Database technology if detectable (e.g., PostgreSQL, MongoDB, Redis)
4. **Auth**: Authentication method or library (e.g., JWT, OAuth, NextAuth, Clerk)
5. **Deployment**: Deployment platform or method (e.g., Vercel, AWS, Docker, Kubernetes, Netlify)
6. **Package Manager**: Package manager used (e.g., npm, yarn, poetry, cargo)
7. **Services**: Third-party services and integrations used in the project

For **Services**, look for dependencies and environment variables indicating:
- Payment processors: Stripe, PayPal, Paddle, LemonSqueezy
- Email services: SendGrid, Mailgun, Postmark, Resend
- Analytics: Segment, Mixpanel, Amplitude, PostHog
- Monitoring: Sentry, DataDog, New Relic, LogRocket
- Communication: Twilio, Plivo
- Search: Algolia, Elasticsearch, Typesense
- Storage: AWS S3, Cloudflare R2, Cloudinary
- Other SaaS integrations

Return your analysis as JSON matching this structure:
{
    "framework": "string or null",
    "language": "string (required)",
    "database": "string or null",
    "auth": "string or null",
    "deployment": "string or null",
    "package_manager": "string or null",
    "services": ["array of service names"]
}

Be conservative - only include values you're confident about. Use null for uncertain fields.
Return an empty array for services if none are detected.
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
