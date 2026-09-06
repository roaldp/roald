---
name: scope-brief
description: Screen a request before spending anything on it, then scope what survives. Asks who is waiting on the answer and by when, what has to be true for it to be safe to act on, and what is the smallest thing that gets the decision made, then commits to do it, cheap test first, not now, or no. Tailored to the work that actually runs here: contracts, figures, records, outbound copy and state lookups.
when_to_use: Use when the request opens something new that would run past about an hour: long, dictated, more than one goal, or an outcome with no named work. Do not use for a turn inside work already in flight, a single concrete action, a question about current state, or an edit to a draft. Median request here is 21 words and only one in nine is a brief, so the usual answer is not to run this.
---

# Turning a long brief into a scoped plan

Roald will not type a command to start this. If the instruction in front of you looks like a
brief rather than a task, run this without being asked and say in one line that you are
doing so.

**Section 1 is a screen and it runs first, before any tool call.** Most requests should not
survive it. The point of this skill is not to produce good plans, it is to stop tokens being
spent on work that was never worth doing.

He pays the cost of explaining once, up front, instead of in a dozen small corrections
later. Do not hand that cost back by asking a lot of questions.

## 1. Archer mode: the screen

Named after Archer, who does this to Roald in conversation. His move is to refuse a fuzzy
goal and refuse to spend on it until someone is waiting on the answer.

The questions below are tailored to the work that actually runs here, measured across 1,741
of Roald's own prompts. See `08-what-the-work-actually-is.md` in the framework repo. The
short version: this is a fund and infrastructure operator's inbox, not a product backlog.
The largest single family is legal and contract work at 12 per cent. Software is 9 per cent.
Almost everything has a counterparty and a date behind it.

### First, the exit

**Median typed prompt here is 21 words, and only 11 per cent run past 60.** Most turns are
moves inside work already in flight, not new jobs. "Ask for Yonten's confirmation of this
timeline" does not need a screen, it needs doing.

If the request continues something already underway, or names one concrete action with an
obvious first step, **do it and say nothing about scoping**. A screen that fires on every
turn is the waste it was built to prevent.

Screen only when the request opens something new and would run past roughly an hour.

### Then three questions, answered in one paragraph, before any tool call

**1. What decision or obligation is waiting on this? Whose, and by when?**

Name the person and the date. Can we sign. What do we quote. Is the wire due. Can this be
sent. If nothing and nobody is waiting, it is a nice-to-have, and the verdict is not now.

**2. What has to be true for the answer to be safe to act on?**

This is the question that fits this work, and it is not about a metric. Roald acts on agent
output with money and legal exposure behind it. What goes wrong here is not building the
wrong feature, it is working from a superseded document, quoting one of three versions of a
figure, or treating an unmerged record as real.

What "safe" means depends on the family:

| Family | Safe to act on means |
|---|---|
| Legal and contract | The current version, named. Which clause, which draft, who has reviewed it, what is superseded. |
| Numbers and model | Every figure traced to a source, and the assumptions stated. Which fee is in and which is out. |
| Record keeping | It is in the authoritative store and merged, not sitting in a branch. The CRM counts only what is committed. |
| Outbound copy | Every claim is one we can stand behind, and the facts come from the brief rather than from the draft. |
| State lookup | The answer names its source file and its date, and says what it could not check. |
| Build and code | It runs, and there is a way to see that it runs. |
| Research and decision | The sources are named, and where they disagree that is reported rather than smoothed over. |

If you cannot say what would make it safe, that is the finding. Say so.

**3. What is the smallest thing that gets that decision made?**

Not the full request. The smallest thing that unblocks the person in question 1. Everything
else waits until they are unblocked.

### Then commit to one of four verdicts

| Verdict | When | What happens |
|---|---|---|
| **Do it** | Someone is waiting and the work is under a few hours | Do it, report, no plan file |
| **Cheap test first** | It rests on something nobody has checked | Check that one thing, report the answer, then re-screen |
| **Not now** | Real, but nobody is waiting on it this week | One line, no further spend |
| **No** | Nobody is waiting, or the cost exceeds what the decision is worth | One line, and say why |

Say the verdict in your first reply. **Only a multi-day "do it" or a "cheap test first"
earns a plan file.**

### The budget

Anything that spends carries one: roughly how much agent work, and how much of Roald's
review time. Write it down before starting.

**When you hit it, stop and report rather than continue.** Running past a budget is the
scope telling you it was wrong, and the answer is a new screen, not more spend.

## 2. Write the brief down, if the verdict earned a plan

Only for a large "do it" or a "cheap test first". Everything else gets one or two lines
in the reply and no file.

Create `.docs/plans/<yyyy.mm.dd>-<slug>/PLAN.md` from the template at
`~/.claude/framework-src/framework/templates/PLAN.template.md`, and paste his instruction
into the Brief section **verbatim**. Do not tidy it, summarise it, or fix the grammar.

Then write the pointer so every later session and every subagent finds it:

```
mkdir -p .docs/plans && echo '.docs/plans/<yyyy.mm.dd>-<slug>/PLAN.md' > .docs/plans/ACTIVE
```

That file is what the re-anchor hook reads. Without it a delegated subagent has no idea a
plan exists.

## 3. Discovery, before ideas

Read before you think. What already exists, what was tried before and abandoned, what the
constraints actually are, what prior art is already on the machine. Check every claim you
are tempted to make about the code by opening the code.

Fill in the Discovery section, and end it with **the problem restated in your own words, in
one paragraph**. That paragraph is the main output of this stage. Reading it costs him less
than answering questions, and it is where a misunderstanding surfaces.

## 4. The intent check, capped at three questions

Roughly a third of what looks ambiguous is answerable by reading the repository. Do that
first. Then ask **at most three questions in total, not three per topic**, and attach your
own proposed answer to each so he can reply "yes".

Never ask about style or how something should read. Measured elicitation rates for style
preferences are close to zero, and the answer is already in
`~/.claude/framework-style/CORE.md` and in the writing corpus.

An unresolved question that blocks nothing does not stop work. Record the assumption in the
plan, mark it, and carry on.

## 5. Ideation, then requirements, then the MVP cut

**Approach.** Name the options you considered, pick one, say why, and name what you
rejected. This is the section that stops the work quietly turning into an easier job.

**Success criteria.** Given, when, then, carrying the metric, baseline, threshold and read
date from the cascade. An observable trigger and an observable outcome. A criterion you
cannot check mechanically is not finished being written.

**MVP scope.** What is in, what is explicitly out, what the deliverable actually looks like
as a file at a path or a message of a given shape, and the kill condition. Prioritise scope
success, then speed, then simplicity for whoever reviews it.

## 6. Have the plan attacked before building it

Spawn the `plan-reviewer` subagent. It is read-only, it never saw your reasoning, and its
job is to argue the plan will not work. Do two rounds with different angles.

You are the boss and may reject a finding, but say which ones you rejected and why. Round 1
of this framework's own review produced 22 findings and round 2 found six real bugs in code
that had already passed a live test.

## 7. Then stop and show him

Half a page. What the plan is, what you had to assume, and the three questions if you have
any. The plan file carries everything else.

Do not start building until he has seen the restatement. That is the one gate in this
procedure that exists for his benefit rather than the work's.

## 8. While building

Tick each step in the plan as its verification passes. When you do something the plan does
not cover, write it in the Log section with the reason, before you do it. A deviation that
is written down is a decision. One that is not is drift, and that is the failure this whole
file exists to catch.
