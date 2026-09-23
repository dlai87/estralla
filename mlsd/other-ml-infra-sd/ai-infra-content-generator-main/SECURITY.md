# Security Policy

## Overview

The AI Infrastructure Content Generator is a framework for creating educational content. While the framework itself doesn't handle sensitive data or run services, we take security seriously to ensure the content and tools we provide are safe to use.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 0.2.x   | :white_check_mark: | Current release |
| < 0.2.0 | :x:                | Not supported |

## Security Considerations for This Project

### 1. Generated Content Security

**AI-Generated Code Examples**:
- All code examples should be reviewed for security vulnerabilities before use
- Examples may contain patterns that are insecure in production environments
- Users must validate and test code in safe environments

**Validation Tools**:
- Our validation scripts (`validation/code-validators/`) check for common security issues
- These checks are not comprehensive - manual security review is required
- See `validation/code-validators/validate-code-examples.py` for what we check

### 2. Template and Prompt Security

**Prompt Injection Risks**:
- Templates and prompts are designed for use with AI models
- Users should validate AI-generated output before using in production
- Never include sensitive data in prompts or templates

**Script Execution**:
- Validation scripts run locally and don't send data externally
- Review script source before running: `validation/code-validators/` and `validation/completeness/`
- Scripts only read files - they don't modify or transmit data

### 3. Dependency Security

**Python Dependencies**:
```python
# Current dependencies (as of validation scripts):
- No external dependencies for core framework
- Optional: pylint, bandit (for code validation)
- Optional: markdown (for validation tools)
```

**Keeping Dependencies Updated**:
- Check for updates monthly: `pip list --outdated`
- Review changelogs before updating
- Test validation scripts after updates

## Reporting a Vulnerability

### What to Report

Please report security vulnerabilities if you discover:

1. **Code Example Vulnerabilities**:
   - SQL injection, XSS, command injection in examples
   - Hardcoded credentials or secrets in templates
   - Insecure cryptographic implementations
   - Authentication/authorization bypasses

2. **Script Security Issues**:
   - Code execution vulnerabilities in validation scripts
   - Path traversal in file operations
   - Unsafe file handling
   - Dependency vulnerabilities

3. **Framework Design Issues**:
   - Prompt injection vectors in templates
   - Insecure patterns recommended in best practices
   - Misleading security guidance

### What NOT to Report

These are not security vulnerabilities:

- General content quality issues (use regular issues)
- Outdated technology versions in examples (use regular issues)
- AI models producing incorrect content (this is expected - see our disclaimer)
- Missing features or documentation gaps

### How to Report

**For Security Issues** (private disclosure):

1. **Email**: ai-infra-curriculum@joshua-ferguson.com
   - Subject: "[SECURITY] Brief description"
   - Include:
     - Description of the vulnerability
     - Steps to reproduce
     - Potential impact
     - Suggested fix (if you have one)

2. **Do NOT**:
   - Open a public GitHub issue for security vulnerabilities
   - Discuss the vulnerability publicly until it's fixed
   - Exploit the vulnerability

**Response Timeline**:
- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity (see below)

### Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **Critical** | Immediate risk to users | 24-48 hours | RCE in validation script |
| **High** | Significant security impact | 3-7 days | SQL injection in code example |
| **Medium** | Limited security impact | 14 days | Insecure pattern in template |
| **Low** | Minimal security impact | 30 days | Outdated security advice |

## Security Best Practices for Users

### When Using This Framework

1. **Review All Generated Content**:
   ```bash
   # Always run validation before using
   python validation/code-validators/validate-code-examples.py lecture-notes.md
   ```

2. **Test in Safe Environments**:
   - Never run generated code in production without testing
   - Use isolated environments for testing
   - Review all code for security issues

3. **Validate AI Output**:
   - AI models can generate insecure code
   - Cross-reference with official security documentation
   - Use static analysis tools (bandit, semgrep, etc.)

4. **Keep Dependencies Updated**:
   ```bash
   # Check for updates
   pip list --outdated

   # Update validation tools
   pip install --upgrade pylint bandit
   ```

5. **Sanitize Sensitive Data**:
   - Never include real credentials in examples
   - Use placeholder values (.env.example)
   - Remove any sensitive data before committing

### When Contributing

1. **Code Examples**:
   - Follow OWASP Top 10 guidelines
   - Include security best practices
   - Document security considerations
   - No hardcoded secrets

2. **Validation Scripts**:
   - Validate all file paths (prevent path traversal)
   - Use safe file operations
   - Don't execute arbitrary code
   - Limit resource usage

3. **Templates and Prompts**:
   - Warn about security considerations
   - Provide secure examples
   - Document common vulnerabilities
   - Include security review checklist

## Security Features

### Built-In Protections

1. **Code Validation**:
   - Checks for hardcoded credentials
   - Identifies SQL injection patterns
   - Detects command injection risks
   - See: `validation/code-validators/validate-code-examples.py`

2. **Content Review Checklist**:
   - Security section in quality checklist
   - Production readiness validation
   - See: `validation/content-checkers/module-quality-checklist.md`

3. **Best Practices Documentation**:
   - Security guidelines in templates
   - OWASP Top 10 references
   - Secure coding patterns

### Limitations

**What We Don't Protect Against**:
- AI models generating insecure code (users must review)
- Vulnerabilities in user-added code
- Misuse of framework for malicious purposes
- Security issues in external dependencies of generated code

## Disclosure Policy

### Our Commitments

1. **Transparency**:
   - We will acknowledge security reports within 48 hours
   - We will provide regular updates on remediation progress
   - We will credit reporters (unless they prefer anonymity)

2. **Coordinated Disclosure**:
   - We will work with reporters to fix issues before public disclosure
   - We request 90 days for remediation before public disclosure
   - We will notify affected users before public disclosure

3. **Recognition**:
   - Security researchers will be credited in release notes
   - We will maintain a security hall of fame (if applicable)

### Disclosure Timeline

```
Day 0:    Vulnerability reported
Day 1-2:  Initial response and triage
Day 3-7:  Verification and impact assessment
Day 7-30: Fix development and testing
Day 30:   Patch release (for high/critical)
Day 90:   Public disclosure (coordinated with reporter)
```

## Security Updates

### How We Communicate Security Issues

1. **GitHub Security Advisories**: For all security fixes
2. **Release Notes**: Security fixes noted in CHANGELOG.md
3. **Security Email List**: (If established) Subscribe for security notifications

### Applying Security Updates

```bash
# Pull latest changes
git pull origin main

# Check CHANGELOG.md for security fixes
cat CHANGELOG.md | grep -i security

# Review SECURITY.md for any new guidance
cat SECURITY.md
```

## Additional Resources

### Security Tools for Generated Content

**Static Analysis**:
```bash
# Python
pip install bandit pylint safety
bandit -r src/
safety check

# JavaScript
npm install -g eslint
npx eslint --plugin security src/
```

**Dependency Scanning**:
```bash
# Python
pip install pip-audit
pip-audit

# JavaScript
npm audit
```

**Container Scanning** (if applicable):
```bash
# Docker images
docker scan your-image:tag

# Trivy
trivy image your-image:tag
```

### Security Learning Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [SANS Secure Coding](https://www.sans.org/cyber-security-courses/secure-coding/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Questions?

For non-security questions:
- Open an issue: https://github.com/ai-infra-curriculum/ai-infra-content-generator/issues
- See SUPPORT.md for help resources

For security concerns:
- Email: ai-infra-curriculum@joshua-ferguson.com
- Subject: "[SECURITY] Your concern"

---

**Last Updated**: 2025-01-04
**Version**: 0.2.0
