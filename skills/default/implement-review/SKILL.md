---
name: implement-review
description: Analyze PR review comments against the current codebase, classify every comment, and produce a structured plan. No comment may be silently dropped.
---

# PR Review Analysis Skill

You are analyzing code review feedback on a pull request. Your workspace contains the full repository. Use your tools to understand the code, not just the diff.

## Workflow

1. Read the review comments from `.forge/review-comments.md`
2. Understand the current state of the code:
   - Run `git log --oneline -10` to see recent commits
   - Run `git diff origin/main..HEAD --stat` to see what changed
   - Read the specific files mentioned in the review comments
   - Use `grep` to find the relevant code sections
3. For each review comment, assign exactly one category:
   - **ACTIONABLE**: you agree the change is correct and will implement it
   - **CONTESTED**: you have a strong technical objection (contradicts the spec, introduces a bug, or is factually wrong)
   - **ACKNOWLEDGED**: you have seen and understood the comment but will not implement it — because it reflects an intentional design decision, is genuinely ambiguous, is out of scope for this PR, or requires a separate discussion

   **Every comment must appear in one of the three output sections. No comment may be silently dropped.**

4. Write your analysis to `.forge/review-plan.md` (always) and optionally `.forge/review-objections.md`.

### `.forge/review-plan.md` (always write this file)

Structure with three sections. Omit a section entirely if it has no items.

```
# Review Plan

## Actionable Items

### Item N: <short title>

**File:** path/to/file.go
**Location:** function name or line range
**Change:** what to do and why

---

## Acknowledged (not addressed)

### <short title>

**Reviewer said:** brief summary of the comment
**Reason not addressed:** concise explanation — e.g. "intentional design per spec section X",
"ambiguous — the reviewer's own note says this is debatable", "out of scope for this fix"

---

## Contested (objections filed in review-objections.md)

### <short title>

One-line note that a full objection is filed separately.
```

### `.forge/review-objections.md` (only if there are CONTESTED items)

```
## Contested: <short title>

**Reviewer said:** exact quote of the review comment
**Why I object:** technical reasoning (spec reference, potential bug, factual error)
**Counter-proposal:** what I suggest instead (if anything)
```

## Important

- Read the actual source files — do not guess at the code structure
- **Every comment must be explicitly classified** — acknowledged comments are not ignored, they are consciously deferred with a reason the human reviewer can see
- Base objections and acknowledgements on technical facts, not preferences
- Be specific about file paths and line numbers
- Do NOT make any code changes in this phase — analysis only
