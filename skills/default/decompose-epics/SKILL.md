---
name: decompose-epics
description: Decompose a Technical Specification into implementable Epics with technical plans. Use when asked to break down features, create epics, or plan implementation.
---

# Epic Decomposition Skill

Decompose a specification into 2-5 implementable Epics using the template and guidelines below.

## Instructions

1. Read the template from `plugins/forge-sdlc/templates/epic-template.md`
2. Analyze the specification content
3. Identify 2-5 cohesive capability areas
4. Create detailed implementation plan for each
5. Map dependencies between Epics
6. Validate against the quality checklist

## Decomposition Rules

1. **Cohesive**: Each Epic represents a single, deployable capability.
2. **Independent**: Minimize dependencies between Epics.
3. **Vertical Slices**: Prefer end-to-end slices over horizontal layers.
4. **Sized Right**: Each Epic should be 1-3 sprints of work.
5. **Clear Boundaries**: No overlap between Epics.

## Epic Naming Convention

Use format: `[Verb] [Noun] [Qualifier]`

Examples:
- "Implement User Authentication System"
- "Create Dashboard Analytics Module"
- "Build Notification Delivery Pipeline"

## Ordering Principles

1. **Foundation First**: Infrastructure/setup Epics before feature Epics
2. **Dependencies**: Dependent Epics come after their dependencies
3. **Value Delivery**: Higher-value Epics earlier when possible
4. **Risk Reduction**: Technical risk Epics early to fail fast

## Quality Checklist

Before returning the Epic breakdown:

- [ ] 2-5 Epics total (not more, not fewer)
- [ ] Each Epic has clear, non-overlapping scope
- [ ] Dependencies between Epics documented
- [ ] Technical approach is specific (not generic)
- [ ] Complexity estimates provided
- [ ] Acceptance criteria are verifiable
- [ ] Implementation is phased logically
- [ ] All specification scenarios covered across Epics

## Output Format

For each Epic, use this format:

```
---
EPIC: [Epic Title]
PLAN:
[Full epic content following plugins/forge-sdlc/templates/epic-template.md]
---
```

Repeat for each Epic (2-5 total).

IMPORTANT: Return ONLY the Epic content. Do not include any planning text, explanations of what you're doing, or meta-commentary. Start directly with the first Epic.
