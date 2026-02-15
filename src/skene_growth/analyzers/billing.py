"""
Billing analyzer for detecting payment integration.

Detects billing providers (Stripe, Paddle) by analyzing:
- Package dependencies
- Import statements
- Webhook endpoints
- API usage patterns
"""

import re
from pathlib import Path
from typing import Dict, List, Any

from skene_growth.codebase import CodebaseExplorer


class BillingAnalyzer:
    """
    Analyzer for detecting billing/payment integrations.

    Detects:
    - Stripe integration
    - Paddle integration
    - Webhook endpoints
    - Subscription logic
    """

    def __init__(self):
        """Initialize billing analyzer."""
        self.detected_providers: List[str] = []
        self.webhook_endpoints: List[Dict[str, Any]] = []

    async def analyze(self, codebase: CodebaseExplorer) -> Dict[str, Any]:
        """
        Analyze codebase for billing integration.

        Args:
            codebase: CodebaseExplorer instance

        Returns:
            Dict with detected billing information:
            {
                "provider": "stripe" | "paddle" | None,
                "webhooks": [{"path": "...", "provider": "..."}],
                "subscription_detected": bool
            }
        """
        result = {
            "provider": None,
            "webhooks": [],
            "subscription_detected": False,
        }

        # Check package.json for billing dependencies
        provider = await self._detect_from_package_json(codebase)
        if provider:
            result["provider"] = provider

        # Scan TypeScript files for imports and webhooks
        ts_files = await self._find_typescript_files(codebase)

        for file_path in ts_files:
            content = await self._read_file(codebase, file_path)

            # Check for Stripe imports
            if "import Stripe from 'stripe'" in content or 'import { Stripe }' in content:
                result["provider"] = "stripe"

            # Check for Paddle imports
            if "import Paddle" in content or "from '@paddle" in content:
                if not result["provider"]:
                    result["provider"] = "paddle"

            # Check for webhook routes
            webhooks = self._detect_webhook_endpoints(content, file_path)
            result["webhooks"].extend(webhooks)

            # Check for subscription logic
            if self._has_subscription_logic(content):
                result["subscription_detected"] = True

        return result

    async def _detect_from_package_json(self, codebase: CodebaseExplorer) -> str | None:
        """Detect billing provider from package.json dependencies."""
        try:
            # Look for package.json in project root
            package_files = await codebase.find_files("**/package.json", max_files=5)

            for file_path in package_files:
                content = await self._read_file(codebase, file_path)

                # Check for Stripe dependency
                if '"stripe"' in content or "'stripe'" in content:
                    return "stripe"

                # Check for Paddle dependency
                if '"@paddle/' in content or "'@paddle/" in content:
                    return "paddle"

        except Exception:
            pass

        return None

    async def _find_typescript_files(self, codebase: CodebaseExplorer) -> List[str]:
        """Find TypeScript files that might contain billing logic."""
        patterns = [
            "**/billing*.ts",
            "**/stripe*.ts",
            "**/paddle*.ts",
            "**/webhook*.ts",
            "**/payment*.ts",
            "**/subscription*.ts",
        ]

        files = []
        for pattern in patterns:
            try:
                found = await codebase.find_files(pattern, max_files=10)
                files.extend(found)
            except Exception:
                continue

        return list(set(files))  # Deduplicate

    async def _read_file(self, codebase: CodebaseExplorer, file_path: str) -> str:
        """Read file content from codebase."""
        try:
            return await codebase.read_file(file_path)
        except Exception:
            return ""

    def _detect_webhook_endpoints(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect webhook endpoint definitions in TypeScript code.

        Looks for patterns like:
        - app.post('/webhooks/stripe', ...)
        - router.post('/webhook', ...)
        - '/webhooks/paddle'
        """
        webhooks = []

        # Pattern 1: Express/Fastify route definitions
        # app.post('/webhooks/stripe', ...)
        route_pattern = r"\.post\s*\(\s*['\"]([/\w-]+(?:stripe|paddle|webhook)[/\w-]*)['\"]"
        matches = re.findall(route_pattern, content, re.IGNORECASE)

        for path in matches:
            provider = None
            if 'stripe' in path.lower():
                provider = 'stripe'
            elif 'paddle' in path.lower():
                provider = 'paddle'
            else:
                provider = 'unknown'

            webhooks.append({
                "path": path,
                "provider": provider,
                "file": file_path,
            })

        # Pattern 2: Webhook path constants
        # const WEBHOOK_PATH = '/webhooks/stripe'
        const_pattern = r"['\"]([/\w-]+(?:stripe|paddle|webhook)[/\w-]*)['\"]"
        if 'webhook' in content.lower():
            matches = re.findall(const_pattern, content, re.IGNORECASE)
            for path in matches:
                if path.startswith('/'):
                    provider = None
                    if 'stripe' in path.lower():
                        provider = 'stripe'
                    elif 'paddle' in path.lower():
                        provider = 'paddle'

                    if provider and not any(w['path'] == path for w in webhooks):
                        webhooks.append({
                            "path": path,
                            "provider": provider,
                            "file": file_path,
                        })

        return webhooks

    def _has_subscription_logic(self, content: str) -> bool:
        """Check if file contains subscription-related logic."""
        subscription_keywords = [
            'subscription',
            'subscribe',
            'trial',
            'plan',
            'tier',
            'billing_period',
            'stripe.subscriptions',
            'createSubscription',
            'cancelSubscription',
        ]

        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in subscription_keywords)


async def detect_billing(codebase: CodebaseExplorer) -> Dict[str, Any]:
    """
    Convenience function to detect billing integration.

    Args:
        codebase: CodebaseExplorer instance

    Returns:
        Dict with billing information
    """
    analyzer = BillingAnalyzer()
    return await analyzer.analyze(codebase)
