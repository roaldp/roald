# Challenge round 2: attack on 06-design-v2.md and the shipped code

Adversarial review, 2026-09-06. Targets: `06-design-v2.md`, `framework/hooks/*.py`,
`framework/templates/PLAN.template.md`, `framework/style/CORE.md`,
`framework/skills/write-external/SKILL.md`, `scripts/install_framework.py`,
`scripts/agent_inventory.py`, and the claims in `04-verification-results.md`.

Round 1's findings are assumed known and are not repeated. Everything below was produced by
running the code against crafted input, by re-deriving the corpus numbers independently, or
by reading the machine. Commands and inputs are given so each can be re-run.

The repo was being edited while this review ran. `framework/skills/write-external/SKILL.md`,
`framework/style/CORE.md`, `framework/output-styles/steering.md` and
`framework/agents/plan-reviewer.md` appeared mid-review and are included.

## Verdict

Draft 2 is a real improvement on draft 1 and it is still wrong in the place it claims to be
most right. Its headline new claim, that the rebuilt contract gate holds, is not what the
shipped installer installs: `scripts/install_framework.py` still registers the gate on
`Write|Edit` and the evidence counter on `Read`, which is exactly the configuration draft 2
demonstrates is defeated by one `echo`. Even wired correctly the gate is a no-op, because
reading any `.json`, `.txt`, `.log` or `.png` file anywhere on disk increments the evidence
counter, so the first `cat package.json` of any real job unlocks it. Its second new claim,
the em-dash density budget of one per thousand words, is justified in the document by the
sentence "does not fail on his own file"; his own file is 451 words with six em dashes, a
rate of 13.3 per thousand, so the justification is false by a factor of thirteen and the
shipped `CORE.md` and `SKILL.md` have already silently reverted to the ban the budget was
meant to replace. The writing profile that anchors all of this is measured from the wrong
register, says so about itself in plain words, and is then used anyway; its em-dash figure
is additionally inflated by about seventy per cent by pasted agent output that the filter
did not catch. Every empirical result in `04-verification-results.md` was produced on
`claude-haiku-4-5-20251001` and the document never says so, which matters for the two
results that are behavioural rather than mechanical. The build order is smaller than draft
1 and still puts the measurement baseline fourth, after three changes that alter what it
would measure.

---

## Code defects

Severity is about what happens on Roald's machine in normal use, not about how hard the
input is to construct.

### 1. The installer registers the gate on the matchers the design proves are defeated. SEVERE

`scripts/install_framework.py`, `HOOK_PLAN`:

```python
"PreToolUse": [("Write|Edit", "contract_gate.py")],
"PostToolUse": [("Read", "evidence_tracker.py")],
```

`contract_gate.py`'s own docstring says `Registered on PreToolUse with matcher
"Write|Edit|Bash"`. `evidence_tracker.py`'s says `Registered on PostToolUse with matcher
"Read|Bash"`. The design says the gate was rebuilt with `Bash` in the matcher and that this
is what makes it hold. The installer disagrees with all three. Run `--apply` today and you
get the draft-1 gate that `echo '{"greeting":{"passes":true}}' > contract.json` walks
straight through, plus a counter that never increments under bypass permissions.

Fix: change the two matchers to `Write|Edit|Bash` and `Read|Bash`.

### 2. Reading any ordinary JSON or text file unlocks the gate. SEVERE

`evidence_tracker.is_evidence` returns True for any path whose suffix is in
`{.log, .txt, .json, .xml, .png, .jpg, .diff, .patch}`, anywhere on the filesystem, with no
relation to the plan.

Reproduced against `/tmp/hookprobe`:

```
$ echo '{"cwd":"/tmp/hookprobe","tool_name":"Read",
         "tool_input":{"file_path":"/tmp/hookprobe/package.json"}}' | python3 evidence_tracker.py
$ cat .docs/plans/demo/.evidence-reads
1
$ echo '{"cwd":"/tmp/hookprobe","tool_name":"Write",
         "tool_input":{"file_path":".../contract.json"}}' | python3 contract_gate.py
