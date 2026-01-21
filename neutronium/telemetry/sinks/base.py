
from typing import Protocol

from neutron.telemetry.facts import RequestFacts


class TelemetrySink(Protocol):
    """
    Protocol defining the interface for request telemetry sinks.

    Sinks receive RequestFacts after each request and can process them
    in various ways (logging, analytics, metrics, etc.).

    Each sink should be independent and not know about other sinks.
    """

    def emit(self, facts: RequestFacts) -> None:
        """
        Process the request telemetry data.

        Args:
            facts: Immutable container with all request telemetry data.
        """
        ...
