---
name: draft_git_commit_message
description: Read the actual staged diff and draft a commit message describing what changed and why.
when_to_use: Use when the user asks for a commit message, or before committing, so the message matches the diff rather than the conversation.
---

Draft a git commit message for the current `git diff`.
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

Return as a fenced text block.
