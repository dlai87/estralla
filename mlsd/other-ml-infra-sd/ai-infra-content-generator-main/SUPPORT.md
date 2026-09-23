# Support

Thank you for using the AI Infrastructure Content Generator! This document provides resources for getting help and support.

## Quick Links

- 📖 [Documentation](docs/)
- 🐛 [Report a Bug](https://github.com/ai-infra-curriculum/ai-infra-content-generator/issues/new?template=bug_report.yml)
- 💡 [Request a Feature](https://github.com/ai-infra-curriculum/ai-infra-content-generator/issues/new?template=feature_request.yml)
- 💬 [Discussions](https://github.com/ai-infra-curriculum/ai-infra-content-generator/discussions)
- 🔒 [Security Issues](SECURITY.md)

---

## Getting Started

### First Time Here?

1. **Read the Documentation**:
   - Start with [Getting Started Guide](docs/getting-started.md)
   - Review [Architecture Overview](docs/architecture.md)
   - Check [Best Practices](docs/best-practices.md)

2. **Explore Examples**:
   - Look at templates in `templates/`
   - Review workflows in `workflows/`
   - Check validation tools in `validation/`

3. **Generate Your First Module**:
   - Follow [Module Generation Workflow](workflows/module-generation.md)
   - Use templates from `templates/lecture-notes/`
   - Run validation: `python validation/completeness/check-module-completeness.py`

### Common Getting Started Questions

**Q: What AI model should I use?**
A: The framework is system-agnostic. Works with Claude, GPT-4, or any LLM. See [Tools and Automation](docs/tools-and-automation.md) for recommendations.

**Q: How long does it take to generate a module?**
A: 8-12 hours for a complete 12,000+ word module with examples, case studies, and exercises.

**Q: Can I use this for non-technical content?**
A: Yes! While designed for technical curriculum, the framework adapts to any educational content.

---

## Help Resources

### Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [Getting Started](docs/getting-started.md) | Quick start guide | New users |
| [Architecture](docs/architecture.md) | System design | All users |
| [Best Practices](docs/best-practices.md) | Content quality tips | Content creators |
| [Tools & Automation](docs/tools-and-automation.md) | MCP servers, skills | Advanced users |
| [Agent Playbook](docs/agent-playbook.md) | Large-scale projects | Program managers |

### Workflows

| Workflow | Use Case | Time Estimate |
|----------|----------|---------------|
| [Module Generation](workflows/module-generation.md) | Single module | 8-12 hours |
| [Project Generation](workflows/project-generation.md) | Hands-on project | 15-24 hours |
| [Curriculum Design](workflows/curriculum-design.md) | Full curriculum | 65-110 hours |
| [Multi-Role Program](workflows/multi-role-program.md) | Multi-role coordination | 2-3 days/role |

### Templates

| Type | Location | Purpose |
|------|----------|---------|
| Lecture Notes | `templates/lecture-notes/` | Module structure |
| Exercises | `templates/exercises/` | Hands-on practice |
| Projects | `templates/projects/` | Portfolio projects |
| Assessments | `templates/assessments/` | Quizzes and tests |
| Research | `templates/research/` | Market research |
| Curriculum | `templates/curriculum/` | Program planning |
| Solutions | `templates/solutions/` | Solution packaging |

---

## Getting Help

### 1. Search Existing Resources

Before asking for help:

- ✅ Search [existing issues](https://github.com/ai-infra-curriculum/ai-infra-content-generator/issues)
- ✅ Check [documentation](docs/)
- ✅ Review [discussions](https://github.com/ai-infra-curriculum/ai-infra-content-generator/discussions)
- ✅ Read relevant [workflows](workflows/)

### 2. GitHub Discussions

For general questions, ideas, and community help:

**👉 [GitHub Discussions](https://github.com/ai-infra-curriculum/ai-infra-content-generator/discussions)**

**Categories**:
- 💬 **Q&A**: Ask questions, get answers
- 💡 **Ideas**: Suggest improvements
- 🙌 **Show and Tell**: Share what you've created
- 📣 **Announcements**: Stay updated
- 🤝 **General**: Everything else

**Discussion Guidelines**:
- Search before posting
- Use descriptive titles
- Provide context and examples
- Be respectful and constructive
- Mark helpful answers

### 3. GitHub Issues

For bugs, feature requests, and specific problems:

**👉 [Open an Issue](https://github.com/ai-infra-curriculum/ai-infra-content-generator/issues/new/choose)**

**When to Use Issues**:
- 🐛 Found a bug
- 💡 Have a feature request
- 📝 Documentation needs improvement
- 🔧 Validation tools not working
- 🔗 Broken links or references

**Issue Templates**:

#### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Run command '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**:
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.9.7]
- Framework version: [e.g., 0.2.0]

**Additional context**
Any other relevant information.
```

#### Feature Request Template
```markdown
**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
What other approaches did you consider?

**Additional Context**
Mockups, examples, or references.
```

### 4. Security Issues

For security vulnerabilities:

**👉 See [SECURITY.md](SECURITY.md)**

**DO NOT** open public issues for security vulnerabilities.

---

## Troubleshooting

### Common Issues

#### Issue 1: Validation Scripts Not Working

**Symptoms**: `python validation/code-validators/validate-code-examples.py` fails

**Solutions**:
```bash
# Ensure Python 3.9+
python --version

# Install optional dependencies
pip install markdown

# Check file path is correct
ls validation/code-validators/validate-code-examples.py

# Run with full path
python /full/path/to/validate-code-examples.py yourfile.md
```

#### Issue 2: Module Generation Takes Too Long

**Symptoms**: Generating content takes 20+ hours

**Solutions**:
- Break into smaller chunks (one section at a time)
- Use more specific prompts
- Leverage MCP servers for acceleration (see docs/tools-and-automation.md)
- Consider using Claude Code skills

#### Issue 3: Generated Code Has Errors

**Symptoms**: Code examples don't run or have syntax errors

**Solutions**:
```bash
# Always validate generated code
python validation/code-validators/validate-code-examples.py lecture-notes.md

# Test code manually
python -c "import ast; ast.parse(open('example.py').read())"

# Use linters
pylint your_code.py
```

#### Issue 4: Word Count Too Low

**Symptoms**: Module has < 12,000 words

**Solutions**:
```bash
# Check current count
wc -w lecture-notes.md

# Use completeness checker
python validation/completeness/check-module-completeness.py lecture-notes.md

# Expand thin sections (see prompts/lecture-generation/)
# Add more code examples
# Expand case studies with metrics
# Add troubleshooting section
```

#### Issue 5: Templates Not Loading

**Symptoms**: Can't find templates

**Solutions**:
```bash
# Verify you're in the correct directory
pwd

# Check if templates exist
ls templates/

# Use full paths if needed
cp /full/path/to/templates/lecture-notes/module-template.md ./
```

### Getting Unstuck

If you're stuck:

1. **Check the relevant workflow** (workflows/)
2. **Review templates** for structure examples
3. **Search issues** for similar problems
4. **Ask in Discussions** for community help
5. **Open an issue** if you found a bug

---

## Community

### Contributing

Want to contribute? We'd love your help!

**👉 See [CONTRIBUTING.md](CONTRIBUTING.md)**

**Ways to Contribute**:
- 📝 Improve documentation
- 🎨 Create new templates
- 🔧 Build validation tools
- 💡 Share prompts that work well
- 🐛 Report bugs
- ⭐ Star the repository
- 📣 Spread the word

### Code of Conduct

We are committed to providing a welcoming and inclusive community.

**👉 See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**

**Key Points**:
- Be respectful and constructive
- Help newcomers
- Focus on what's best for the community
- Accept feedback gracefully
- Report unacceptable behavior

---

## Additional Resources

### External Resources

**AI Tools**:
- [Claude](https://claude.ai/) - Anthropic's AI assistant
- [Claude Code](https://docs.claude.com/en/docs/claude-code) - Official CLI
- [ChatGPT](https://chat.openai.com/) - OpenAI's AI assistant

**Educational Content Creation**:
- [Bloom's Taxonomy](https://cft.vanderbilt.edu/guides-sub-pages/blooms-taxonomy/) - Learning objectives
- [Backward Design](https://cte.rice.edu/blogarchive/2022/7/28/backward-design) - Curriculum planning
- [ADDIE Model](https://www.instructionaldesign.org/models/addie/) - Instructional design

**Technical Writing**:
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/welcome/)
- [Write the Docs](https://www.writethedocs.org/)

### Learning Resources

**Curriculum Design**:
- Understanding by Design (book)
- The Wiley Handbook of Learning Technology
- Curriculum Development: A Guide to Practice

**AI-Assisted Content Creation**:
- Anthropic Claude Documentation
- OpenAI Documentation
- Prompt Engineering Guide

---

## Response Times

We aim for the following response times:

| Request Type | Target Response | Who Responds |
|--------------|----------------|--------------|
| Security Issue | 48 hours | Maintainers |
| Bug Report | 3-5 business days | Maintainers |
| Feature Request | 7 days | Maintainers |
| Discussion Question | 2-3 days | Community |
| Pull Request | 3-7 days | Maintainers |

**Note**: These are targets, not guarantees. Response times may vary based on maintainer availability and issue complexity.

---

## Contact

### Primary Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, community
- **Security**: See SECURITY.md for security-specific contact

### Additional Contact

- **Project Organization**: https://github.com/ai-infra-curriculum
- **Repository**: https://github.com/ai-infra-curriculum/ai-infra-content-generator

---

## Feedback

We value your feedback! Help us improve:

- 📝 **Documentation unclear?** Open an issue or PR
- 🐛 **Found a bug?** Report it
- 💡 **Have an idea?** Start a discussion
- ⭐ **Like the project?** Star it and tell others

---

**Thank you for using the AI Infrastructure Content Generator!**

We're here to help you create amazing educational content.

---

**Last Updated**: 2025-01-04
**Version**: 0.2.0
