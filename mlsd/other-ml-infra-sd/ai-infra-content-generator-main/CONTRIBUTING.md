# Contributing to AI Infrastructure Content Generator

Thank you for your interest in contributing to this project! This framework aims to help educators and content creators build high-quality technical curriculum using AI assistance.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Contribution Guidelines](#contribution-guidelines)
- [Quality Standards](#quality-standards)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

---

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to ai-infra-curriculum@joshua-ferguson.com.

**Key Points**:
- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

For full details, see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## How Can I Contribute?

There are many ways to contribute to this project:

### 1. Improve Documentation

- **Fix typos or clarify explanations** in existing documentation
- **Add examples** showing how to use the framework
- **Create tutorials** for specific use cases
- **Translate documentation** to other languages
- **Improve README** with better explanations or examples

### 2. Enhance Templates

- **Create new templates** for different content types
- **Improve existing templates** with better structure
- **Add template variations** for different learning styles
- **Document template usage** with examples

### 3. Develop Prompts

- **Create new AI prompts** for content generation
- **Refine existing prompts** for better results
- **Add prompt variations** for different contexts
- **Share successful prompts** you've discovered

### 4. Build Validation Tools

- **Write validation scripts** for automated quality checks
- **Create linters** for content standards
- **Build completeness checkers** for curriculum coverage
- **Develop testing frameworks** for code examples

### 5. Contribute Workflows

- **Document new workflows** for content generation
- **Share best practices** from your experience
- **Create workflow automation** scripts
- **Improve existing workflows** with lessons learned

### 6. Share Examples

- **Provide sample modules** showing target quality
- **Share generated projects** that worked well
- **Document case studies** of successful usage
- **Create before/after examples** showing improvements

### 7. Report Issues

- **Report bugs** in templates or documentation
- **Suggest improvements** to existing content
- **Request new features** that would be valuable
- **Identify missing documentation** or unclear sections

### 8. Review Contributions

- **Review pull requests** from other contributors
- **Test proposed changes** in your environment
- **Provide constructive feedback** on submissions
- **Help maintainers** by triaging issues

---

## Getting Started

### Prerequisites

Before contributing, make sure you have:

1. **Git** installed and configured
2. **GitHub account** with SSH keys set up
3. **Text editor** (VS Code, Vim, etc.)
4. **Markdown knowledge** for documentation
5. **AI tool access** (Claude, GPT-4, etc.) for testing prompts

### Fork and Clone

1. **Fork the repository** to your GitHub account
2. **Clone your fork** locally:
   ```bash
   git clone git@github.com:YOUR_USERNAME/ai-infra-content-generator.git
   cd ai-infra-content-generator
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream git@github.com:ai-infra-curriculum/ai-infra-content-generator.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. **Keep your fork updated**:
   ```bash
   git fetch upstream
   git merge upstream/main
   ```
2. **Make your changes** in your feature branch
3. **Test your changes** thoroughly
4. **Commit with clear messages**:
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a pull request** from your fork to the main repository

---

## Contribution Guidelines

### Documentation Contributions

**File Naming**:
- Use lowercase with hyphens: `my-document.md`
- Be descriptive: `module-generation-workflow.md` not `workflow1.md`

**Markdown Style**:
- Use ATX-style headers (`#` not underlines)
- Include table of contents for docs > 500 words
- Use fenced code blocks with language identifiers
- Add line breaks between sections for readability

**Content Standards**:
- Write in clear, concise language
- Use active voice when possible
- Define technical terms when first used
- Include examples to illustrate concepts
- Add links to related documentation

### Template Contributions

**Structure Requirements**:
- Include clear section headers
- Provide detailed instructions in comments
- Add examples for each section
- Document expected word counts or lengths
- Include validation criteria

**Quality Standards**:
- Templates must be production-ready
- Follow best practices for content type
- Include metadata (role, duration, prerequisites)
- Provide clear guidance for AI generation
- Test template with actual content generation

### Prompt Contributions

**Prompt Format**:
- Start with clear objective statement
- Include context and constraints
- Specify output format and structure
- Add quality criteria
- Include examples of good output

**Testing Requirements**:
- Test prompt with multiple AI models
- Verify output meets quality standards
- Document any model-specific variations
- Include expected output examples
- Note any limitations or edge cases

### Code Contributions

**Validation Scripts**:
- Write in Python 3.9+ or Bash
- Include docstrings and comments
- Add error handling
- Provide usage examples
- Include tests

**Style Guidelines**:
- Python: Follow PEP 8
- Bash: Follow Google Shell Style Guide
- Use meaningful variable names
- Add type hints (Python)
- Keep functions focused and small

### Workflow Contributions

**Documentation Structure**:
- Overview and objectives
- Prerequisites
- Step-by-step instructions
- Expected outputs
- Troubleshooting section
- Time estimates
- Examples

**Quality Requirements**:
- Workflows must be tested end-to-end
- Include real examples
- Document common issues
- Provide troubleshooting guidance
- Add time estimates for each step

---

## Quality Standards

### Minimum Requirements

All contributions must meet these standards:

**Documentation**:
- No spelling or grammatical errors
- Clear, professional language
- Properly formatted Markdown
- Working links (no 404s)
- Code examples that work

**Templates**:
- Complete structure
- Clear instructions
- Production-ready quality
- Tested with actual generation
- Includes validation criteria

**Prompts**:
- Clear objectives
- Specific constraints
- Output format defined
- Tested with AI tools
- Documented limitations

**Code**:
- Passes linting
- Includes tests
- Has documentation
- Error handling present
- Security considerations addressed

### Review Criteria

Pull requests will be reviewed for:

1. **Correctness**: Does it work as intended?
2. **Quality**: Meets minimum standards?
3. **Completeness**: All required sections present?
4. **Clarity**: Easy to understand and use?
5. **Consistency**: Follows project conventions?
6. **Testing**: Has it been tested?
7. **Documentation**: Is usage documented?

---

## Submitting Changes

### Pull Request Process

1. **Ensure your changes meet quality standards**
2. **Update documentation** if you've changed functionality
3. **Add tests** for new code
4. **Update CHANGELOG.md** with your changes
5. **Write a clear PR description**:
   - What problem does this solve?
   - How does it solve it?
   - Any breaking changes?
   - Screenshots (if applicable)
   - Testing performed

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Template improvement
- [ ] Prompt enhancement
- [ ] Workflow addition
- [ ] Code/tooling

## Testing
- [ ] Tested locally
- [ ] All examples work
- [ ] Documentation builds
- [ ] Links verified
- [ ] Code passes linting

## Checklist
- [ ] Follows project style guidelines
- [ ] Self-reviewed my code
- [ ] Commented complex sections
- [ ] Updated documentation
- [ ] Added tests (if applicable)
- [ ] No breaking changes (or documented)
```

### Commit Message Guidelines

Use clear, descriptive commit messages:

**Format**:
```
<type>: <brief description>

<optional detailed description>

<optional footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: Add project template for hands-on exercises

docs: Improve getting-started guide with examples

fix: Correct word count calculation in validation script

refactor: Reorganize template directory structure
```

### Review Process

1. **Automated checks** run on your PR
2. **Maintainer reviews** your changes
3. **Feedback provided** if changes needed
4. **Iterate** based on feedback
5. **Approval and merge** when ready

**Response Times**:
- Initial review: Within 3-5 business days
- Follow-up reviews: Within 1-2 business days
- Small fixes: May be merged quickly
- Large changes: May take longer for thorough review

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, questions
- **GitHub Discussions**: General discussion, ideas, help
- **Pull Requests**: Code and content contributions

### Getting Help

If you need help:

1. **Check existing documentation** in the `docs/` directory
2. **Review the [Support Guide](SUPPORT.md)** for troubleshooting and resources
3. **Search issues** for similar questions
4. **Open a discussion** for general questions
5. **Open an issue** for bugs or specific problems
6. **Tag maintainers** if urgent

For detailed help resources, troubleshooting guides, and response times, see [SUPPORT.md](SUPPORT.md).

### Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in [CHANGELOG.md](CHANGELOG.md) for their contributions
- Acknowledged in release notes for significant contributions

See [CHANGELOG.md](CHANGELOG.md) for the full history of contributions and releases.

---

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

## Questions?

Don't hesitate to ask questions! We're here to help:

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Feature requests**: Open a GitHub Issue with "enhancement" label
- **Security issues**: Email maintainers directly (see SECURITY.md)

---

**Thank you for contributing to making technical education more accessible through AI-assisted content generation!**
