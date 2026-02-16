# Skene

> AI-powered Product-Led Growth orchestration with deterministic state machines

Skene replaces fragmented SaaS tools (Salesforce, Klaviyo, Confluence, Stripe) with a unified, context-aware fabric that understands your product in real-time. It provides deterministic state machines with 100% auditability, natural language prompts for execution, and AI-native apps that replace legacy business operations tools.

**Built for**: Developers, product teams, and businesses seeking to replace multiple SaaS tools with an integrated AI-powered growth operating system

## Tech Stack

Skene is built with:

- **Language**: TypeScript
- **Services**: Stripe, HubSpot, Salesforce, Intercom, Paddle, Chargebee, Braintree, Resend

## Features

### Billing Gateway

Unified billing system that works with multiple payment providers like Stripe. Handles subscriptions, cancellations, and one-time charges with automatic provider detection.

```
const gateway = new BillingGateway({ provider: new StripeProvider(apiKey) }); await gateway.subscribe(customerId, 'plan_pro_monthly');
```

### Adaptive Billing Engine

Automatically analyzes your codebase and configures billing behavior based on detected patterns (usage-based, subscription, or hybrid models).

```
const engine = new AdaptiveBillingEngine(); const config = await engine.configureFromManifest(manifest);
```

### Subscription Gating

Controls access to features based on user subscription tiers. Shows upgrade prompts when users approach limits or try to use premium features.

```
const gate = new SubscriptionGate(); const result = await gate.checkAccess(userId, 'premium-tool');
```

### Multi-Tenant Context

Manages organization and user context across requests in multi-tenant applications. Handles permissions and metadata automatically.

```
await manager.withTenant(orgId, userId, organization, user, async () => { const ctx = manager.getCurrent(); });
```

### Gamification Engine

Adds points, levels, and achievements to encourage user engagement. Tracks XP, manages level progression, and unlocks badges based on user actions.

```
const engine = new GamificationEngine({ levels, xpMap }); await engine.awardXP('user123', 'create_post');
```

### Journey Tracking

Tracks user progression through any workflow or lifecycle. Records state transitions and events to understand user behavior patterns.

```
const tracker = new JourneyTracker(); await tracker.recordStateChange(userId, 'activated', 'completed onboarding');
```

### Proactive Triggers

Monitors user behavior and automatically suggests relevant actions or features. Includes cooldown management and acceptance tracking.

```
const engine = new TriggerEngine(rules); const triggers = engine.evaluate(userContext);
```

### Payment Provider Skills

Ready-to-use integrations for popular payment providers including Stripe, Paddle, Chargebee, and Braintree with unified API.

```
const stripeSkill = new StripeSkill(); await stripeSkill.execute({ params: { customerId, priceId } });
```

### CRM Integrations

Connect with major CRM platforms like HubSpot, Salesforce, and Intercom to manage leads, contacts, and customer communications.

```
const hubspotSkill = new HubspotSkill(); await hubspotSkill.execute({ params: { operation: 'createContact', email } });
```

### Smart Email System

Reliable email sending with automatic retries, template variables, and batch processing using the Resend API.

```
const sender = createEmailSender(apiKey); await sender.send({ to: user.email, subject: 'Welcome!', body: html });
```


## Roadmap

We're working on the following improvements:

- **User Onboarding Flows**: Missing structured user onboarding sequences to guide new users through key features and reduce time-to-value. Critical for reducing churn and increasing activation rates.
- **Viral Sharing Mechanisms**: No native sharing or referral features to enable organic growth through user networks. Missing social sharing of achievements, results, or collaborative features.
- **Analytics Dashboard**: Lack of user-facing analytics and insights dashboard for tracking usage, performance metrics, and ROI. Users can't see the value they're getting from the platform.

- Team Collaboration Features: Missing team invitation, workspace sharing, and collaborative features that drive seat expansion and reduce churn through network effects.
- Usage-Based Pricing: While billing infrastructure exists, there's no clear usage metering and limit enforcement for freemium or usage-based monetization models.
- In-App Help System: No contextual help, tooltips, or guided tours to improve user experience and reduce support load. Critical for self-service adoption.
- Social Proof Elements: Missing testimonials, user counts, success stories, or case studies within the product to build trust and encourage upgrades.
- Mobile App or PWA: No mobile experience for on-the-go access, which limits user engagement and stickiness in today's mobile-first world.

---

*Documentation generated by skene-growth*