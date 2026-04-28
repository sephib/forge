# Technical Specification

**Document Version**: 1.0
**Date**: [current date]
**Status**: Draft
**Parent PRD**: [ticket key]

---

## 1. Overview

[1-2 sentences: what behavior this spec defines. Do not repeat PRD rationale or business context.]

---

## 2. User Scenarios

### Priority Legend
- **P1**: Critical path — must work for MVP
- **P2**: Important — required for full release
- **P3**: Enhancement — can be deferred

### 2.1 P1 Scenarios (Critical)

#### SC-001: [Scenario Name]
**Preconditions**: [Required state before scenario executes]
**Trigger**: [What initiates this scenario]

**Acceptance Criteria**:
```gherkin
Given [initial context]
  And [additional context if needed]
When [action performed]
Then [expected outcome]
  And [additional outcome if needed]
```

**Edge Cases**:
- [Edge case]: [Expected behavior]

---

<!-- Add SC-002, SC-003 etc. as needed. Only add P2/P3 sections if there are P2/P3 scenarios grounded in the PRD. -->

## 3. Functional Requirements

### 3.1 Core Functions

| ID | Function | Description | Inputs | Outputs |
|----|----------|-------------|--------|---------|
| FN-001 | [name] | [what it does] | [params] | [return value] |

### 3.2 Business Rules

| ID | Rule | Condition | Action |
|----|------|-----------|--------|
| BR-001 | [name] | [when] | [then] |

---

## 4. Interface Changes

<!-- Use this section for whatever interface this feature touches. Pick the subsection(s) that apply and delete the rest. -->

### 4.1 Configuration Schema [if adding config fields]

```yaml
# Show the new/changed fields with types and descriptions
field_name: "type - required/optional - description"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| [field] | string | No | [value] | [description] |

### 4.2 API Endpoints [if adding/changing API endpoints]

```
[METHOD] /api/v1/[resource]
```

**Request**:
```json
{
  "field": "type - description"
}
```

**Response (Success)**:
```json
{
  "field": "type - description"
}
```

**Status Codes**:
| Code | Condition |
|------|-----------|
| 200 | Success |
| 400 | Validation error |
| 404 | Not found |

---

## 5. State Management [omit if not applicable]

### 5.1 State Transitions

| From | To | Trigger | Guard |
|------|----|---------|-------|
| [state] | [state] | [event] | [condition] |

---

## 6. Error Handling

### 6.1 Error Scenarios

<!-- Match error style to the stack: field.ErrorList for Go/CLI, HTTP codes for REST APIs. -->

| Scenario | Error | Resolution |
|----------|-------|------------|
| [what went wrong] | [exact error text or code] | [how user fixes it] |

---

## 7. Non-Functional Requirements [omit if none are feature-specific]

| Requirement | Target | Category |
|-------------|--------|----------|
| [metric] | [value] | Performance / Compatibility / Security |

---

## 8. Testing Requirements

### 8.1 Test Scenarios

| ID | Scenario | Type | Priority | Automated |
|----|----------|------|----------|-----------|
| TS-001 | [scenario description] | Unit / Integration / E2E | P1/P2/P3 | Yes/No |

---

## 9. Open Questions [omit if none are genuinely unresolved]

| ID | Question | Owner | Resolution |
|----|----------|-------|------------|
| Q-001 | [question not answered in PRD] | [who decides] | Pending |