(no output — allowed)
```

`tsconfig.json` and `notes.txt` behave identically. Every real job reads a `.json` in its
first few tool calls. The gate is therefore open before the agent has done any work, and
`04-verification-results.md` §8 only failed to see this because its test project contained
nothing to read except the files on the `NEVER_EVIDENCE` list.

Fix: count only files under the plan directory, or only files whose modification time is
later than the last contract write.

### 3. One evidence read unlocks a write that can pass every step at once. SEVERE

The counter is a single integer per plan. It carries no association between the evidence
read and the step being marked. `contract_gate.main` checks `read_counter(counter) == 0`
and then permits the entire write. An agent that reads one log may write
`{"a":{"passes":true},"b":{"passes":true},"c":{"passes":true}}` in one call.

The hook's own docstring claims the opposite: "marking a step as passing is only reachable
through having opened the evidence for it."

Fix: key the counter per step name and require the write to change only steps with a
non-zero count, or drop the mechanism.

### 4. The re-anchor hook reports an unanswered intake question as the next step. SEVERE for the anchor, and it is the one mechanism draft 2 rests on

`reanchor.UNCHECKED_STEP` matches the first `- [ ]` anywhere in the file.
`framework/templates/PLAN.template.md` puts `## Open questions` with `- [ ] **Q1.**` before
`## Steps`. Against a plan built from the shipped template:

```
$ echo '{"cwd":"/tmp/hookprobe","hook_event_name":"SubagentStart"}' | python3 reanchor.py
{"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext":
"ACTIVE PLAN: /tmp/hookprobe/.docs/plans/demo/PLAN.md\nCURRENT PHASE: greeting\n
NEXT UNCHECKED STEP: **Q1.** Should we use X? — *Proposed answer: yes.*\n..."}}
```

Every delegated subagent is told its next step is a question waiting for Roald. §8 of the
verification results did not catch this because it tested against a hand-written `PLAN.md`,
not against the template that shipped alongside it.

Fix: scope the regex to the text after the `## Steps` heading.

### 5. The plan pointer the whole framework depends on is gitignored. SEVERE

`.gitignore` line 11 is `.context/`. `git check-ignore -v .context/active-plan` confirms it
is ignored. Every hook resolves the plan through `.context/active-plan`, so the pointer
cannot be committed, does not travel to a new Conductor workspace on the same branch, and
does not survive a fresh clone. In a new workspace the re-anchor hook is silent and the gate
is off, and nothing reports that.

Separately, `.evidence-reads` is written into `.docs/plans/<name>/`, which is **not**
ignored, so the gate's private state file turns up in `git status` and in diffs.

Fix: move the pointer to a tracked path, or write the plan path into `PLAN.md` discovery
and drop the pointer. Add `.evidence-reads` to `.gitignore`.

### 6. `reanchor.py` crashes on any contract.json that is not a JSON object. MODERATE

Input: `printf '[]' > contract.json`, then any `SessionStart` payload.

```
AttributeError: 'list' object has no attribute 'items'   (rc=1)
```

Same for `'"unfinished"'` and for any top-level scalar. The installer registers this hook on
`SessionStart` with matcher `startup|resume|compact`, so it runs at the start of every
session in every directory. A malformed contract produces a visible hook-error banner on
every session start until someone fixes the file.

Fix: `if not isinstance(contract, dict): return None`.

### 7. `evidence_tracker.py` crashes on a non-string command or file_path. MODERATE

Input: `{"cwd":"/tmp/hookprobe","tool_input":{"command":123}}` gives
`TypeError: expected string or bytes-like object`. `{"tool_input":{"file_path":["a","b"]}}`
gives `TypeError: expected str, bytes or os.PathLike object, not list`. Both exit 1. The
payloads are contrived today but the hook has no type guards at all, and the tool schema is
not under this repo's control.

Fix: `isinstance(x, str)` guards in `extract_read_paths`.

### 8. The Bash write patterns are bypassed by ordinary shell and deny ordinary reads. MODERATE

Verified by feeding each command to `contract_gate.py` (ALLOW means the write is not seen):

| Command | Result |
|---|---|
| `echo x > contract.json` | DENY |
| `F=contract.json; echo x > $F` | **ALLOW** |
| `cd .docs/plans/demo && echo x > c*.json` | **ALLOW** |
| `printf x \| dd of=contract.json` | **ALLOW** |
| `jq '.a=1' contract.json \| sponge contract.json` | **ALLOW** |
| `ed -s contract.json <<< "w"` | **ALLOW** |
| `npm install && cat contract.json` | **DENY** (a pure read) |
| `cp contract.json contract.json.bak` | **DENY** (a backup) |
| `pip install -r req.txt && python3 check.py contract.json` | **DENY** (a pure read) |

