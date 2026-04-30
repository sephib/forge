# Proposal: CI Hint Command via GitHub PR Comment

**Author:** eshulman2
**Date:** 2026-04-30
**Status:** Draft

## Summary

When Forge is stuck in a CI fix loop it cannot resolve on its own, there is currently no way to give it guidance without manually fixing the code yourself. This proposal adds a `/forge hint <message>` PR comment command that injects human-provided context into the next `attempt_ci_fix` invocation and resets the attempt counter, giving the agent a fresh start with the additional information.

## Motivation

### Problem Statement

Forge's CI fix loop is fully autonomous — it reads the CI failure logs, attempts a fix, pushes, and waits for the next result. When it gets stuck (e.g. misidentifying the root cause, missing domain knowledge about the project), the only options are:

1. Wait for it to exhaust retries, then manually fix the code and push
2. Use `/forge skip-gate` to bypass the check entirely
3. Patch the Redis checkpoint directly

None of these let you keep Forge in the driver's seat while nudging it in the right direction. If you know *why* the fix is wrong — e.g. "this test requires the Octavia service to be enabled in devstack" — you should be able to tell Forge that without having to write the fix yourself.

### Current Workarounds

- **Skip gate**: Works when the failure is infrastructure-related and can be safely ignored. Not applicable when the fix is within reach but Forge is missing context.
- **Manual fix**: Takes Forge out of the loop and negates the automation benefit.
- **Wait and retry**: Only works if Forge eventually converges, which isn't guaranteed with a missing context problem.

## Proposal

### Overview

Add `/forge hint <message>` as a GitHub PR comment command. When detected during a CI stage, Forge:

1. Stores the hint in workflow state (`ci_fix_hint`)
2. Resets `ci_fix_attempts` to 0, giving the agent a fresh retry budget
3. Waits for the next CI gate failure before acting — if the agent already fixed it on its own, the hint is never used
4. On the next failure, injects the hint into the `attempt_ci_fix` prompt as additional context

### Detailed Design

#### Command syntax (GitHub PR comment)

```
/forge hint The test_octavia suite requires Octavia to be enabled in devstack — add "octavia" to enabled_services in the e2e workflow
```

Only one active hint is supported at a time. A new `/forge hint` replaces the previous one.

#### Command detection — `_handle_resume_event` in `worker.py`

Extend the existing GitHub `issue_comment` handler alongside the skip-gate logic:

```python
HINT_PREFIX = "/forge hint"

if comment_body.lower().startswith(HINT_PREFIX.lower()):
    hint = comment_body[len(HINT_PREFIX):].strip()
    # Store hint and reset attempt counter
    await self._checkpoint.aput(
        config,
        {
            **current_state,
            "ci_fix_hint": hint,
            "ci_fix_attempts": 0,
        },
        {},
    )
    # Post acknowledgement on PR
    await self._post_hint_feedback(ticket_key, pr_number, repo, hint)
```

The hint is stored but the workflow is **not immediately resumed** — it stays paused at `wait_for_ci_gate`. The hint only takes effect on the next CI failure. If CI passes without further intervention, the hint is never used.

#### State schema

```python
class CIIntegrationState(TypedDict, total=False):
    ci_fix_hint: str | None   # NEW: human-provided context for next fix attempt
    ci_fix_attempts: int
    ci_skipped_checks: list[str]
    ...
```

Initialized to `None`. Cleared after it is consumed (i.e. after the first `attempt_ci_fix` that uses it), so it doesn't persist across subsequent failures.

#### Prompt injection — `attempt_ci_fix` in `ci_evaluator.py`

```python
hint = state.get("ci_fix_hint")
if hint:
    prompt += f"\n\n**Human hint:** {hint}\n\nUse this context to guide your fix."
    # Clear the hint after use
    state = {**state, "ci_fix_hint": None}
```

#### Attempt counter reset

