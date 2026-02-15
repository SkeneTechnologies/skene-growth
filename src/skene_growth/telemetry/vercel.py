"""
Vercel infrastructure telemetry collector
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from .base import TelemetryCollector, TelemetryResult


class VercelTelemetry(TelemetryCollector):
    """Collects telemetry from Vercel infrastructure"""

    @property
    def source_name(self) -> str:
        return "vercel"

    async def collect(self) -> TelemetryResult:
        """Collect Vercel infrastructure data"""
        try:
            token = self.config.get('token') or os.getenv('VERCEL_TOKEN')
            team_id = self.config.get('team_id') or os.getenv('VERCEL_TEAM_ID')

            if not token:
                return self._create_result(
                    {},
                    error="Missing VERCEL_TOKEN"
                )

            data = {}

            # Collect deployments
            deployments = await self._get_deployments(token, team_id)
            if deployments:
                data['deployments'] = deployments

            # Collect environment variables count
            env_vars = await self._get_env_vars_info(token, team_id)
            if env_vars:
                data['env_vars'] = env_vars

            # Collect project info
            projects = await self._get_projects(token, team_id)
            if projects:
                data['projects'] = projects

            return self._create_result(data)

        except Exception as e:
            return self._create_result({}, error=str(e))

    async def _get_deployments(self, token: str, team_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get recent deployments"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {token}'
                }

                url = 'https://api.vercel.com/v6/deployments'
                params = {'limit': 10}
                if team_id:
                    params['teamId'] = team_id

                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        deployments = data.get('deployments', [])

                        return {
                            'count': len(deployments),
                            'recent': [
                                {
                                    'id': d.get('uid'),
                                    'state': d.get('state'),
                                    'created': d.get('created')
                                }
                                for d in deployments[:5]
                            ]
                        }
            return None
        except Exception:
            return None

    async def _get_env_vars_info(self, token: str, team_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get environment variables information"""
        try:
            # This would require project ID - placeholder implementation
            return {
                'monitoring': 'enabled'
            }
        except Exception:
            return None

    async def _get_projects(self, token: str, team_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get projects information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {token}'
                }

                url = 'https://api.vercel.com/v9/projects'
                params = {'limit': 20}
                if team_id:
                    params['teamId'] = team_id

                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        projects = data.get('projects', [])

                        return {
                            'count': len(projects),
                            'names': [p.get('name') for p in projects[:10]]
                        }
            return None
        except Exception:
            return None
