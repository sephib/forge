---
name: generate-tasks
description: Break down Epic implementation plans into concrete, actionable Tasks. Use when decomposing Epics into implementation units.
---

# Task Generation Skill

Generate implementation Tasks from Epic plans following the guidelines below.

## Instructions

1. Analyze the Epic implementation plan
2. Identify discrete, testable units of work (2-8 hours each)
3. Define clear acceptance criteria for each Task
4. Identify which repository each Task belongs to
5. Order Tasks by dependency (foundation first)

## Task Sizing Rules

1. **Atomic**: Each Task should be completable in a single PR
2. **Testable**: Clear acceptance criteria that can be verified
3. **Independent**: Minimize dependencies between Tasks where possible
4. **Sized Right**: 2-8 hours of work per Task

## Output Format

For each Task, use this format:

```
---
TASK: [Task Title]
REPO: [repository-name or "unknown"]
DESCRIPTION:
[Detailed implementation steps]

ACCEPTANCE_CRITERIA:
- [Criterion 1]
- [Criterion 2]
---
```

Repeat for each Task (typically 3-10 Tasks per Epic).

## Quality Checklist

Before returning the Task breakdown:

- [ ] Each Task is atomic and completable in one PR
- [ ] Acceptance criteria are specific and testable
- [ ] Dependencies are identified and ordered correctly
- [ ] Repository assignments are clear
- [ ] No gaps - full Epic coverage across all Tasks