Resetting `ci_fix_attempts` to 0 when a hint is provided is intentional: the previous failures happened without the context the hint provides, so they shouldn't count against the budget. The agent gets a full fresh set of retries with the new information.

#### Feedback comments

**GitHub PR reply** (immediately after hint is stored):
```
💡 Hint received from @eshulman2

The following context will be injected into the next CI fix attempt:
> The test_octavia suite requires Octavia to be enabled in devstack — add "octavia" to enabled_services in the e2e workflow

Retry counter reset. Forge will use this hint on the next CI failure.
If CI is already passing, the hint will not be used.
```

**Jira audit comment**:
```
CI fix hint provided on GitHub PR by eshulman2:
> The test_octavia suite requires Octavia to be enabled...

Retry counter reset to 0. Hint will be injected into the next fix attempt.
```

### User Experience

```
# Forge has tried 3 fixes. It keeps removing the wrong devstack service.
# Engineer reads the logs and spots the issue.

[PR #773 comment by eshulman2]
/forge hint The e2e job needs Octavia enabled — add "octavia,o-api,o-hm,o-cw,o-hk"
             to enabled_services in .github/workflows/e2e.yaml

[Forge reply on PR #773]
💡 Hint received from @eshulman2
> The e2e job needs Octavia enabled...
Retry counter reset. Forge will use this hint on the next CI failure.

# CI fails again on the next push (or Forge re-triggers). Forge now has the hint.

[Forge, on next attempt_ci_fix]
# Agent reads hint, updates e2e.yaml correctly, pushes fix.

[CI passes. Forge moves to human review.]
```

## Alternatives Considered

| Alternative | Pros | Cons | Why Not |
|-------------|------|------|---------|
| Jira comment hint | Consistent with Jira-based feedback | CI context belongs next to the failure on GitHub | Mismatch between where the problem lives and where you provide context |
| Resume immediately on hint | Faster feedback loop | Wastes a fix attempt if CI hasn't re-run yet; hint fires into a stale failure | Wait for next gate failure is the right trigger point |
| Keep previous attempt count | Simpler | Hint is useless if budget is already exhausted | Counter must reset — that's the whole point of providing context |
| Multiple concurrent hints | More flexible | Ambiguous ordering; hints could contradict each other | One active hint at a time; new hint replaces old |

## Implementation Plan

### Phases

1. **Phase 1: State + prompt injection** — Add `ci_fix_hint` to state schema and initial states; inject into `attempt_ci_fix` prompt and clear after use. (~1 hour)
2. **Phase 2: Command detection** — Parse `/forge hint` from `issue_comment` events in `worker.py`; reset attempt counter; store hint in checkpoint. (~2 hours)
3. **Phase 3: Feedback comments** — Post GitHub PR acknowledgement and Jira audit comment. (~1 hour)
4. **Phase 4: Tests** — Unit tests for hint injection, counter reset, hint clearing after use, and command detection. (~half day)

### Dependencies

- [ ] `ci_fix_hint` added to `create_initial_feature_state` and `create_initial_bug_state`
- [ ] GitHub `issue_comment` webhook already delivered — no new permissions required
- [ ] `_post_hint_feedback` helper following the same pattern as `_post_skip_gate_feedback`

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hint resets counter and agent still can't fix it, burning more CI resources | Med | Low | Hint only resets once per hint — subsequent failures still count toward the new budget |
| Hint contains incorrect information that leads the agent further astray | Low | Med | Hint is visible on the PR for reviewers to see; audit comment in Jira; engineer still reviews the resulting code change |
| Engineer provides hint at wrong workflow stage | Low | Low | Command only active at CI stages (`wait_for_ci_gate`, `ci_evaluator`, `attempt_ci_fix`); Forge posts explanation otherwise |

## Open Questions

- [ ] Should the hint be cleared if CI passes without being used, or kept for the lifetime of the PR in case CI fails again later?
- [ ] Should Forge quote the hint back in its commit message or PR description update so it's auditable in git history?
