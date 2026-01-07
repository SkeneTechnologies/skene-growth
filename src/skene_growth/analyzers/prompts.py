"""
Prompt templates for PLG analysis.

These are basic, open-source prompts designed for general use.
Premium prompts with higher quality output can override these
in closed-source implementations.
"""

# Tech Stack Detection Prompt
TECH_STACK_PROMPT = """
Analyze the provided configuration files and detect the technology stack used in this project.

Focus on identifying:
1. **Framework**: The primary web/app framework (e.g., Next.js, FastAPI, Rails, Django)
2. **Language**: The main programming language (e.g., Python, TypeScript, Go)
3. **Database**: Database technology if detectable (e.g., PostgreSQL, MongoDB, Redis)
4. **Auth**: Authentication method or library (e.g., JWT, OAuth, NextAuth, Clerk)
5. **Deployment**: Deployment platform or method (e.g., Vercel, AWS, Docker, Kubernetes)
6. **Package Manager**: Package manager used (e.g., npm, yarn, poetry, cargo)

Return your analysis as JSON matching this structure:
{
    "framework": "string or null",
    "language": "string (required)",
    "database": "string or null",
    "auth": "string or null",
    "deployment": "string or null",
    "package_manager": "string or null"
}

Be conservative - only include values you're confident about. Use null for uncertain fields.
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
