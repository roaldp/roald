---
name: push_all_changes_to_git
description: Stage the current changes, draft a commit message from the real diff, commit and push.
when_to_use: Use when the user asks to commit and push, save the work to git, or push everything.
---

## 1. Stage Changes
First, stage all the current changes.

## 2. Draft git commit message
Then, draft a git commit message for the current `git diff`.
- IMPORTANT: actually get the `git diff`, this could be different than your most recent actions, or certain things might already be committed
- IMPORTANT: if nothing is staged, ask the user to stage first

The format should be a one-line summary, followed by a blank line, and then a flat list of bullet points (using dashes -) detailing the changes.

Follow these rules for the bullet points:
- Group related, granular changes into a single, more concise bullet point. For example, instead of listing "add file X" and "configure Y in file X" separately, combine them.
- Focus on the high-level change, not the implementation details. Describe *what* was changed, not every single line that was altered.
- Omit minor details like configuration tweaks (e.g., changing a timeout value, adjusting a model parameter), minor refactorings, or code formatting changes.
- Each line should follow this structure ["add", "update", "fix", "refactor", ...] [path to file]: [description]
- DO NOT USE ADJECTIVES (for example: do not use superior, massive, ...), and use objective, to-the-point wording
- Do not add any advertising for Claude or "Generated with X" or "Co-Authored by X" additions

## 3. Push to Github
Finally, push the changes to git with the git commit message.