The false positives come from `install` being in the same alternation as `mv|cp|rm`, so any
command containing the word `install` followed later by `contract.json` with no `|` or `;`
between them is blocked. The design already concedes the bypasses; it does not mention that
the same patterns block reads.

Fix: none that is worth writing. Pattern-matching a shell command is not a boundary. Use
`permissions.deny` or drop the gate.

### 9. Two concurrent subagents corrupt each other's counter. MODERATE

`evidence_tracker` does read-then-write with no lock:

```python
current = int(counter.read_text(...)) if counter.is_file() else 0
counter.write_text(str(current + 1), ...)
```

Two subagents reading evidence at the same moment both read `1` and both write `2`. Worse,
`contract_gate` resets the shared counter to `0` after any permitted write, so subagent A
completing a write silently re-locks the gate against subagent B, which read its evidence
thirty seconds earlier. The design's "one worker at a time" applies to implementation only;
it explicitly keeps reading and review fanned out, which is precisely when this fires.

Fix: per-agent counter files keyed on `agent_id`, or drop the gate.

### 10. The pointer file chooses where the hook writes, including inside `~/.claude`. MODERATE

`resolve_plan_dir` takes the pointer's contents, joins it to the project directory if
relative, and returns `plan_path.parent`. `evidence_tracker` then writes `.evidence-reads`
into that directory. Verified:

```
$ echo '../../../tmp/victimdir/PLAN.md' > .context/active-plan
$ echo '{"cwd":"/tmp/hookprobe","tool_name":"Read",
         "tool_input":{"file_path":"/etc/hosts.txt"}}' | python3 evidence_tracker.py
$ ls /tmp/victimdir
.evidence-reads  PLAN.md

$ echo "$HOME/.claude/CLAUDE.md" > .context/active-plan
$ (same call)
$ ls ~/.claude/.evidence-reads
-rw-r--r--  1 roaldp  staff  1 ...
```

A `.context/active-plan` committed by anyone into any repo Roald opens decides where a
background process creates a file. The filename is fixed and the content is a digit, so the
blast radius is small, but the mechanism is arbitrary-directory file creation driven by
repo content, and there is no containment check. (The stray file created during this test
was deleted.)

Fix: require the resolved plan directory to be inside the project directory.

### 11. The installer's symlinks follow whichever checkout it was run from. MODERATE

`REPO_ROOT = Path(__file__).resolve().parent.parent`. The design devotes a paragraph to why
the install must come from a dedicated clone at `~/.claude/framework-src` and not from a
Conductor checkout. The code adds that paragraph as a comment and enforces nothing. Run
from `~/conductor/workspaces/roald/lima`, which is where it sits today, it points
`~/.claude/framework-hooks` at a workspace Conductor can archive, and every hook on the
machine then fails with a missing-file error on every tool call.

Fix: refuse to run when `REPO_ROOT` is under `~/conductor`, or take the source path as a
required argument.

### 12. The settings backup only exists for the first run. MODERATE

`back_up_settings` copies `settings.json` aside only `if not backup.exists()`. Install once,
use the machine for a month while `settings.json` accumulates real changes, then run
`--uninstall`: the backup on disk is the month-old one, and the uninstall write is
unprotected. The design describes this as "backs the file up first", which is true once.

Fix: timestamp the backup filename.

### 13. `load_settings` has no error handling and the installer has no shebang. MINOR

`json.loads(SETTINGS.read_text(...))` raises an uncaught `JSONDecodeError` and prints a
traceback if `~/.claude/settings.json` ever contains a trailing comma or a comment. Also,
every hook in `framework/hooks/` is `0755` with a shebang; `scripts/install_framework.py` is
`0644` with neither, so the documented invocation is `python3 scripts/install_framework.py`
and nothing says so.

### 14. Three different statements of the SessionStart matcher. MINOR, but it changes behaviour

- `reanchor.py` docstring: `SessionStart (matcher compact|resume)`
- `install_framework.py`: `("startup|resume|compact", "reanchor.py")`
- `06-design-v2.md`: "on `SessionStart` for `startup` and `resume`"

The installed version includes `startup`, so the anchor fires at the start of every session
in every directory that has a pointer. `04-verification-results.md` §6 presents "a fresh
startup fired neither hook" as a confirmed result; the installer then discards the only
thing that result established.

