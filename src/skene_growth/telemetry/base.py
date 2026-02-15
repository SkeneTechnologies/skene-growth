"""
Base telemetry collector interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class TelemetryResult:
    """Result from a telemetry collection"""

    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'error': self.error,
            'success': self.success
        }


class TelemetryCollector(ABC):
    """Abstract base class for telemetry collectors"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def collect(self) -> TelemetryResult:
        """Collect telemetry data from the source"""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the telemetry source"""
        pass

    def _create_result(self, data: Dict[str, Any], error: Optional[str] = None) -> TelemetryResult:
        """Helper to create a telemetry result"""
        return TelemetryResult(
            source=self.source_name,
            data=data,
            error=error,
            success=error is None
        )
