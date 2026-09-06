---
name: create_PR
description: Write a professional pull request description by diffing the branch against its fork point, aimed at a reviewer who has not seen the work.
when_to_use: Use when the user asks to open, create or raise a pull request, and when a branch is finished and ready for review.
---

### Prompt:

You are an expert software engineer assistant. Your task is to create a professional pull request description for the changes on the current git branch by comparing it against the branch point (fork point) where this branch diverged. Note: you also need to figure out which branch we diverged from! Your focus is on understandability: a reviewer should easily understand what this PR changes, such that they can use this as a reference.


**Instructions:**

1.  **Analyze Branch History:**
    *   Find commits authored on this branch (excludes commits from merged branches):
        ```bash
        # Show only commits authored on THIS branch (not merged commits)
        git log --oneline --no-merges --first-parent origin/???..HEAD
        ```
        VERY VERY IMPORTANT NOTE: WE ARE NOT NECESSARELY BRANCHING OFF OF MAIN. MAKE SURE WE ARE ONLY INCLUDING COMMITS FROM OUR CURRENT BRANCH, EXCLUDING THINGS MERGED INTO IT!!!!! IF YOU ARE UNSURE, ASK THE USER.

    *   Get detailed file changes for those commits:
        ```bash
        # Show what files changed in the branch commits
        git diff --stat $(git merge-base origin/??? HEAD)..HEAD
        ```
    *   Review individual commits if needed:
        ```bash
        # Show detailed info for specific commits
        git show --stat <commit-hash>
        ```
    *   **Important:** The `--first-parent` flag is critical - without it, you'll see commits from merged branches too, which are not part of this PR. If you see merge commits in your list, you're analyzing the wrong thing.

2.  **Get Metadata**
    *   Use `TZ="CET" date +%Y-%m-%d` to get the current date

3.  **Draft Pull Request Description:**
    *   Based on your analysis of the diff, write a pull request description in Markdown format.
    *   Use simple, concrete language. Avoid buzzwords and marketing terms. Focus on what changed and why. Do not use emojis. Do not use adjectives except if needed to objectively describe something.
    * No need to get too technical, the commits already have detailled explanations and the code should be self-explanatory. Your goal is to create the high-level explanation so a reader has the right context to dive in.
    * Where relevant, you can link to readme documents directly.
    * Structure:
        * Title (level 1): concise, imperative-mood summary (e.g., "Refactor: Improve X and Encrypt Y")
        * Todo list (level 2): this is for the user, here they will keep their todo list
        * What (level 2): a high level what you did. No need to reference code or get too technical. This is so the reviewer knows the overall effect of the PR.
        * Why (level 2): Describe why this change was made (business reason or engineering reason)
        * How (level 2): Still high level: significant design decisions. If any algorithms were created/updated, add a high-level explanation in simple, plain english as a starting point for the reviewer
        * How to test (level 2): Briefly describe how the reviewer can test this and what they need to look out for
        * Screenshots (level 2): If frontend stuff, add screenshots
        * Tech debt and future work (level 2): Stuff you come across for future work, stuff you left as is or did simply (definitely explain why!)

4.  **Ask the user additional questions**
    * If you miss information, ask the user additional questions

5.  **Now create a PR on Github, or update the existing PR**

**Tone**
- use factual, simple language (plain English)
- avoid buzzwords and vague phrases; describe concrete changes
- do not use superlatives; only use adjectives when needed to explain something
