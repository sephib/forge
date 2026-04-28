---
name: review-code
description: Perform AI code review analyzing pull requests for quality, security, and specification alignment. Use for PR reviews.
---

# Code Review Skill

Review code changes for quality, security, and spec alignment.

## Instructions

1. Analyze the code diff provided
2. Check for code quality issues
3. Identify security vulnerabilities
4. Verify alignment with specifications
5. Provide actionable feedback

## Review Criteria

### Code Quality
- Clean, readable code
- Proper error handling
- No obvious bugs or logic errors
- Appropriate use of language features
- DRY principle followed

### Security
- No hardcoded secrets or credentials
- Input validation present
- No SQL injection, XSS, or other OWASP Top 10 vulnerabilities
- Secure authentication/authorization patterns
- Safe file operations

### Spec Alignment
- Code implements the requirements
- Edge cases handled per spec
- API contracts match specification
- Test coverage for acceptance criteria

### Best Practices
- Following project conventions
- Consistent code style
- Appropriate documentation
- Meaningful variable/function names

## Output Format

```markdown
## Summary
[One paragraph overall assessment]

## Issues Found
- [SEVERITY: critical/major/minor] [Issue description]
  - File: path/to/file
  - Line: X
  - Suggestion: [How to fix]

## Approval Decision
[APPROVE if no critical/major issues, REQUEST_CHANGES otherwise]

## Comments
[Optional additional feedback]
```

## Severity Definitions

- **critical**: Security vulnerabilities, data loss risks, breaking changes
- **major**: Bugs, spec violations, significant quality issues
- **minor**: Style issues, minor improvements, suggestions
