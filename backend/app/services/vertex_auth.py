"""Helpers for Vertex AI configuration and authentication checks."""

from __future__ import annotations

import os
from pathlib import Path

from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

from app.services.provider_errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderServiceError,
)


def ensure_vertex_access(*, project: str | None, location: str | None, provider_label: str) -> None:
    """Fail fast with a clear message before making a Vertex SDK request."""

    if not project or not location:
        raise ProviderConfigurationError(
            f"{provider_label} requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION."
        )

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and not Path(credentials_path).expanduser().exists():
        raise ProviderAuthenticationError(
            f"{provider_label} cannot use GOOGLE_APPLICATION_CREDENTIALS={credentials_path!r} "
            "because that file does not exist on this machine. "
            "Unset GOOGLE_APPLICATION_CREDENTIALS to use `gcloud auth application-default login`, "
            "or point it at a valid service account key file."
        )

    try:
        default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    except DefaultCredentialsError as exc:
        raise ProviderAuthenticationError(
            f"{provider_label} requires Application Default Credentials. "
            "Run `gcloud auth application-default login` for local development "
            "or set GOOGLE_APPLICATION_CREDENTIALS to a service account key file."
        ) from exc


def wrap_vertex_error(
    *,
    provider_label: str,
    model_name: str,
    project: str | None,
    location: str | None,
    exc: Exception,
) -> RuntimeError:
    """Normalize common Vertex failures into clearer application errors."""

    message = str(exc).strip()
    if "Unable to authenticate your request" in message:
        return ProviderAuthenticationError(
            f"{provider_label} could not authenticate. "
            "Run `gcloud auth application-default login` for local development "
            "or set GOOGLE_APPLICATION_CREDENTIALS to a service account key file."
        )
    if "Publisher Model" in message and "was not found or your project does not have access" in message:
        return ProviderConfigurationError(
            f"{provider_label} cannot use model {model_name!r} in project {project!r} "
            f"at location {location!r}. "
            "Use a supported Vertex model ID, for example `gemini-2.5-flash`, "
            "and confirm the Vertex AI API is enabled for the project."
        )

    detail = message or exc.__class__.__name__
    return ProviderServiceError(f"{provider_label} failed: {detail}")
