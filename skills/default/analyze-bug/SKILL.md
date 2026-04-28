---
name: analyze-bug
description: Generate Root Cause Analysis (RCA) for bugs using TDD methodology. Use when analyzing bug reports.
---

# Bug Analysis Skill

Analyze bugs and generate Root Cause Analysis with TDD fix approach.

## Instructions

1. Analyze the bug report symptoms
2. Identify affected components
3. Determine the root cause
4. Propose a TDD-based fix approach

## Analysis Framework

### Symptom Collection
- What is the observed behavior?
- What is the expected behavior?
- When does it occur?
- Who is affected?

### Component Analysis
- Which systems/modules are involved?
- What are the data flows?
- Where are the integration points?

### Root Cause Investigation
- What changed recently?
- What assumptions were violated?
- Where is the actual defect?

## Output Format

```markdown
## Summary
[One paragraph bug summary]

## Root Cause Analysis

### Symptoms
- [Observable symptom 1]
- [Observable symptom 2]

### Affected Components
- [Component 1]: [How affected]
- [Component 2]: [How affected]

### Root Cause
[Detailed explanation of what went wrong and why]

### Chain of Events
1. [Initial trigger]
2. [Subsequent effect]
3. [Eventual failure]

## Proposed Fix (TDD Approach)

### Test First
Write tests that:
1. [Test case 1 - reproduces the bug]
2. [Test case 2 - verifies correct behavior]

### Implementation
[Description of the fix approach]

### Verification
[How to verify the fix is complete]

## Prevention
[How to prevent similar bugs in the future]
```

## Quality Checklist

- [ ] Root cause clearly identified
- [ ] Chain of events documented
- [ ] Test cases defined before fix
- [ ] Fix approach is minimal and focused
- [ ] Prevention strategy included
