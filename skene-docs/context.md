# Skene - Project Context

> Auto-generated context document for AI/LLM consumption
> Generated: 2024-12-19 10:30:00

## Overview

AI-powered Product-Led Growth orchestration platform with deterministic state machines that replaces fragmented SaaS tools with a unified, context-aware fabric for business operations.

## Technology Stack

| Category | Technology |
|----------|------------|
| Language | TypeScript |
| Package Manager | pnpm |
| Services | Stripe, HubSpot, Salesforce, Intercom, Paddle, Chargebee, Braintree, Resend |

## Growth Hubs

The following features have been identified as having growth potential:

### Subscription Management & Billing Gateway

- **File**: `packages/billing-gateway/src/gateway.ts`
- **Intent**: Supports monetization through subscription management, payment processing, and revenue optimization
- **Confidence**: 95.0%
- **Entry Point**: `BillingGateway class methods: subscribe(), cancel(), charge()`- **Growth Potential**:
  - Add pricing experimentation and A/B testing for subscription plans
  - Implement dunning management for failed payments to reduce churn
  - Add upgrade prompts with usage-based triggers
  - Create subscription analytics dashboard for MRR tracking
  - Implement referral discounts and promotional pricing
  - Add seat-based billing for team expansion
  - Integrate with analytics to track conversion from trial to paid

### Adaptive Billing Engine

- **File**: `packages/billing-gateway/src/adaptive-billing.ts`
- **Intent**: Enables data-driven billing decisions through automatic pattern detection and configuration
- **Confidence**: 90.0%
- **Entry Point**: `AdaptiveBillingEngine.configureFromManifest()`- **Growth Potential**:
  - Add real-time billing optimization based on user behavior
  - Implement predictive pricing models using ML
  - Create automated plan recommendations for users
  - Add usage-based billing triggers for overages
  - Implement dynamic pricing based on value delivered
  - Add cohort-based billing strategies
  - Create billing health score to predict churn risk

### Subscription Tier Gating System

- **File**: `packages/subscription-gating/src/gate.ts`
- **Intent**: Drives user engagement and monetization through feature restrictions and upgrade prompts
- **Confidence**: 92.0%
- **Entry Point**: `SubscriptionGate.checkAccess(), triggerUpgradePrompt()`- **Growth Potential**:
  - Add progressive disclosure of premium features
  - Implement soft paywalls with usage previews
  - Create personalized upgrade recommendations
  - Add social proof in upgrade prompts (user counts, testimonials)
  - Implement trial extensions based on engagement
  - Add feature unlock celebrations to increase perceived value
  - Create urgency through limited-time upgrade offers

### Gamification Engine

- **File**: `packages/gamification/src/engine.ts`
- **Intent**: Drives user engagement through achievements, levels, and progress tracking
- **Confidence**: 88.0%
- **Entry Point**: `GamificationEngine.awardXP(), checkAchievements()`- **Growth Potential**:
  - Add leaderboards to drive competitive engagement
  - Implement sharing achievements on social media
  - Create team-based challenges for viral growth
  - Add milestone rewards that encourage feature adoption
  - Implement streaks to build daily usage habits
  - Create badge collections that showcase user expertise
  - Add referral-based achievements to drive invitations

### Points and Badge Systems

- **File**: `packages/gamification/src/points.ts`
- **Intent**: Facilitates user onboarding and engagement through reward systems
- **Confidence**: 85.0%
- **Entry Point**: `PointSystem.awardForAction(), BadgeSystem.awardBadge()`- **Growth Potential**:
  - Add point redemption marketplace for premium features
  - Implement badge sharing on LinkedIn/Twitter for viral growth
  - Create point-based referral rewards system
  - Add seasonal challenges and limited-time badges
  - Implement team point pooling for enterprise accounts
  - Create badge-gated content to drive engagement
  - Add point multipliers for consecutive usage days

### Journey Tracker

