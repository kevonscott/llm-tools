# Agent Guidelines for Python Code Quality

Guidelines for maintaining high-quality Python code. These rules MUST be followed by ALL.

## Core Principles

All code MUST be optimized:
- maximizing algorithmic big-O efficiency for memory and runtime
- using parallelization and vectorization where appropriate
- following proper style conventions for the code language (e.g. maximizing code reuse)
- no extra code beyond what is absolutely necessary to solve the problem (i.e. no technical debt or bloat)

## Preferred Tools

- Use `uv` for Python package management.
- For data science:
  - **NEVER** ingest more than 10 rows of a data frame at a time. Only analyze subsets of code to avoid overloading your memory context.

## Code Style and Formatting

- **MUST** use meaningful, descriptive variable and function names
- **MUST** follow PEP 8 style guidelines
- **MUST** use 4 spaces for indentation (never tabs)
- **NEVER** use emoji, or unicode that emulates emoji (e.g. ✓, ✗).
- Use snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- Limit line length to 8 characters (ruff formatter standard)
- Follow guidlines in pyproject.toml if available in the project

## Documentation

- **MUST** include docstrings for all public functions, classes, and methods
- **MUST** document function parameters, return values, and exceptions raised
- Keep comments up-to-date with code changes
- Include examples in docstrings for complex functions
- **ONLY** use numpy-style docstring with type-hint ONLY in method signature

Example docstring:

```python
def process_data(data: np.ndarray, threshold: float = 0.5) -> List[int]:
    """
    Filter data based on a specific threshold.

    Parameters
    ----------
    data
        The input array containing numeric values to be processed.
    threshold
        The cutoff value used for filtering elements.

    Returns
    -------
    list
        Indices of the elements that exceed the specified threshold.
    """
    return np.where(data > threshold)[0].tolist()
```

## Type Hints

- **MUST** use type hints for all function signatures (parameters and return values)
- **NEVER** use `Any` type unless absolutely necessary
- **NEVER** use `from __future__ import annotations`
- **MUST** run mypy and resolve all type errors
- Use `T | None` for nullable types

## Error Handling

- **NEVER** silently swallow exceptions without logging
- **MUST** never use bare `except:` clauses
- **MUST** catch specific exceptions rather than broad exception types
- **MUST** use context managers (`with` statements) for resource cleanup
- Provide meaningful and actionable error messages

## Function Design

- **MUST** keep functions focused on a single responsibility
- **NEVER** use mutable objects (lists, dicts) as default argument values
- Limit function parameters to 7 or fewer in most cases
- Return early to reduce nesting

## Class Design

- **MUST** keep classes focused on a single responsibility
- **MUST** keep `__init__` simple; avoid complex logic
- Use dataclasses and enums for simple data containers
- Prefer composition over inheritance
- Avoid creating additional class functions if they are not necessary

## Testing

- **MUST** write unit tests for all new functions and classes
- **MUST** mock external dependencies (APIs, databases, file systems)
- **MUST** use unittest as the testing framework for writing tests
- Use .venv/pytest for running tests

## Python Best Practices

- **MUST** use `is` for comparing with `None`, `True`, `False`
- **MUST** use f-strings for string formatting
- Run mypy for type checking once all code is implemented.
- **MUST** use Ruff for code formatting and linting
- **MUST** document dependencies in `pyproject.toml`
- **MUST** avoid wildcard imports (`from module import *`)

## Security

- **NEVER** store secrets, API keys, or passwords in code. Only store them in `.env`.
  - Ensure `.env` is declared in `.gitignore`.
  - **NEVER** print or log URLs to console if they contain an API key.
- **MUST** use environment variables for sensitive configuration
- **NEVER** log sensitive information (passwords, tokens, PII)

## Version Control
@git-ops/git.md

---

**Remember:** Prioritize clarity and maintainability over cleverness.
