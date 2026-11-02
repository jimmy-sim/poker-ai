"""Check the installed package rather than adding src/ to the import path."""

from importlib.metadata import distribution
from importlib.resources import files


def test_installed_distribution_includes_type_marker() -> None:
    """Catch missing package installation or a missing PEP 561 marker."""
    assert distribution("poker-ai").metadata["Name"] == "poker-ai"
    assert files("poker_ai").joinpath("py.typed").is_file()
