---
name: scope-brief
description: Turn a long, spoken or rambling instruction into a scoped work plan before doing any of it. Runs discovery, then Archer mode which forces the goal down to a measurable number with a baseline and a threshold, then ideation, then an MVP cut sized by that number, and writes one plan file. Asks at most three questions, each with a proposed answer.
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

## 4. Archer mode

Named after Archer, a friend of Roald's who does this to him in conversation and is the
reason this section exists. Archer's move is to refuse a fuzzy goal. He keeps asking until
the thing you want is a number, and then asks what the smallest piece of work is that moves
that number.

Run the cascade in order. **Answer every question yourself first**, from the repository and
from what you found in discovery. Write your answer into the plan. Only the ones you
genuinely cannot resolve become part of the three questions in section 3, and there is
rarely more than one.

If a step has no answer, that is the finding. Say so rather than inventing one.

### The nine questions

**1. What is different in the world if this works?** Not "better onboarding". A thing that
is observably different afterwards. If you cannot finish the sentence "afterwards, X
happens and it did not before", you have not found the job yet.

**2. Who notices, and how do they notice?** A named person or a named group, and the moment
they would notice. If nobody notices, the work has no value and belongs in the out-list.

**3. What is the number?** One metric, with a unit. Percentage, minutes, euros, count per
week. If you cannot name a unit, go back to question 1, because you are still describing an
activity rather than an outcome.

**4. What is that number today?** The baseline. **If there is no baseline, measuring it is
the first step of the job and it is often the entire MVP.** Say that plainly. A great deal
of work gets built to fix something nobody has measured.

**5. What value would make this worth having done?** The threshold, not "any improvement".
Archer's question here is the sharp one: if it moved by half that, would you regret the
time? If yes, the threshold is wrong.

**6. When do we read it?** A date. A metric with no read date is never read, and the work
quietly becomes unfalsifiable.

**7. What is the smallest thing that moves this number?** Now cut. **The MVP is defined by
the metric, not by the feature.** Take the full idea and ask what could be deleted while
still moving the number by the threshold. Then ask again. Two rounds, minimum.

**8. What are we deliberately not doing?** The out-list, named. Everything from question 7's
two rounds of cutting lands here, so it is visible later and does not creep back.

**9. What would make us stop?** The kill condition. If the number has not moved by the
threshold by the read date, the work stops rather than gets extended. Write the condition
now, while it is cheap, not later when the work has sunk cost in it.

### When there is genuinely no metric

Some jobs are real and have no natural number: write a document, restructure a folder,
answer a legal question. Do not skip the cascade and do not invent a fake percentage. Use a
proxy, which is an observable event rather than a measurement:

- A decision that gets made, by a named person, by a date.
- A draft that gets sent without the first paragraph being rewritten.
- A question that stops being asked.
- A file that a named person opens and acts on.

A proxy still needs questions 4 through 9. "Roald sends it without rewriting the opening,
first attempt, by Friday" is a threshold, a read date and a kill condition in one line.

### The cost check

Before writing the steps, put the estimated cost next to the threshold. Agent time, Roald's
review time, and anything the work commits him to afterwards.

If the cost is close to or above what moving the number is worth, **say so and propose the
smaller version instead.** This is the point of the whole section. Archer's actual
contribution is not the metric, it is refusing to spend a week on something worth an
afternoon.

### What goes in the plan

The Success criteria section takes the answers to 3 through 6, and the MVP scope section
takes 7 through 9. Both are checked mechanically:

```
python3 ~/.claude/framework-src/scripts/check_plan_metrics.py <path to PLAN.md>
```

That script fails when a metric has no unit, no baseline, no threshold, no read date or no
kill condition. Run it before showing the plan to Roald. It is a lint, not a judgement: it
cannot tell you the metric is the right one.

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
