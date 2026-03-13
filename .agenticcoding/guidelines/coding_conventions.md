# Coding Conventions for TypeScript

## General Principles
- Prioritize readability over cleverness
- Keep it simple - no overengineering, no fallbacks
- Fail fast: throw errors immediately if values are not as expected
- For not-implemented features, throw an error - do not implement fallbacks or hardcode responses
- No emoji's in code

## Code Structure
- Each function or class method should do only one specific job
- Create code sections: MAIN HANDLERS / ENDPOINTS / MAIN ENTRYPOINTS at the top, HELPER FUNCTIONS below
- Add a file description: short human-readable summary, followed by bullet points with responsibilities
- Add constants at the top of the file for frequently changed or repeated values (do not overdo this)

### Section Format
```
// ============================================================================
// SECTION NAME
// ============================================================================
```

### Common sections
**Backend files:** constants, helper files, entry point, main logic
**Frontend files:** constants, event handlers, components, render

## Types and Interfaces
- Always define types for function parameters and return values
- Use specific types instead of `any` (or use interface where logical)
- Use `interface` for data transfer objects when data needs to be passed between classes
- Where applicable, the result of a function should be an (updated) DTO

## Documentation
- Use JSDoc, including params with a short explanation and what the function returns
- Where a block of code is complex, use comments (//) to annotate the steps
- Prefer simple, readable code over clever optimizations unless performance is critical

## Dependencies
- Use dependency injection to inject instances of other classes that are needed

## Naming Conventions
- **Component files**: PascalCase (e.g., `MyComponent.tsx`)
- **Component names**: PascalCase (e.g., `const MyComponent = () => {...}`)
- **Props**: camelCase (e.g., `onClick`, `backgroundColor`)
- **Variable names**: camelCase (e.g., `userProfile`, `setIsLoading`)
- **Custom hooks**: Start with "use" (e.g., `useWindowSize`)
