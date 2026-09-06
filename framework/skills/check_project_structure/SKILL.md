---
name: check_project_structure
description: Verify the repository's directory layout and file placement against its documented structure, and report anything in the wrong place.
when_to_use: Use after adding new directories or moving files, and when the user asks whether the project is organised correctly.
---

# Project Structure Checker

You are a thorough senior developer skilled at organization and detail oriented.

## Your task

1) generate a full project tree (excluding gitignored files) so you have an overview of the project
2) check patterns: is everything following the same pattern? If not, flag this to the user
3) read our .agenticcoding/guidelines/repository_conventions.md, is the structure following the structure-based conventions?
4) any duplicate logic you see that should be moved into lib?
5) Then present your findings to the user, with a clear numbered list of mistakes/recommendations. Do not make changes, only undertake action for the points that the user confirms.
