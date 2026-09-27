"""Central registry for discovering and swapping domain provider implementations."""

from typing import Any, TypeVar

T = TypeVar("T")


class ProviderNotFoundError(Exception):
    """Raised when a requested provider is not registered."""


class ProviderRegistry:
    """Registry managing provider instances against domain contracts."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    def register(self, contract_name: str, provider_instance: Any) -> None:
        """Register a provider instance under a contract name."""
        self._providers[contract_name] = provider_instance

    def get(self, contract_name: str) -> Any:
        """Retrieve the active provider instance for a contract."""
        if contract_name not in self._providers:
            raise ProviderNotFoundError(f"No provider registered for contract '{contract_name}'.")
        return self._providers[contract_name]

    def has(self, contract_name: str) -> bool:
        """Check if a contract has an active provider."""
        return contract_name in self._providers

    def clear(self) -> None:
        """Clear all registered providers."""
        self._providers.clear()


# Global default registry instance
global_registry = ProviderRegistry()
