---
name: create_plan
description: Turn a decided piece of work into a written implementation plan before any code is written. Produces a plan file with a filetree, per-file methods and types, phases and success criteria, then has it adversarially reviewed twice.
when_to_use: Use when the user describes a feature, refactor or change of any size and the approach is settled but nothing is written down yet. Also use when the user says plan it, draft a plan, or how would you build this. Do not use for a one-line fix.
---

# Create Plan

You are a senior engineer who is skilled at making clear documentation for other developers. Your goal is to create a plan for the feature discussed with the user.

## Plan location

Add it to `.docs/plans/yyyy.mm.dd-name-of-plan`

## Plan structure

- section of high level goal
- filetree section: clear indication of all files involved, mark new ones, deleted ones, modified ones (with a small explanation of what is changing, what is added, etc)
- section of per-file methods and types/DTOs. Keep it high level, no code. For methods we just need the arguments, what it returns, and an explanation. Ideally, arguments and returns are DTOs.
- section with important technical notes. Do not add simple, straighforward code. Only document more difficult or intricated code. It is possible that this section can be omitted.
- phases section: a section with all phases and todos to implement the plan step by step
- success criteria section


## Format of per-file methods and types/DTOs

```markdown
### use-report-tutorial-navigation.ts (NEW)

#### Types

```
NavigationState {
  section: number
  isAnimating: boolean
  cameFromContact: boolean
}

UseReportTutorialNavigationProps {
  sectionSlugs: string[]
}

UseReportTutorialNavigationReturn {
  currentSection: number
  currentSlug: string
  isContactSection: boolean
  isFirstSection: boolean
}
```

#### Methods

| Method | Arguments | Returns | Description |
|--------|-----------|---------|-------------|
| `useReportTutorialNavigation` | `props: UseReportTutorialNavigationProps` | `UseReportTutorialNavigationReturn` | Main hook that sets up all navigation event listeners and manages section state |
| `calculateNextIndex` | `current: number, direction: "up" \| "down", config: IndexConfig` | `number` | Pure function that determines next section index, handling contact modal trigger logic |
| `navigateToSection` | `index: number, slug: string` | `void` | Scrolls to section DOM element (skips for virtual "contact" section) |
```


## Workflow

1) Create plan as described above
2) Use the subagent plan-reviewer to review the plan
3) Review the suggestions from the subagent. Note: you can choose what to implement and what not to implement, as you have more context. You are the boss.
4) Do one more iteration with a plan-reviewer
5) Summarize to the user the plan, and also create for each reviewing cycle a table with the suggestions you got, what you (partially) implemented in the plan and what you ignored
