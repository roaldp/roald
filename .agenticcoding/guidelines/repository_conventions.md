# Repository Conventions

## Directory Structure

```
.conductor/              # Conductor workspace config
  conductor.json         # Setup script reference
  conductor-setup.sh     # Environment symlinker
  prompts/               # Custom prompts (slash commands + subagents)

.agenticcoding/          # Agentic coding configuration
  guidelines/            # Coding and repository conventions

.docs/                   # Documentation
  plans/                 # Implementation plans (yyyy.mm.dd-name-of-plan)

CLAUDE.md                # Agent interaction guidelines
```

## Plan Files

Plans are stored in `.docs/plans/` with the naming convention:
```
yyyy.mm.dd-name-of-plan.md
```

Each plan follows a standard structure:
1. High level goal
2. File tree (new/modified/deleted files)
3. Per-file methods and types/DTOs
4. Important technical notes (optional)
5. Phases with todos
6. Success criteria

## Conventions

- Colocate test files with source files as `[filename].test.ts`
- Integration tests go in `tests/integration/`
- E2E tests go in `tests/e2e/api/` and `tests/e2e/ui/`
- Keep git commit messages factual, no adjectives, no "Generated with" tags
