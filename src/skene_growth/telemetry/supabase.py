"""
Supabase infrastructure telemetry collector
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from .base import TelemetryCollector, TelemetryResult


class SupabaseTelemetry(TelemetryCollector):
    """Collects telemetry from Supabase infrastructure"""

    @property
    def source_name(self) -> str:
        return "supabase"

    async def collect(self) -> TelemetryResult:
        """Collect Supabase infrastructure data"""
        try:
            url = self.config.get('url') or os.getenv('SUPABASE_URL')
            service_key = self.config.get('service_key') or os.getenv('SUPABASE_SERVICE_KEY')

            if not url or not service_key:
                return self._create_result(
                    {},
                    error="Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"
                )

            data = {}

            # Collect schema information
            schema_info = await self._get_schema_info(url, service_key)
            if schema_info:
                data['schema'] = schema_info

            # Collect edge function info
            functions_info = await self._get_functions_info(url, service_key)
            if functions_info:
                data['edge_functions'] = functions_info

            # Collect connection stats (if available)
            stats_info = await self._get_stats_info(url, service_key)
            if stats_info:
                data['stats'] = stats_info

            return self._create_result(data)

        except Exception as e:
            return self._create_result({}, error=str(e))

    async def _get_schema_info(self, url: str, service_key: str) -> Optional[Dict[str, Any]]:
        """Get database schema information via REST API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'apikey': service_key,
                    'Authorization': f'Bearer {service_key}'
                }

                # Query information_schema to get table count
                # This is a simplified version - real implementation would use PostgREST
                async with session.get(
                    f"{url}/rest/v1/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        # In reality, you'd query specific tables
                        return {
                            'status': 'accessible',
                            'tables': 'detected'
                        }
            return None
        except Exception:
            return None

    async def _get_functions_info(self, url: str, service_key: str) -> Optional[Dict[str, Any]]:
        """Get edge functions information"""
        try:
            # Edge functions are typically accessed via /functions/v1/
            # This is a placeholder - real implementation would use Supabase Management API
            return {
                'status': 'accessible',
                'detected': True
            }
        except Exception:
            return None

    async def _get_stats_info(self, url: str, service_key: str) -> Optional[Dict[str, Any]]:
        """Get connection and usage statistics"""
        try:
            # Real implementation would query pg_stat_database or use Management API
            return {
                'monitoring': 'enabled'
            }
        except Exception:
            return None