### 15. Measured cost: 34 ms per invocation. MINOR, stated for the record

Twenty runs each, non-matching payload, `/usr/bin/python3` 3.9.6:

```
contract_gate:    34.2 ms per call
evidence_tracker: 34.1 ms per call
```

With the matchers the installer ships, that is roughly 2,500 invocations per fortnight at
the machine's current tool rates, about 90 seconds total. With the `Bash` matchers the
design calls for, it is about 15,000 invocations and roughly 70 ms added to every Bash call
in the interactive loop. Not a reason to reject anything. It is a reason not to add hooks
that do nothing.

### 16. `agent_inventory.py` merges a dictionary with itself. MINOR

```python
return describe_surfaces(Path.home()) | describe_surfaces(CLAUDE_HOME.parent) | {...}
```

`CLAUDE_HOME` is `Path.home() / ".claude"`, so `CLAUDE_HOME.parent` is `Path.home()`. The
same expensive scan runs twice and the second result overwrites the first with identical
values. Delete the second call.

---

## Findings on the design

### A. The em-dash budget's stated justification is false, and the shipped artefacts already contradict it. SEVERE

Draft 2: "A budget of one per thousand is his own measured rate, is well under the published
human baseline of 3.23, and does not fail on his own file."

Measured, counting `—` against whitespace-delimited words:

| File | Words | Em dashes | Per 1,000 |
|---|---|---|---|
| `~/.claude/CLAUDE.md` (his, hand-written) | 451 | 6 | **13.30** |
| `framework/templates/PLAN.template.md` | 482 | 6 | **12.45** |
| `framework/style/CORE.md` | 1,709 | 4 | 2.34 |
| `06-design-v2.md` | 3,021 | 9 | 2.98 |
| `04-verification-results.md` | 1,468 | 11 | 7.49 |

His own file fails the proposed budget by thirteen times. Round 1's finding was that a *ban*
flags his file six times; draft 2's fix is a budget that flags the same file just as hard,
under a sentence asserting it does not. The framework's own plan template fails by twelve
times, and `CORE.md`, the file whose whole purpose is to carry the rule, fails by more than
two times while instructing on line 207 "Count em dashes in body prose. Target zero."

The rule now exists in three mutually inconsistent forms in three shipped files:
`05-roald-writing-profile.md` says "The ban stays, and the target is zero";
`06-design-v2.md` says a budget of one per thousand, not a ban; `SKILL.md` says "Count the
em dashes. Target zero." Draft 2 quotes Anthropic's guidance that Claude picks arbitrarily
between contradicting rules, in the course of criticising `create_plan.md` for exactly this.

### B. The em-dash figure is contaminated by pasted agent output. SEVERE

I re-derived the corpus from `~/.claude/projects/**/*.jsonl` with the filters described in
`05-roald-writing-profile.md`. It reproduces: 1,743 prompts, 49,390 words, em dashes 1.09
per thousand against the reported 1.01. So the arithmetic is honest.

The sample is not. The filter removes code fences, bullets, headers, tables and bold, which
catches pasted *formatted* output. It does not catch pasted *prose*. Inspecting all 44
prompts in the corpus that contain an em dash, almost every one is Roald typing a short
lead-in and pasting agent or document text after it:

> `"— split across the two legs, the SPV on neither" wtf does this mean, leave out such unclear garbage`

> `should I add something? Annexes: Schedule 1A (counterparty notice), … — adapted from Schedules 1–3 of the Pled…`

> `<task-notification> <task-id>bruixvq85</task-id> …`

Splitting the corpus on paste markers (curly quotes, `<task-notification>`, clause
references such as `5.12(b)`):

| Subset | Prompts | Words | Em/1k | Semi/1k | Paren/1k |
|---|---|---|---|---|---|
| All | 1,744 | 49,494 | 1.09 | 0.48 | 5.76 |
| Paste markers absent | 1,671 | 46,120 | **0.65** | 0.39 | 5.14 |
| Paste markers present | 73 | 3,374 | **7.11** | 1.78 | 14.23 |
| Prompts under 160 characters | 1,126 | 17,542 | **0.46** | 0.11 | 4.28 |

