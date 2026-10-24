"""Dispatch generation to the explicitly selected project framework."""

from typing import Callable, TypeVar

_Result = TypeVar('_Result')


def generate_project_for_framework(
    framework: str,
    react_generator: Callable[[], _Result],
    reflex_generator: Callable[[], _Result],
) -> _Result:
    """Run the requested generator; omitted/empty framework retains React."""
    selected = (framework or 'react').strip().lower()
    if selected == 'react':
        return react_generator()
    if selected == 'reflex':
        return reflex_generator()
    raise ValueError(f"Unsupported framework '{framework}'. Choose 'react' or 'reflex'.")
