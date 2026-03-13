## Guide on How to interact with the user
- before implementing code, always first propose a plan to the user and ask for feedback. You are free to read whichever files you need without asking for permission.
- when giving options, FIRST give all the options, do not execute them
- do not use emoji's
- if you want to do operations outside the scope of the user request, first ask the user
- BE TO THE POINT. Less is more.
- DO NOT OVERENGINEER. KEEP IT SIMPLE.
- Do not create dummy's or placeholders for stuff that still needs to be implemented. Add an explicit comment of what needs to be implemented, with a short description. If appropriate, throw a "not implemented" error

## Coding Guidelines
- Follow the coding conventions in `.agenticcoding/guidelines/`
- Plans go in `.docs/plans/yyyy.mm.dd-name-of-plan`

## Conductor Workflow
- Use `/create_plan` to create a structured implementation plan with subagent review
- Use `/implement_plan` to execute a plan phase-by-phase using subagents
- Use `/check_plan` to review an existing plan for gaps and inconsistencies
- Use `/check_coding_conventions` to audit code against our guidelines
- Use `/check_project_structure` to verify project organization
- Use `/push_all_changes_to_git` to stage, commit, and push
- Use `/create_PR` to create a professional pull request
- Use `/show_filetree_with_edits` to visualize file changes
- Use `/thoroughly_test` to run unit, integration, and e2e tests in stages
- Use `/draft_git_commit_message` to draft a commit message from the current diff