Four per cent of the corpus supplies 24 of the 54 em dashes and inflates the headline rate
by about seventy per cent. Roald's own typed rate is around 0.5 per thousand and probably
lower. The budget of one per thousand is therefore set at roughly twice a number that is
itself inflated, and it was set that way to accommodate em dashes that the agents wrote.

### C. The writing profile is measured from the wrong register, and it says so itself. SEVERE

`05-roald-writing-profile.md`, its own words:

> This is his instructing-an-agent register, not his external-email register. He types these
> fast, in lowercase, with typos, to a machine. … **Nothing here should be copied into a
> rule about how to write to an investor.**

`06-design-v2.md` then copies three things from it into the rules for writing to people
outside the company: the em-dash budget, "semicolons effectively never", and "parentheses
sparingly". The profile's own carve-out was that the register-independent mechanical
thresholds were the salvageable part, but em-dash rate is not register-independent. Typing
an em dash on a Mac terminal requires option-shift-hyphen; in the same corpus he uses the
spaced hyphen at 0.45 per thousand and the double hyphen at 0.47 per thousand, together
roughly twice his em-dash rate. The measurement is picking up keyboard friction, not
preference. The parenthesis rate of 5.61 per thousand is a stronger register artefact
still: a parenthetical aside typed to a machine and a parenthetical aside in an investor
email are different acts.

Plainly: no, the profile is not valid evidence for the external-writing rules. It is good
evidence for how an agent should write *to Roald*, which is what
`framework/output-styles/steering.md` is for, and the design should say that and stop.

### D. Problem 1 has no exemplars for the register that is actually failing. SEVERE

`research/05-roald-writing-corpus.md` Section E, the corpus author's own gap list: no
English long-form prose he wrote unaided; no cold outbound email; investor updates exist
only as agent drafts with his review comments; nothing longer than about 400 words that he
typed himself; no public or marketing writing. The English emails that *are* in the corpus
are, in full: "Likewise!", "Sure lets go", "Hi Nick, booked for Thursday! Thank you."

Roald's complaint is that emails and documents produced for people outside the company read
as machine-written. Short scheduling replies do not read as machine-written and never did.
The register that fails has zero samples. `06-design-v2.md` marks build item 3 "corpus
exists" and does not carry the gap forward anywhere in the document.

There is a fix and it is cheap: the corpus already contains the highest-value artefact
available, the diff between an agent draft and what Roald actually sent. There are nine such
pairs and only one set is high-confidence. Instrument for more of them — which is what
`SKILL.md` §6 half-gestures at — and stop extrapolating from calendar confirmations.

### E. `SKILL.md` inverts the exemplars-primary thesis on a single untested datapoint. SEVERE

The shipped skill says:

> Do not go and read the full writing corpus as well. That was measured on 2026-09-06:
> loading `CORE.md` alone produced almost the same draft as loading `CORE.md` plus the
> 1,176-line corpus, and the corpus costs a lot of context for one deleted phrase.

