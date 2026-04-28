# Epic: [Epic Title]

## Overview

[2-3 sentences describing this Epic's purpose and value]

## Scope

### Included
- [Capability 1]
- [Capability 2]

### Excluded
- [What this Epic does NOT cover]

## Technical Architecture

### Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| [name] | [what it does] | [stack] |

### Data Model

```
[Entity]
├── [field]: [type]
├── [field]: [type]
└── [relationship] -> [OtherEntity]
```

### API/Interface Design

```
[METHOD] /api/v1/[resource]
  Request: [schema summary]
  Response: [schema summary]
```

## Implementation Approach

### Phase 1: Foundation
1. [Task 1]
2. [Task 2]

### Phase 2: Core Logic
1. [Task 1]
2. [Task 2]

### Phase 3: Integration
1. [Task 1]
2. [Task 2]

## Dependencies

### Internal
- [Dependency on other Epic or existing system]

### External
- [Third-party service, library, or team]

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| [risk] | H/M/L | H/M/L | [strategy] |

## Acceptance Criteria

- [ ] [Criterion 1 - verifiable outcome]
- [ ] [Criterion 2 - verifiable outcome]
- [ ] [Criterion 3 - verifiable outcome]

## Estimated Complexity

- **T-Shirt Size**: S / M / L / XL
- **Story Points**: [estimate]
- **Reasoning**: [why this estimate]

## Testing Strategy

| Test Type | Coverage | Automation |
|-----------|----------|------------|
| Unit | [what] | Yes |
| Integration | [what] | Yes |
| E2E | [what] | Yes/No |
