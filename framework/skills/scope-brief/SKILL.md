---
name: scope-brief
description: Screen a request before spending anything on it, then scope what survives. Asks what breaks if we do not do this, what one number says it worked, and what the cheapest test of the risky assumption is, then commits to do it now, cheap test first, not now, or no. Only work that earns it gets a plan file and a budget.
when_to_use: Use when the instruction is long, covers more than one goal, was clearly dictated rather than typed, contains several "and also" clauses, or names an outcome without naming the work. Also use when the user asks to scope something, or says here is what I want, work out how. Do not use for a single concrete task with an obvious first step.
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
goal and refuse to spend on it until it has a number.

**Run this before discovery, not after.** Discovery is where the tokens go. Screening first
is the whole point: most requests should never reach a plan.

**The default answer is no.** The burden is on the work to earn the spend, not on you to
find a reason to decline.

### Three questions, answered in one paragraph

**1. What breaks if we do not do this?** If the honest answer is nothing, the answer is no.
Say so and stop. An improvement nobody is waiting on is not a job.

**2. What one number says it worked?** With a unit, and the value it holds today. If you
cannot name a unit, this is a wish rather than a job. If nobody has ever measured it,
**measuring it is the job** and it is usually an hour, not a week.

**3. What is the cheapest thing that would show us we are wrong?** That is the work. Not the
full idea, the test of the assumption the full idea rests on. Build that and nothing else.

### Then commit to one of four verdicts

| Verdict | When | What happens |
|---|---|---|
| **Do it** | Small, obvious, and question 1 has a real answer | Skip the plan, do it, say what you did |
| **Cheap test first** | The idea rests on an assumption nobody has checked | Build only the test, set a budget, report the number |
| **Not now** | Real, but something else is worth more this week | One line in the plan directory, no further spend |
| **No** | Question 1 came back empty, or the cost exceeds what the number is worth | Say so in one line and stop |

Say the verdict out loud in your first reply. **Only "cheap test first" and a large "do it"
earn a plan file.** Everything else is one or two lines.

### The budget

Every verdict that spends anything carries a budget: roughly how much agent work, and how
much of Roald's review time. Write it down before starting.

**When you hit it, stop and report rather than continue.** A job that runs past its budget
has told you the scope was wrong, and the right response is a new screen, not more spend.

### What this costs you to run

Under a minute of thinking and no tool calls. That is deliberate. A screen that costs as
much as the work is not a screen.

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