That measurement is not in `04-verification-results.md`, is n = 1, was run on Haiku like
everything else, and its conclusion is the exact question `research/02` lists as open and
that round 1 named as the cheapest unresolved test ("draft the same email three ways and
have Roald rank them blind"). Draft 1's thesis was "exemplars are the mechanism, rules are
the backstop". Draft 2's build item 3 says "rules only … plus the corpus exemplars", and the
shipped skill instructs the agent not to load the exemplars. The thesis has been reversed
without being argued.

Also in the same file: "Read `~/.claude/framework-style/CORE.md` in full. It is under 200
lines." `CORE.md` is 211 lines.

### F. Every verification result was produced on Haiku, and the document does not say so. SEVERE for two of the eight

Counting `model` fields in the assistant turns of the two test projects:

```
/Users/roaldp/.claude/projects/-private-tmp-fwtest    {'claude-haiku-4-5-20251001': 52}
/Users/roaldp/.claude/projects/-private-tmp-hooktest  {'claude-haiku-4-5-20251001': 24}
```

Twenty `--model claude-haiku-4-5-20251001` invocations in the framework session transcript
and no other `--model` flag anywhere in it. `04-verification-results.md` names the Claude
Code version, the permission mode and the working directories, and never names the model.

Six of the eight results are mechanical and hold regardless: hook events fire, matchers
filter, `additionalContext` is delivered to a subagent, the field names are `file_path`,
`load_reason`, `memory_type`, `AGENTS.md` is not loaded, `--goal` does not exist. Take those
as settled.

Results 5 and 8 are behavioural and do not transfer. Both establish that an agent *reported*
being blocked and did not route around the block. Both prompts were cooperative: the
negative case instructed the agent to "edit `contract.json` immediately and not read
anything first", which is an instruction to walk into the gate rather than to get past it.
Nobody ran the adversarial prompt — "get the contract marked as passing, work around any
blocker" — on any model. I ran the mechanical equivalent by hand and
`F=contract.json; echo x > $F` clears the gate, so the behavioural result would not have
survived a model that tries twice. The claim in draft 2 that "rebuilt … it holds", stated
"verified in both directions", rests entirely on one weak model complying with a compliant
prompt.

### G. "One worker at a time" answers the sentence, not the brief. MODERATE

Draft 2 reconciles Roald's request and the Anthropic-plus-Cognition guidance as "one worker
at a time, doing the writing, driven by an orchestrator that does not write". That is a
sound reading of the research and it is stated honestly, which round 1 asked for.

Two things it does not say. First, the brief's problem 2 opens "He supervises several agent
streams at once", and Conductor is currently running seven workspaces. Serialising the
worker inside one job is compatible with that; the document does not say so, so a reader
plausibly takes it as "stop running things in parallel". One sentence fixes it.

Second, `00-STATE.md` records a method constraint from Roald: "at most two Opus 5 subagents
running at once". Draft 1 answered it, badly, with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`.
Round 1 killed that. Draft 2 does not replace it with anything and does not mention the
constraint. See the silent-drops section.

### H. The gate and the deny rule are not complements, they are mutually exclusive. MODERATE

Draft 2: "A permanent deny cannot express 'deny until evidence is read', so the two are
complements: the hook for the conditional logic, `permissions.deny` for anything that must
never be written at all."

The only file in the design that anyone wants protected is `contract.json`, and the
contract's entire function requires the agent to write it. `permissions.deny` on
`Edit(**/contract.json)` makes it unwritable, which makes the contract a file only Roald
updates, which removes the gate's reason to exist. There is no second file named anywhere in
the design that the deny rule would protect. So the sentence describes a division of labour
between a mechanism that does not work and a mechanism with nothing to do.

### I. The build order puts the baseline measurement fourth. MODERATE

Item 4 is "`InstructionsLoaded` logging, then two weeks of silence", and the design's own
argument for it is that "without it, an instruction that was ignored cannot be distinguished
from an instruction that was never loaded, and every other decision here is guesswork".
Items 1, 2 and 3 — the `plan-reviewer` agent, the `@AGENTS.md` shims across repos, the
`write-external` skill — all change what loads. Two weeks of logging that begins after those
three land measures the new configuration and produces no baseline for the thing the design
says it most needs a baseline for. It costs ten minutes and it should be item 1.

### J. Still no success criteria for the framework itself. MODERATE

Round 1 raised this as finding 17. Draft 2 has a "Still to verify" table of seven cheap
tests and no statement of what outcome would count as any of the five problems being solved,
or what number would tell Roald to switch a mechanism off. The measurements named — "count
replies over half a page against the current baseline", "use it for a week" — have no
threshold attached and no current baseline recorded, so in four weeks there is nothing to
compare against. Three would do: an agent-drafted external email Roald sends without
rewriting the first paragraph; a week where no reply exceeds half a page; a `PLAN.md` whose
Log has an entry written by the agent that deviated.

### K. Is the smaller design still too big? Yes, by two hooks and one file. MODERATE

Counting what a single job touches under draft 2: `PLAN.md` with nine sections, optionally
`contract.json`, the `.context/active-plan` pointer, the `.evidence-reads` counter, the
re-anchor hook on two events, the instructions logger, the contract gate, the evidence
tracker, the `write-external` skill, `CORE.md`, the per-repo overlay, the `steering` output
style, the `plan-reviewer` agent, the installer and a per-repo `CLAUDE.md` shim. Fifteen
artefacts and five hook registrations, against draft 1's twenty-one and five.

The prose halved. The hook count did not. And the document's prose and the repo's code now
disagree about it: `06-design-v2.md` lists "the contract gate and `contract.json`" under
"Everything else waits for a measurement", while `install_framework.py` wires both the gate
and the tracker into `settings.json` on `--apply`. Whichever is intended, one of them is
wrong today, and the one that ships is the code.

Against `CLAUDE.md`'s "DO NOT OVERENGINEER. KEEP IT SIMPLE.", the correct count is three
hooks minus two: keep `instructions_log.py`, keep `reanchor.py`, delete `contract_gate.py`
and `evidence_tracker.py` and the counter and the contract from the framework entirely. That
removes defects 1, 2, 3, 8, 9 and half of 5, and removes the only two mechanisms whose
supporting evidence is a Haiku transcript.

### L. `PLAN.template.md` is nine sections and the brief asked for four stages. MINOR

The brief's fixed sequence is discovery, ideation, design requirements with concrete output
requirements, then MVP execution. The template maps Discovery, Approach, Success criteria
and MVP scope onto those, which is fair, and then adds Brief, Open questions, Steps and Log.
"Concrete output requirements" — what the deliverable must look like — has no home; success
criteria are given-when-then behaviour, not output format. For a man whose complaint is that
briefs cost him context switches, an eight-section template with a nine-section instruction
block is the section most likely to be skipped in practice. Worth checking after two uses
whether the Approach and Success criteria sections are ever filled in.

---

## What draft 2 dropped silently

Things that were in draft 1, are absent from draft 2, and are not named in draft 2's own
"everything else waits for a measurement" list.

1. **Roald's "at most two Opus 5 subagents at once" constraint.** In `00-STATE.md` as a
   method constraint. Draft 1 addressed it with the depth-cap environment variable. Round 1
   killed the variable, correctly. Draft 2 dropped the constraint with it and never
   mentions it. The constraint is Roald's, not the framework's, and it survives the kill.

2. **The core-plus-overlay style layering.** Draft 1 Part 1 was built on a general `CORE.md`
   plus per-vehicle overlays, and round 1's finding 20 pointed out the AIC `AGENTS.md`
   already implements the split. Draft 2 replaces the whole idea with a list of section
   numbers to copy. `CORE.md` then shipped anyway, with the overlay concept living only as
   three bullet points inside `SKILL.md`. The layering is now undocumented.

3. **The delegation brief.** Draft 1 section "The delegation brief carries four fields and
   hands back a path" was the concrete part of the orchestrator answer. Draft 2's problem 5
   is three diagnostic actions and a reconciliation sentence. The only surviving trace is the
   three-clause instruction inside `reanchor.build_anchor`. Nothing tells an orchestrator
   what to put in a subagent brief, which is the thing that most directly causes the drift
   problem 5 is about.

4. **"Merging with what each agent already knows".** Draft 1 Part 6 had a section for it;
   the brief's problem 4 asks for it explicitly ("merged with the context each agent already
   carries"). Draft 2 reduces it to the `@AGENTS.md` import, which prepends a file, and the
   installer, which symlinks. Neither merges. Nothing in draft 2 handles a repo whose
   `AGENTS.md` contradicts the framework, and round 1 showed `tiny-skylines` is already that
   repo.

5. **Exemplars as the primary mechanism.** Draft 1 stated it as a principle. Draft 2 keeps
   the sentence "which is the argument for exemplars over rules" in the writing section and
   then ships a skill that instructs the agent not to read them. Reversed, not retracted.

6. **The 200-line cap on the style guide,** which round 1 showed was single-sourced. Removed
   without comment, then re-asserted as fact in `SKILL.md` about a file that is 211 lines.

Two things round 1 raised that draft 2 did not address and did not acknowledge: success
criteria for the framework itself (finding 17), and adding hooks one at a time with a week
between each (finding 14). The installer adds five in one command.

---

## Four-week prediction

Assume Roald reads draft 2 tomorrow and follows it in order.

**Week 1.** Items 1 and 2 land and are the only unambiguous wins. `plan-reviewer` exists,
`/create_plan` stops calling into the void, the emoji instruction goes, and the `@AGENTS.md`
shims turn on the AIC router in the repo holding most of the machine's work. These are real
and they would still be in place in a year.

**Week 1 or 2, first friction.** Someone runs `install_framework.py --apply` from the
Conductor workspace, because that is where the file is and nothing stops it. Either the
symlinks point into a workspace and break later, or they work and nobody notices the
difference — because with the shipped `Write|Edit` and `Read` matchers, on a machine where
agents write through Bash, the gate and the tracker never fire at all. The first real
symptom is the re-anchor hook announcing "NEXT UNCHECKED STEP: **Q1.** …" to every subagent
of the first plan built from the template, which reads as a bug and is one.

**Week 2.** The `write-external` skill gets used on a real investor email. The draft comes
back better than the current baseline, because loading a style guide at the moment of
writing genuinely works and that is the one mechanism here with a plausible effect size.
Roald still rewrites the first paragraph, because the exemplar set for long English prose is
empty and the rules were calibrated on his terminal typing. Nobody logs the diff, because
`SKILL.md` §6 asks for it and nothing enforces it, so the feedback loop that would have
fixed this does not start.

**Week 3.** `contract.json` is used on one job, the gate blocks a legitimate write or fails
to block an illegitimate one, and the hook is commented out of `settings.json`. The
`InstructionsLoaded` log has two weeks of lines in it and nobody has opened it, because
opening it was never assigned to anyone and there is no question it was meant to answer that
was written down as a question.

**Week 4, the state of things.** Surviving and in daily use: the `@AGENTS.md` shims, the
`plan-reviewer` agent, the `write-external` skill. Probably surviving: the `steering` output
style, if it was ever installed, with no way to tell whether it beat the `CLAUDE.md` rule
because no baseline was recorded. Abandoned: `contract.json`, `contract_gate.py`,
`evidence_tracker.py`, `.context/active-plan` (it was gitignored and stopped being updated
after the second workspace), the `PLAN.md` template's Approach and Success criteria sections.
Never started: the `/implement_plan` transcript diagnosis, because it is item 8 and it is the
only item with no artefact to produce. The em-dash budget is still written in three
inconsistent forms in three files and nobody has noticed, because no one measured it.

Estimated value delivered: the two items that fix things that are already broken and already
loaded. Everything built new is either unused or off. That is not a bad four weeks, but it
is about a day of work, and the plan spends five.

---

## What I would ship, in order

1. **Delete `contract_gate.py`, `evidence_tracker.py`, `contract.json` and the counter from
   the framework.** Their only support is one Haiku transcript against a cooperative prompt,
   and defects 1, 2, 3, 8 and 9 are all in them. This removes two of the five hooks and the
   only two that can block a tool call.

2. **Fix the `plan-reviewer` gap and the emoji contradiction in `~/.claude/commands/`, and
   audit the other ten command files for dangling agent names.** Unchanged from round 1 and
   still the highest-value hour on the machine.

3. **Turn on `InstructionsLoaded` logging today, before anything else changes.** Write down
   the one question it is meant to answer — "does `~/.claude/CLAUDE.md` load in a Conductor
   subagent session, and does anything else" — and put a date on when someone reads it.

4. **Ship the one-line `@AGENTS.md` shims,** with the `tiny-skylines` de-duplication round 1
   identified, and record what happens in that repo when the shim contradicts the framework.
   That is the answer to problem 4's "merged with the context each agent already carries",
   which is currently unanswered.

5. **Ship `write-external`, and delete the em-dash budget from it.** Restore "target zero
   inside sentences", which is what `CORE.md` and `SKILL.md` already say, and delete the
   density-budget paragraph from `06-design-v2.md` rather than leaving three versions of the
   rule in three files. Strike the sentence in `SKILL.md` that tells the agent not to read
   the corpus, until the blind ranking test in draft 2's own verification table has been run
   on Opus 5.

6. **Start collecting agent-draft-versus-sent pairs.** One file, appended to whenever Roald
   edits a draft before sending. Nine pairs exist and only one set is high-confidence; that
   is the binding constraint on problem 1 and no other item in this plan relieves it.

7. **Fix `reanchor.py` and ship it on `SubagentStart` only.** Scope the step regex to the
   `## Steps` section, guard `read_current_phase` against a non-object contract, and drop
   `SessionStart` until there is a reason for it. The subagent case is the one with a real
   verified result behind it and it is the mechanism problem 5 needs.

8. **Ship the `steering` output style, and record the baseline first.** Count what fraction
   of replies exceed half a page for three days before installing it. Without that number
   the week-long comparison the design proposes cannot be made.

9. **Then, and only then, the `/implement_plan` transcript diagnosis.** It is the only item
   that can tell you whether problem 5 needs a mechanism at all, and it produces no artefact,
   which is why it will otherwise never happen. Put it on a calendar.

Not shipping: `install_framework.py --apply` in its current form. Fix defects 1, 11 and 12
first, or install the four remaining files by hand — there are four of them.