- **File**: `packages/lifecycle-tracker/src/tracker.ts`
- **Intent**: Enables data-driven decisions through user journey analysis and segmentation
- **Confidence**: 87.0%
- **Entry Point**: `JourneyTracker.recordStateChange(), query()`- **Growth Potential**:
  - Add predictive churn scoring based on journey patterns
  - Implement automated intervention triggers for at-risk users
  - Create personalized onboarding flows based on user segments
  - Add journey-based email campaigns
  - Implement cohort analysis for retention optimization
  - Create success path recommendations for new users
  - Add journey visualization dashboard for product teams

### Trigger Engine

- **File**: `packages/trigger-engine/src/engine.ts`
- **Intent**: Drives user engagement through proactive recommendations and notifications
- **Confidence**: 90.0%
- **Entry Point**: `TriggerEngine.evaluate(), evaluateOne()`- **Growth Potential**:
  - Add intelligent timing optimization for notifications
  - Implement A/B testing for trigger messages
  - Create cross-platform trigger delivery (email, push, in-app)
  - Add machine learning for trigger personalization
  - Implement trigger sequences for complex user flows
  - Create trigger analytics dashboard for optimization
  - Add collaborative filtering for recommendation triggers

### Skills Marketplace Integration

- **File**: `packages/skills/stripe/src/index.ts`
- **Intent**: Supports monetization through payment processing and subscription management integrations
- **Confidence**: 80.0%
- **Entry Point**: `StripeSkill.executeSkill(), various payment provider skills`- **Growth Potential**:
  - Add skill usage analytics to identify power users
  - Implement skill recommendation engine
  - Create skill-based pricing tiers
  - Add skill performance benchmarking
  - Implement skill marketplace with user ratings
  - Create skill combination templates for common workflows
  - Add skill usage tracking for feature adoption metrics

### Smart Email System

- **File**: `packages/smart-email/lib/email-sender.ts`
- **Intent**: Facilitates user onboarding and retention through email communication
- **Confidence**: 75.0%
- **Entry Point**: `EmailSender.send(), sendTemplate()`- **Growth Potential**:
  - Add email open/click tracking for engagement scoring
  - Implement drip campaigns for onboarding sequences
  - Create behavioral trigger emails (abandoned actions, milestones)
  - Add email A/B testing capabilities
  - Implement email preference centers to reduce churn
  - Create win-back campaigns for inactive users
  - Add email-based referral campaigns with tracking

### Webhook Management System

- **File**: `packages/sidecar-daemon/src/webhook-manager.ts`
- **Intent**: Enables data-driven decisions through external event processing and automation
- **Confidence**: 70.0%
- **Entry Point**: `WebhookManager webhook endpoints`- **Growth Potential**:
  - Add webhook-based user event scoring
  - Implement real-time trigger processing for immediate responses
  - Create webhook analytics for integration health monitoring
  - Add webhook-based cohort updates for dynamic segmentation
  - Implement webhook queuing for high-volume processing
  - Create webhook-triggered email campaigns
  - Add webhook-based feature flag updates for personalization


## GTM Gaps

The following go-to-market gaps have been identified:

| Feature | Description | Priority |
|---------|-------------|----------|
| User Onboarding Flows | Missing structured user onboarding sequences to guide new users through key features and reduce time-to-value. Critical for reducing churn and increasing activation rates. | high |
| Viral Sharing Mechanisms | No native sharing or referral features to enable organic growth through user networks. Missing social sharing of achievements, results, or collaborative features. | high |
| Analytics Dashboard | Lack of user-facing analytics and insights dashboard for tracking usage, performance metrics, and ROI. Users can't see the value they're getting from the platform. | high |
| Team Collaboration Features | Missing team invitation, workspace sharing, and collaborative features that drive seat expansion and reduce churn through network effects. | medium |
| Usage-Based Pricing | While billing infrastructure exists, there's no clear usage metering and limit enforcement for freemium or usage-based monetization models. | medium |
| In-App Help System | No contextual help, tooltips, or guided tours to improve user experience and reduce support load. Critical for self-service adoption. | medium |
| Social Proof Elements | Missing testimonials, user counts, success stories, or case studies within the product to build trust and encourage upgrades. | low |
| Mobile App or PWA | No mobile experience for on-the-go access, which limits user engagement and stickiness in today's mobile-first world. | low |

---

*This context document was generated by skene-growth.*