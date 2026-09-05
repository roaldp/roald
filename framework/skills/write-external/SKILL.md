---
name: write-external
description: Draft or revise anything a person outside the team will read - emails, Slack and WhatsApp messages, documents, proposals, investor and customer copy, landing page and outreach text, pull request descriptions read by outsiders. Use whenever the output is prose that leaves the company, and when asked to rewrite, tighten or review such copy. Loads the house style and Roald's own writing samples at the moment of drafting.
---

# Drafting anything that leaves the company

Do not draft from your own sense of good business writing. Your sense of good business
writing is the problem this skill exists to solve.

## 1. Load the style before writing a sentence

Read `~/.claude/framework-style/CORE.md` in full. It is under 200 lines and it governs
every sentence you are about to write.

`CORE.md` carries its own before-and-after pairs in section 1: agent draft on the left,
what Roald actually sent on the right. Those pairs are the mechanism and the rules are the
backstop, so read section 1 slowly rather than skimming to the rule list.

Do not go and read the full writing corpus as well. That was measured on 2026-09-06:
loading `CORE.md` alone produced almost the same draft as loading `CORE.md` plus the
1,176-line corpus, and the corpus costs a lot of context for one deleted phrase. The corpus
is the source document for maintaining `CORE.md`, not something to load while drafting.

If the project you are in has its own overlay for this medium, read that too and let it
win on anything it covers:

- Investor and customer copy in `ai-infrastructure-capital`:
  `docs/pitch-materials/style/STYLE.md`, then `CLAIMS.md`, then `FORMATS.md`.
- WhatsApp, Telegram and SMS in the same repo: `docs/pitch-materials/style/MESSAGES.md`.
  Different medium, own rules, and it overrides the document rules.

## 2. Establish the facts before drafting

Facts come from the brief, from the repo, or from a named source. A figure with no source
is marked `[TK]` and never softened into an adjective.

If there is no brief, build one before writing. Ask for missing facts rather than
inventing them, and keep it to three questions.

## 3. Draft

Write it once, straight through, following the format the medium calls for.

## 4. Revise your own draft before showing it

This is not optional and it is where the defects are. Work through `CORE.md` section 9,
one numbered check at a time.

The four that fail most often:

**No closing line.** No sentence may tell the reader what to conclude. If you wrote one,
delete it and add nothing.

**Cut the explanation, keep the fact.** A specific enough fact is its own argument. Naming
the institution beats two sentences interpreting why it matters.

**Headers are the reader's question**, never a category label.

**Count the em dashes.** Target zero inside sentences.

## 5. Say what you were unsure about

End your reply to Roald with the two or three places you had to guess: a figure you could
not source, a claim you were not sure we can make, a name you were not sure of. Do not
bury these in the draft.

## 6. Save it where the feedback loop can see it

For anything substantial, write the draft to a file and say where it is, rather than
leaving it only in the chat. The diff between your draft and what Roald actually sends is
the highest-value input this system gets, and a draft that exists only in a chat window
teaches it nothing.
