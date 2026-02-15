"""
Stripe infrastructure telemetry collector
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from .base import TelemetryCollector, TelemetryResult


class StripeTelemetry(TelemetryCollector):
    """Collects telemetry from Stripe infrastructure"""

    @property
    def source_name(self) -> str:
        return "stripe"

    async def collect(self) -> TelemetryResult:
        """Collect Stripe infrastructure data"""
        try:
            api_key = self.config.get('api_key') or os.getenv('STRIPE_SECRET_KEY')

            if not api_key:
                return self._create_result(
                    {},
                    error="Missing STRIPE_SECRET_KEY"
                )

            data = {}

            # Collect products
            products = await self._get_products(api_key)
            if products:
                data['products'] = products

            # Collect pricing information
            prices = await self._get_prices(api_key)
            if prices:
                data['prices'] = prices

            # Collect webhooks
            webhooks = await self._get_webhooks(api_key)
            if webhooks:
                data['webhooks'] = webhooks

            # Collect subscription stats
            subscriptions = await self._get_subscriptions(api_key)
            if subscriptions:
                data['subscriptions'] = subscriptions

            return self._create_result(data)

        except Exception as e:
            return self._create_result({}, error=str(e))

    async def _get_products(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get Stripe products"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(api_key, '')

                async with session.get(
                    'https://api.stripe.com/v1/products',
                    auth=auth,
                    params={'limit': 20},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        products = data.get('data', [])

                        return {
                            'count': len(products),
                            'active': len([p for p in products if p.get('active')]),
                            'names': [p.get('name') for p in products[:10]]
                        }
            return None
        except Exception:
            return None

    async def _get_prices(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get Stripe prices"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(api_key, '')

                async with session.get(
                    'https://api.stripe.com/v1/prices',
                    auth=auth,
                    params={'limit': 20},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        prices = data.get('data', [])

                        # Detect usage-based pricing
                        usage_based = [
                            p for p in prices
                            if p.get('recurring', {}).get('usage_type') == 'metered'
                        ]

                        return {
                            'count': len(prices),
                            'active': len([p for p in prices if p.get('active')]),
                            'usage_based_count': len(usage_based),
                            'has_usage_based': len(usage_based) > 0
                        }
            return None
        except Exception:
            return None

    async def _get_webhooks(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get Stripe webhook endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(api_key, '')

                async with session.get(
                    'https://api.stripe.com/v1/webhook_endpoints',
                    auth=auth,
                    params={'limit': 20},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        webhooks = data.get('data', [])

                        return {
                            'count': len(webhooks),
                            'enabled': len([w for w in webhooks if w.get('status') == 'enabled']),
                            'event_types': list(set(
                                event
                                for w in webhooks
                                for event in w.get('enabled_events', [])
                            ))[:20]
                        }
            return None
        except Exception:
            return None

    async def _get_subscriptions(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get Stripe subscriptions stats"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(api_key, '')

                async with session.get(
                    'https://api.stripe.com/v1/subscriptions',
                    auth=auth,
                    params={'limit': 100},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        subscriptions = data.get('data', [])

                        return {
                            'count': len(subscriptions),
                            'active': len([s for s in subscriptions if s.get('status') == 'active']),
                            'trial': len([s for s in subscriptions if s.get('status') == 'trialing'])
                        }
            return None
        except Exception:
            return None
