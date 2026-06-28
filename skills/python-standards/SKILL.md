---
name: python-standards
description: Enforces Python code standards when writing or reviewing Python code. Triggers on Python development tasks.
---

# Python Standards

Detailed Python style. TYhe judgement-based rules live in the global
`CLAUDE.md`; This skill holds the mechanical detail and templates.

## Style
- snake case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- Never use mutable default arguments (e.g. `def f(x=[])`); use `None`, and build inside the function
- Type hints on all function or method signatures; never put type hints in docstring
- use `T | None` for all nullable types
- numpy-style docstring on all public functions, classes, and methods
- Use pathlib instead of os.path
- f-strings for string formatting, never `.format()`
- Prefer list comprehensions and generator expressions over manual loops
- Use `enumerate()` instead of a manual counter
- Limit all lines to a maximum of 80 characters

## Design
- Limit function parameters to 5 or fewer

## Docstring template (numpy style)

Document every parameter , return value and exception raised, Include an Examples
section for complex functions.

```python
def calculate_area(radius: float, shapeL str | None = "circle") -> float:
    """
    Calculate the area of a geometric shape.

    Extended description of the functions's logic can go here,
    explaining any complex algorithms or assumptions.

    Parameters
    ---------
    raduis
        The radius of the circle or side of the square.
    shape
        The type of shape ('circle' or 'square'). Default is 'circle'

    Returns
    -------
    area
        The calculated area of the specified shape.

    Raises
    ------
    ValueError
        If the radius is negative of shape is unsupported.

    Examples
    --------
    >>> calculate_area(5)
    78.53981633974483
    >>> calculate_area(4, shape="square")
    16.0
```

## Testing
- Write tests with the unittest framework
- run tests with pytest
