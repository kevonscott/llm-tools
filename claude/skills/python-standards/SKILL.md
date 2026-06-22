---
name: python-standards
description: Enforces Python code standards when writing or reviewing Python code. Triggers on Python development tasks.
---

# Python Standards

## Style
- Type hints on all function or method signatures
- No type hints in the function or method docstring
- numpy style docstrings on functions and methods
- Use pathlib instead of os.path
- f-strings for string formatting, never .format()
- Limit all lines to a maximum of 80 characters

## Testing
- Tests should be written with unittest framework
- use pytest for running tests
