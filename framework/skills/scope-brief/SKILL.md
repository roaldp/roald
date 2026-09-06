---
name: scope-brief
description: Turn a long, spoken or rambling instruction into a scoped work plan before doing any of it. Runs discovery, then ideation, then design requirements, then an MVP cut, and writes one plan file. Asks at most three questions, each with a proposed answer.
when_to_use: Use when the instruction is long, covers more than one goal, was clearly dictated rather than typed, contains several "and also" clauses, or names an outcome without naming the work. Also use when the user asks to scope something, or says here is what I want, work out how. Do not use for a single concrete task with an obvious first step.
---

# Turning a long brief into a scoped plan

Roald will not type a command to start this. If the instruction in front of you looks like a
brief rather than a task, run this without being asked and say in one line that you are
doing so.

The whole point is that he pays the cost of explaining once, up front, instead of in a
dozen small corrections later. Do not hand that cost back to him by asking a lot of
questions.

## 1. Write the brief down before you do anything else

Create `.docs/plans/<yyyy.mm.dd>-<slug>/PLAN.md` from the template at
`~/.claude/framework-src/framework/templates/PLAN.template.md`, and paste his instruction
into the Brief section **verbatim**. Do not tidy it, summarise it, or fix the grammar.

Then write the pointer so every later session and every subagent finds it:

```
mkdir -p .docs/plans && echo '.docs/plans/<yyyy.mm.dd>-<slug>/PLAN.md' > .docs/plans/ACTIVE
```

That file is what the re-anchor hook reads. Without it a delegated subagent has no idea a
plan exists.

## 2. Discovery, before ideas

Read before you think. What already exists, what was tried before and abandoned, what the
constraints actually are, what prior art is already on the machine. Check every claim you
are tempted to make about the code by opening the code.

Fill in the Discovery section, and end it with **the problem restated in your own words, in
one paragraph**. That paragraph is the main output of this stage. Reading it costs him less
than answering questions, and it is where a misunderstanding surfaces.

## 3. The intent check, capped at three questions

Roughly a third of what looks ambiguous is answerable by reading the repository. Do that
first. Then ask **at most three questions in total, not three per topic**, and attach your
own proposed answer to each so he can reply "yes".

Never ask about style or how something should read. Measured elicitation rates for style
preferences are close to zero, and the answer is already in
`~/.claude/framework-style/CORE.md` and in the writing corpus.

An unresolved question that blocks nothing does not stop work. Record the assumption in the
plan, mark it, and carry on.

## 4. Ideation, then requirements, then the MVP cut

**Approach.** Name the options you considered, pick one, say why, and name what you
rejected. This is the section that stops the work quietly turning into an easier job.

**Success criteria.** Given, when, then. An observable trigger and an observable outcome. A
criterion you cannot check mechanically is not finished being written.

**MVP scope.** What is in, what is explicitly out, and what the deliverable actually looks
like: a file at a path, a message of a given shape, a script with a given interface. The
"out" list is the section that does the work. Prioritise scope success, then speed, then
simplicity for whoever reviews it.

## 5. Have the plan attacked before building it

Spawn the `plan-reviewer` subagent. It is read-only, it never saw your reasoning, and its
job is to argue the plan will not work. Do two rounds with different angles.

You are the boss and may reject a finding, but say which ones you rejected and why. Round 1
of this framework's own review produced 22 findings and round 2 found six real bugs in code
that had already passed a live test.

## 6. Then stop and show him

Half a page. What the plan is, what you had to assume, and the three questions if you have
any. The plan file carries everything else.

Do not start building until he has seen the restatement. That is the one gate in this
procedure that exists for his benefit rather than the work's.

## 7. While building

Tick each step in the plan as its verification passes. When you do something the plan does
not cover, write it in the Log section with the reason, before you do it. A deviation that
is written down is a decision. One that is not is drift, and that is the failure this whole
file exists to catch.
