"""Base tool interface for opensre.

All tools must inherit from BaseTool and implement the required methods.
This mirrors the pattern defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolParams:
    """Generic container for tool execution parameters."""

    raw: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)


@dataclass
class ToolResult:
    """Standardised result returned by every tool."""

    success: bool
    output: Any = None
    error: str | None = None

    def __bool__(self) -> bool:  # allows `if result:` checks
        return self.success


class BaseTool(ABC):
    """Abstract base class for all opensre tools.

    Subclasses must define:
        - ``my_tool_name``  – unique snake_case identifier
        - ``MyToolName``    – human-readable display name
        - ``is_available``  – runtime availability check
        - ``extract_params``– parse raw kwargs into a ToolParams instance
        - ``run``           – execute the tool and return a ToolResult
    """

    #: Unique snake_case identifier (e.g. ``"http_check"``)
    my_tool_name: str = ""

    #: Human-readable display name (e.g. ``"HTTP Check"``)
    MyToolName: str = ""

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the tool can be used in the current environment.

        Implementations should check for required binaries, credentials,
        network access, etc.
        """

    @abstractmethod
    def extract_params(self, **kwargs: Any) -> ToolParams:
        """Validate and normalise raw keyword arguments into ToolParams.

        Raise ``ValueError`` for missing or invalid parameters.
        """

    @abstractmethod
    def run(self, params: ToolParams) -> ToolResult:
        """Execute the tool with the given params and return a ToolResult."""

    # ------------------------------------------------------------------
    # Convenience entry point
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> ToolResult:
        """High-level entry point: validate availability, extract params, run.

        Example::

            result = my_tool.execute(url="https://example.com", timeout=5)
            if result:
                print(result.output)
        """
        if not self.is_available():
            return ToolResult(
                success=False,
                error=f"Tool '{self.my_tool_name}' is not available in this environment.",
            )

        try:
            params = self.extract_params(**kwargs)
        except ValueError as exc:
            return ToolResult(success=False, error=f"Invalid parameters: {exc}")

        try:
            return self.run(params)
        except Exception as exc:  # noqa: BLE001 – catch-all so callers always get a ToolResult
            return ToolResult(success=False, error=f"Unexpected error during '{self.my_tool_name}': {exc}")
