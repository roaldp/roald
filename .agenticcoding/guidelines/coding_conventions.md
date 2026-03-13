# Coding Conventions

## General Principles
- Prioritize readability over cleverness
- Keep it simple - no overengineering, no fallbacks
- Fail fast: throw/raise errors immediately if values are not as expected
- For not-implemented features, raise an error - do not implement fallbacks or hardcode responses
- No emoji's in code

## Code Structure
- Each function or class method should do only one specific job
- Create code sections: MAIN HANDLERS / ENDPOINTS / MAIN ENTRYPOINTS at the top, HELPER FUNCTIONS below
- Add a file description: short human-readable summary, followed by bullet points with responsibilities
- Add constants at the top of the file for frequently changed or repeated values (do not overdo this)

### Section Format

**TypeScript:**
```
// ============================================================================
// SECTION NAME
// ============================================================================
```

**Python:**
```
# ============================================================================
# SECTION NAME
# ============================================================================
```

### Common sections
**Backend files:** constants, helper functions, entry point, main logic
**Frontend files:** constants, event handlers, components, render

## Types

### TypeScript
- Always define types for function parameters and return values
- Use specific types instead of `any` (or use interface where logical)
- Use `interface` for data transfer objects when data needs to be passed between classes
- Where applicable, the result of a function should be an (updated) DTO

### Python
- Always add type hints for function parameters and return values
- Use specific types instead of `Any` (use `TypedDict`, `dataclass`, or `NamedTuple` where logical)
- Use `TypedDict` or `dataclass` for data transfer objects when data needs to be passed between classes

```python
# Good:
def poll_slack_messages(config: dict, channel_id: str) -> list[dict]:
    ...

# Bad:
def poll_slack_messages(config, channel_id):
    ...
```

## Documentation

### TypeScript
- Use JSDoc, including params with a short explanation and what the function returns

### Python
- Use Google-style docstrings on all public functions
- Include Args, Returns, and Raises sections where applicable

```python
def migrate_config(config: dict) -> dict:
    """Ensure user config has all keys from template, preserving user values.

    Args:
        config: Current configuration dictionary loaded from config.yaml.

    Returns:
        Updated config dict with any missing keys filled from template.
    """
```

### Both languages
- Where a block of code is complex, use comments to annotate the steps
- Prefer simple, readable code over clever optimizations unless performance is critical

## Dependencies
- Use dependency injection to inject instances of other classes that are needed

## Naming Conventions

### TypeScript
- **Component files**: PascalCase (e.g., `MyComponent.tsx`)
- **Component names**: PascalCase (e.g., `const MyComponent = () => {...}`)
- **Props**: camelCase (e.g., `onClick`, `backgroundColor`)
- **Variable names**: camelCase (e.g., `userProfile`, `setIsLoading`)
- **Custom hooks**: Start with "use" (e.g., `useWindowSize`)

### Python
- **Module files**: snake_case (e.g., `mcp_inventory.py`)
- **Functions and variables**: snake_case (e.g., `poll_slack_messages`, `last_ts`)
- **Classes**: PascalCase (e.g., `PulseConfig`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `RESTART_EXIT_CODE`)
