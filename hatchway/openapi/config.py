"""
Configuration for OpenAPI spec generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenAPIConfig:
    """
    Configuration for OpenAPI specification generation.

    Example:
        config = OpenAPIConfig(
            title="My API",
            version="1.0.0",
            description="My awesome API built with Hatchway",
        )
    """

    title: str
    """The title of the API"""

    version: str
    """API version string (e.g., "1.0.0")"""

    description: str | None = None
    """Optional description of the API"""

    terms_of_service: str | None = None
    """URL to the Terms of Service"""

    contact: dict[str, str] | None = None
    """Contact information (name, url, email)"""

    license: dict[str, str] | None = None
    """License information (name, url)"""

    servers: list[dict[str, str]] = field(default_factory=lambda: [{"url": "/"}])
    """List of server configurations"""

    tags: list[dict[str, str]] | None = None
    """List of tags for grouping operations"""

    external_docs: dict[str, str] | None = None
    """External documentation (description, url)"""

    security: list[dict[str, list[str]]] | None = None
    """Global security requirements"""

    components: dict[str, Any] | None = None
    """Additional components (schemas, security schemes, etc.)"""

    def to_openapi_info(self) -> dict[str, Any]:
        """Convert configuration to OpenAPI info object."""
        info = {
            "title": self.title,
            "version": self.version,
        }

        if self.description:
            info["description"] = self.description

        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service

        if self.contact:
            info["contact"] = self.contact

        if self.license:
            info["license"] = self.license

        return info

    def to_openapi_base(self) -> dict[str, Any]:
        """Convert configuration to base OpenAPI spec structure."""
        spec = {
            "openapi": "3.0.3",
            "info": self.to_openapi_info(),
            "servers": self.servers,
            "paths": {},
        }

        if self.tags:
            spec["tags"] = self.tags

        if self.external_docs:
            spec["externalDocs"] = self.external_docs

        if self.security:
            spec["security"] = self.security

        # Merge components with default security schemes
        components = self._get_default_components()
        if self.components:
            # Deep merge components
            for key, value in self.components.items():
                if key in components and isinstance(value, dict):
                    components[key].update(value)
                else:
                    components[key] = value

        if components:
            spec["components"] = components

        return spec

    def _get_default_components(self) -> dict[str, Any]:
        """Get default components including security schemes (using snake_case for dataclass fields)."""
        return {
            "security_schemes": {
                "TokenAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "description": "Token authentication using 'Token <token>' format",
                },
                "SessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "sessionid",
                    "description": "Django session authentication",
                },
            }
        }
