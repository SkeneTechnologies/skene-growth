"""
Aggregates telemetry from multiple sources
"""

import asyncio
from typing import List, Dict, Any
from .base import TelemetryCollector, TelemetryResult
from .supabase import SupabaseTelemetry
from .vercel import VercelTelemetry
from .stripe import StripeTelemetry


class TelemetryAggregator:
    """Aggregates telemetry from multiple collectors"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.collectors: List[TelemetryCollector] = []

        # Initialize collectors
        if self.config.get('supabase', {}).get('enabled', True):
            self.collectors.append(SupabaseTelemetry(self.config.get('supabase', {})))

        if self.config.get('vercel', {}).get('enabled', True):
            self.collectors.append(VercelTelemetry(self.config.get('vercel', {})))

        if self.config.get('stripe', {}).get('enabled', True):
            self.collectors.append(StripeTelemetry(self.config.get('stripe', {})))

    async def collect_all(self) -> Dict[str, Any]:
        """Collect telemetry from all sources concurrently"""
        tasks = [collector.collect() for collector in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated = {
            'telemetry': {},
            'errors': [],
            'success_count': 0,
            'total_count': len(self.collectors)
        }

        for result in results:
            if isinstance(result, Exception):
                aggregated['errors'].append(str(result))
                continue

            if isinstance(result, TelemetryResult):
                aggregated['telemetry'][result.source] = result.to_dict()
                if result.success:
                    aggregated['success_count'] += 1
                if result.error:
                    aggregated['errors'].append(f"{result.source}: {result.error}")

        return aggregated

    def to_manifest_format(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Convert telemetry to growth manifest format"""
        manifest_section = {
            'infrastructure_state': {
                'timestamp': None,
                'sources': {}
            }
        }

        for source, data in telemetry.get('telemetry', {}).items():
            if data.get('success'):
                manifest_section['infrastructure_state']['sources'][source] = data['data']
                if not manifest_section['infrastructure_state']['timestamp']:
                    manifest_section['infrastructure_state']['timestamp'] = data['timestamp']

        return manifest_section
