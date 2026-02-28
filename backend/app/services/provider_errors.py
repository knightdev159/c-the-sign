"""Provider-specific exceptions with user-facing guidance."""

from __future__ import annotations


class ProviderConfigurationError(RuntimeError):
    """Raised when a provider is selected without the required config."""


class ProviderAuthenticationError(RuntimeError):
    """Raised when a provider cannot authenticate in the current environment."""


class ProviderServiceError(RuntimeError):
    """Raised when an upstream provider request fails after configuration succeeds."""
