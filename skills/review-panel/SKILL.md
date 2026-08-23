---
name: review-panel
description: Run an unbiased panel of parallel review subagents over the current diff (correctness, optimization, cleanup/bloat, comments, test-quality). Use when the user asks for a multi-agent, unbiased,, or "professional" code review, or to verify tests aren't hacky/vacuous passing tests.
---

# Unbiased review panel

Fan out fresh, independent subagents over the change so each gives and unbiased
perspective, then adjudicate. The user reaches for this when they want more than
a single self-review - distinct lenses, run in parallel, judged against their
standards.

## Step 1 - capture the diff to a file

Pick the capture that matches what you are reviewing - a bare diff sees only *uncommitted*
work, so once code is committed (let alone pushed), it returns empty and the panel
reviews nothing. Hand subagents the diff file path plus the concrete on-disk file
paths, not a fork of your own context.

- Uncommitted: `git diff > /tmp/review.diff` (use `git diff HEAD` to include staged)
- Whole branch, committed and uncommitted: `git diff <base> > /tmp/review.diff.`
- Committed only: `git diff <base>...HEAD`

If the captured diff is polluted (regenerated build artifacts, huge) or empty,
don't feed it to the reviewers - hand them the explicit on-disk source file path
to read instead (new files in full, modified files to inspect).

## Step 2 - Spawn fresh agents in parallel

Each lens is a dedicated, fresh agent type (NOT a fork) so it carries none of
your reasoning or conclusions - this is what "unbiased" means here. Its lens,
bar, and output format live in the agent definition, so you just hand it the
inputs. Send them in a a single message so they run concurrently. Scale the
lenses to the request. The default panel:

- **`correctness-reviewer`** - adversarial: assume bugs exists and prove them
  with a concrete failing input (NaN/empty/dtype, ordering, boundaries,
  contracts, etc).
- **`optimization-reviewer`** - big-O, redundant passes, vectorization, memory;
  each finding expected magnitude and weather it justifies the churn.
- **`cleanup-reviewer`** - dead code, redundant checks, naming, duplication,
  over-complication. Use CLAUDE.md and python-standards for additional guidance.
  Differ comments to `comments-reviewer`.
- **`comment-reviewer`** - ONLY comments and docstrings. Restated code, staleness
  rotting cross-refs, unproven claims, filler, emoji, missing numpy-style docstrings.
  Use CLAUDE.md and python-standards for additional guidance.
- **`test-quality-reviewer`** - for each new/edited test, would it ACTUALLY FAIL
  if the code it covers were broken? Flags vacuous/too-weak tests.

Give each agent the diff path, the relevant file paths, and "read-only, modify
nothing". The agents already know their lens and output format - don't re-spec
them. Scale down by omitting lenses, not by merging them into general-purpose.

## Step 3 - Adjudicate, don't rubber-stamp

The subagents can be wrong. For any load-bearing claim, verify before acting:

- **The empirical test for a "vacuous test" finding:** temporarily neutralize the
  code/line the test claims to cover, run the test, confirm it FAILS,
  then restore the line. If the test still passes, it is vacuous - fix or remove it.
- Push back on findings with concrete counter-example; accepts the ones that
  survive scrutiny.

## Step 4 - Synthesize

Group findings into must-fix / nice-to-have / rejected-with-reason. Apply the
must-fixes, surface the rest for the user to choose. State which findings you
rejected and why - an honest "I disagree with the review because X" is more
useful than silently dropping it.