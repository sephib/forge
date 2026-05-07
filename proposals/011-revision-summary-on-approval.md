# Proposal: Revision Summary on Artifact Approval

**Author:** eshulman2
**Date:** 2026-05-07
**Status:** Draft

## Summary

When a user approves a PRD or spec that went through one or more revision cycles, post a structured summary comment to Jira listing each round of feedback and what changed in response. This mirrors the existing Q&A summary (proposal 001) and gives reviewers a concise audit trail of how the artifact evolved before it was approved.

## Motivation

### Problem Statement

Revisions happen iteratively: a reviewer posts feedback, Forge regenerates, the reviewer checks again. By the time approval comes, the Jira thread contains interleaved feedback comments, acknowledgment messages, and updated artifact content — often across many comments. There is no consolidated record of "here's what was asked for and here's what changed."

This matters for:
- **Async reviewers** who join after approval and want to understand why the artifact looks the way it does
- **The implementing team** who may need to understand the intent behind a design decision that came out of a revision
- **Audit / retrospective** use cases where teams want to understand how requirements evolved

### Current Workarounds

Reviewers must scroll through the full Jira comment history and manually reconstruct the revision chain. The implicit trail is there (feedback comment → acknowledgment comment → updated artifact) but it is not surfaced as a coherent summary anywhere.

## Proposal

### Overview

Add a `revision_history` list to workflow state, populated during each regeneration. On artifact approval, call `post_revision_summary_if_needed()` to post a formatted summary comment to Jira — structured identically to how `post_qa_summary_if_needed()` works for Q&A.

Each revision entry records the feedback and a brief agent-generated summary of what changed. This "change note" is produced as a side effect of the regeneration node: the agent is already generating the revised artifact, so it can emit a one-sentence changelog at the same time.

### Detailed Design

#### State Changes

```python
# In WorkflowState (base.py or feature/state.py)
revision_history: list[dict[str, str]]
# Each entry: {feedback, change_note, artifact_type, timestamp}
```

`revision_history` is initialized to `[]` and never cleared mid-workflow (unlike `feedback_comment`, which is cleared after each regeneration). It accumulates across all revision rounds for a given artifact type.

#### Regeneration Nodes

In `regenerate_prd_with_feedback()` and `regenerate_spec_with_feedback()`, after the agent produces the revised content, record the revision:

```python
revision_history = state.get("revision_history", [])
revision_history.append({
    "feedback": state["feedback_comment"],
    "change_note": result.change_note,   # new field from agent response
    "artifact_type": "prd",              # or "spec"
    "timestamp": datetime.utcnow().isoformat(),
})
```

The `change_note` is a one-sentence description of what changed — e.g., "Removed the microservices split and consolidated into a single service per the reviewer's request." The agent already has this context; we just need to ask for it explicitly in the `regenerate.md` prompt.

#### Prompt Change (`regenerate.md`)

Add an instruction to produce a `change_note` field alongside the revised document. The simplest approach is to ask for a brief (one sentence) plain-text summary of the main change made, returned as a labelled prefix before the document body, which the node parser strips out and stores separately.

#### New Utility (`src/forge/workflow/utils/revision_summary.py`)

```python
async def post_revision_summary_if_needed(
    state: WorkflowState,
    jira: JiraClient,
    artifact_type: str,
) -> None:
    history = [
        e for e in state.get("revision_history", [])
        if e["artifact_type"] == artifact_type
    ]
    if not history:
        return

    lines = [f"*Revision history ({len(history)} round(s)):*\n"]
    for i, entry in enumerate(history, 1):
        lines.append(f"*Feedback {i}:* {entry['feedback']}")
        lines.append(f"*Change {i}:* {entry['change_note']}\n")

    await jira.add_comment(state["ticket_key"], "\n".join(lines))
```

#### Approval Gates

In `prd_approval.py` and `spec_approval.py`, call the revision summary alongside the existing Q&A summary when routing to the next stage:

```python
await post_qa_summary_if_needed(state, jira, "prd")
await post_revision_summary_if_needed(state, jira, "prd")
```

### User Experience

After a two-round revision cycle, approval triggers this Jira comment alongside the existing Q&A summary:

```
*Revision history (2 round(s)):*

*Feedback 1:* The auth section assumes OAuth but we use SAML internally — please update.
*Change 1:* Replaced the OAuth flow with SAML-based SSO and updated FR-004 accordingly.

*Feedback 2:* The rate limiting numbers seem arbitrary — add a rationale.
*Change 2:* Added rationale for the 100 req/min limit based on the p99 load analysis in the requirements.
```

If there were no revisions (first draft approved), no summary comment is posted.

## Alternatives Considered

| Alternative | Pros | Cons | Why Not |
|-------------|------|------|---------|
| Feedback only (no change note) | Simpler — no prompt change needed | Reader still can't tell what actually changed without reading the full artifact diff | Loses half the value of the summary |
| Full artifact diff per revision | Complete audit trail | Very verbose, expensive to produce, Jira comment size limits | Over-engineered for the use case |
| Rely on Jira comment history | Zero implementation cost | Unstructured, requires manual reconstruction | The whole point of this proposal is to avoid that |
| Post after every regeneration, not just on approval | More immediate visibility | Creates noise during active revision; summary is most useful as a stable record at approval | Approval is the right checkpoint |

## Implementation Plan

### Phases

1. **Phase 1: State + history tracking** — ~half a day
   - Add `revision_history` to state
   - Populate in `regenerate_prd_with_feedback()` and `regenerate_spec_with_feedback()`
   - Store feedback + timestamp; use placeholder `""` for change_note initially

2. **Phase 2: Change note from agent** — ~1 day
   - Update `regenerate.md` prompt to produce a one-sentence change note
   - Update node parser to extract and store it
   - Update `regenerate_with_feedback()` in `agent.py` to return the change note alongside the content

3. **Phase 3: Summary utility + gate integration** — ~half a day
   - Implement `post_revision_summary_if_needed()` in `src/forge/workflow/utils/revision_summary.py`
   - Call it from `prd_approval.py` and `spec_approval.py` on approval routing

### Dependencies

- [x] `qa_history` pattern (exists — this proposal follows it directly)
- [x] `regenerate_prd_with_feedback()` / `regenerate_spec_with_feedback()` (exist)
- [x] `post_qa_summary_if_needed()` (exists — blueprint for the new utility)
- [ ] `regenerate.md` prompt update to emit change notes

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent produces verbose or unhelpful change notes | Medium | Low | Constrain prompt to one sentence; reviewers can ignore if low quality |
| Prompt change causes regression in regeneration quality | Low | High | Gate behind a prompt version bump; test on a few tickets before full rollout |
| Revision history grows large for heavily-iterated tickets | Low | Low | Jira comment size limit is generous; no action needed for MVP |

## Open Questions

- [ ] Should plan and task revisions be included too, or just PRD and spec for the initial version?
- [ ] Should the change note be agent-generated or inferred from a diff of the artifact content? (Agent-generated is simpler; diff-based is more reliable but adds complexity.)
- [ ] Should the revision summary and Q&A summary be merged into a single "session history" comment, or kept as separate comments?

## References

- [001-qa-mode-for-generated-artifacts.md](001-qa-mode-for-generated-artifacts.md) — the pattern this proposal mirrors
- `src/forge/workflow/utils/qa_summary.py` — implementation to replicate
- `src/forge/workflow/nodes/prd_generation.py` — primary integration point
- `src/forge/workflow/nodes/spec_generation.py` — primary integration point
