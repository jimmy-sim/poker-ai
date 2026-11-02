"""Reproducible property checks under the committed dependency lockfile."""

from hypothesis import settings

settings.register_profile(
    "reproducible", derandomize=True, max_examples=200, deadline=None
)
settings.load_profile("reproducible")
