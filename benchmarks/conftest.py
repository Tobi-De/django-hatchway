"""
Pytest configuration for benchmarks.

Benchmarks use the demo project since they test realistic API endpoints.
"""

import os
import sys

# Add demo project to path FIRST (before any imports)
demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo")
if demo_path not in sys.path:
    sys.path.insert(0, demo_path)

# Override Django settings BEFORE any Django imports
os.environ["DJANGO_SETTINGS_MODULE"] = "demo.settings"

import django

# Setup Django immediately
django.setup()


def pytest_configure(config):
    """Additional pytest configuration."""
    pass


def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Customize benchmark JSON output."""
    # Add metadata
    output_json["metadata"] = {
        "framework": "django-hatchway",
        "python_version": sys.version,
    }
