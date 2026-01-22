# Growth Loops Implementation Plan

*Generated on 2026-01-22 13:09:10*
*Based on: growth-manifest.json, growth-objectives.md, daily logs*

---

## Loop 1: User Onboarding Tutorial

**PLG Stage:** activation
**Goal:** Improve user activation and adoption by guiding new users through the tool's features and benefits.

### Why This Loop?
The 'User Onboarding Tutorial' directly addresses the 'User Onboarding Tutorial' GTM Gap (high priority) and low 'successful_plan_generation' metric (40%, below the target of 60%). By providing a guided tutorial, new users will quickly understand how to use the tool to generate growth plans, increasing the likelihood of successful plan generation and subsequent WAU (adoption). This loop prioritizes activating users and helping them quickly derive value.

### What It Does

### Implementation Steps
1. Step 1: Create a 'tutorial' subcommand using Typer that guides the user through the basic commands and features of skene-growth (e.g., 'skene-growth tutorial').
2. Step 2: Implement interactive prompts within the tutorial, using Typer's features to guide the user step-by-step through generating a growth objectives file, creating a plan, and running a daily log.
3. Step 3: Incorporate docstrings and help messages within the Typer CLI to provide context and explanations for each command and option during the tutorial. Also integrate the 'Syntax Highlighter' loop for contextual help and documentation search within the tutorial flow.
4. Step 4: Track tutorial completion rates. Implement a mechanism to detect if a user has completed the tutorial or skipped certain steps. This data can be used to improve the tutorial's effectiveness.

### Success Metrics
- Tutorial Completion Rate: Percentage of users who start the tutorial and complete all steps. Measure this by tracking events within the CLI.
- Successful Plan Generation Rate (post-tutorial): Percentage of users who successfully generate a growth plan after completing the tutorial. Compare this rate against users who did not complete the tutorial.
- Time to First Plan Generation: Measure the time taken for a user to generate their first growth plan after installing the tool. This should decrease with an effective tutorial.

---

## Loop 2: Usage Analytics

**PLG Stage:** adoption
**Goal:** 

### Why This Loop?
While 'User Onboarding Tutorial' addressed activation, we need to focus on adoption. The current Weekly Active Users (WAU) is only at 40%, significantly below the target of 60%. Implementing usage analytics directly addresses the 'Usage Analytics' GTM Gap (high priority) and provides the data necessary to understand why users aren't actively using the tool. This loop fills the knowledge gap, enabling data-driven decisions for improvement.

### What It Does

### Implementation Steps
1. Step 1: Install and configure a Python library for CLI usage tracking (e.g., 'cli-analytics' or similar).
2. Step 2: Implement event tracking for key command executions (e.g., 'plan' command, 'objectives' command) including successful execution and errors.
3. Step 3: Implement event tracking for the frequency of command usage (e.g. track the number of times 'plan' command is used per week).
4. Step 4: Store collected analytics data in a local database or a cloud-based analytics platform.
5. Step 5: Create a command (e.g., 'skene-growth analytics') to allow users to opt-in or opt-out of usage data collection. Ensure that data collection is opt-in or complies with privacy regulations.

### Success Metrics
- Metric 1: Number of users who opt-in to usage analytics. Measured by querying the analytics database or platform.
- Metric 2: Command usage frequency. Measured by tracking the number of times each command is executed per week.

---

## Loop 3: Community Forum/Support

**PLG Stage:** retention
**Goal:** Enhance user engagement and build a community around the tool.

### Why This Loop?
The previous two loops focused on activation and adoption. Now, we need to address retention, which is already at 80% but can be improved further. Implementing a 'Community Forum/Support' directly addresses the 'Community Forum/Support' GTM Gap (medium priority) and fosters a sense of belonging and continuous learning around the tool. This will encourage users to stick around and actively participate, contributing to long-term user retention. It also provides a valuable feedback loop for continuous product improvement.

### What It Does

### Implementation Steps
1. Step 1: Integrate a discussion platform: Choose an existing discussion platform (e.g., Discourse, GitHub Discussions) or develop a simple forum using Typer and Python.
2. Step 2: Seed the forum with content: Create initial threads covering common use cases, FAQs, and best practices for using 'skene-growth'.
3. Step 3: Actively moderate and participate: Dedicate time to answer questions, provide support, and engage with user feedback in the forum.
4. Step 4: Link to the forum from the CLI tool: Add a command or message within the CLI tool to direct users to the community forum for support and discussions (e.g., a 'support' command that opens the forum in a browser).
5. Step 5: Gamify participation: Implement a simple system for rewarding active contributors in the forum (e.g., badges, recognition).

### Success Metrics
- Metric 1: Forum Activity: Measure the number of active users, posts, threads, and replies in the forum weekly/monthly. This indicates user engagement and participation.
- Metric 2: User Retention Rate (Long-Term): Track the long-term user retention rate (e.g., 90-day retention) after implementing the community forum. This measures the impact of the forum on user stickiness.

---

*Growth loops selected by skene-growth using LLM analysis.*