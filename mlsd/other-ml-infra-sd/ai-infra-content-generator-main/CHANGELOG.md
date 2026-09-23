# Changelog

All notable changes to the AI Infrastructure Content Generator framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Example module generation demonstrating complete workflow
- Quick start tutorial for first-time users
- Claude Code skill for automated content generation
- Additional validation scripts for links and formatting

### Added
- GitHub issue templates for bug reports and feature requests (`.github/ISSUE_TEMPLATE/`)
- Curriculum project plan template (`templates/curriculum/project-plan-template.md`) and documentation references
- AI Infrastructure Curriculum end-to-end guide (`docs/ai-infrastructure-curriculum-guide.md`)

### Changed
- Support policy now focuses on the latest release (see `SECURITY.md`)
- README framework statistics updated to reflect current repository size

---

## [0.2.0] - 2025-01-04

### Added

#### Multi-Role Program Support
- **Research Framework**: Complete market research and skills analysis toolkit
  - `templates/research/` - Role research, job posting analysis, practitioner interviews, skills matrix templates
  - `prompts/research/` - AI prompts for role research and skills synthesis
  - `research/` directory structure with README guide
- **Curriculum Planning Framework**: Structured multi-role curriculum coordination
  - `templates/curriculum/` - Master plans, module roadmaps, multi-role alignment dashboard, repository strategy
  - `curriculum/` directory structure with README guide
- **Solutions Framework**: Standardized solution packaging for all content types
  - `templates/solutions/` - Exercise, project, and assessment solution templates
  - `prompts/solutions/` - Solution generation prompts
- **Multi-Role Orchestration Workflow**: `workflows/multi-role-program.md` - End-to-end process for coordinating research and curriculum across multiple job roles

#### Enhanced Workflows
- Updated `workflows/curriculum-design.md` with research template integration and multi-role alignment
- Updated `workflows/project-generation.md` with repository strategy and solution placement guidance
- Updated `workflows/module-generation.md` for consistency

#### Community & Governance Files
- `CODE_OF_CONDUCT.md` - Contributor Covenant with educational content guidelines
- `CHANGELOG.md` - This file, tracking all changes
- `SECURITY.md` - Security policy and vulnerability reporting
- `SUPPORT.md` - Support resources and help channels

### Changed
- **README.md**:
  - Added multi-role capabilities to feature list
  - Updated framework statistics (37 files, ~49,000 words)
  - Fixed LICENSE reference
  - Removed non-existent `examples.md` from structure
  - Added research and solutions framework documentation sections
  - Updated version to 0.2.0
- **Architecture documentation** updated to reflect new directory structure

### Fixed
- LICENSE reference in README (was "to be added", now properly linked)
- Removed broken reference to non-existent `docs/examples.md`
- Corrected word count statistics to reflect actual content
- Version number updated from 0.1.0 to 0.2.0

### Total Impact
- **New Files**: 23 files (15 new templates/workflows, 4 community files, 4 updated workflows)
- **New Content**: ~15,000 words of templates, workflows, and documentation
- **New Capabilities**: Multi-role program orchestration, research framework, solutions framework

---

## [0.1.0] - 2025-01-03

### Added

#### Core Framework
- **Documentation** (~75,000 words):
  - `docs/getting-started.md` - Quick start guide (8,300 words)
  - `docs/architecture.md` - System design and 8-phase workflow (12,500 words)
  - `docs/best-practices.md` - Content generation best practices (15,400 words)
  - `docs/tools-and-automation.md` - 30 MCP servers, 6 skills, automation (20,500 words)
  - `docs/agent-playbook.md` - 8-phase agent orchestration (10,800 words)

#### Templates
- `templates/lecture-notes/module-template.md` - Comprehensive lecture note structure (3,800 words)
- `templates/exercises/exercise-template.md` - Hands-on exercise template (2,400 words)
- `templates/projects/hands-on-project-template.md` - Project template (6,000 words)
- `templates/assessments/quiz-assessment-template.md` - Quiz and assessment template (4,000 words)

#### AI Prompts
- `prompts/lecture-generation/comprehensive-module-prompt.md` - Module generation prompt (4,200 words)
- `prompts/code-generation/production-code-examples-prompt.md` - Code generation guidelines (5,000 words)
- `prompts/case-studies/industry-case-study-prompt.md` - Case study framework (6,500 words)

#### Workflows
- `workflows/module-generation.md` - Complete module generation process (7,800 words)
- `workflows/project-generation.md` - Project creation workflow (5,000 words)
- `workflows/curriculum-design.md` - Curriculum design methodology (6,000 words)

#### Validation Tools
- `validation/code-validators/validate-code-examples.py` - Automated code quality validation (Python script)
- `validation/completeness/check-module-completeness.py` - Module completeness checker (Python script)
- `validation/content-checkers/module-quality-checklist.md` - Quality checklist (6,100 words)

#### Community Files
- `CONTRIBUTING.md` - Comprehensive contribution guidelines
- `LICENSE` - MIT License with AI content disclaimer
- `README.md` - Project overview and documentation

### Framework Features
- System-agnostic AI content generation
- Template-driven approach for consistency
- Built-in quality validation
- 12,000+ word module standard
- Production-ready code examples
- Real-world case studies
- Comprehensive assessment materials

### Total Content
- **Files**: 20+ templates, workflows, and tools
- **Documentation**: ~75,000 words
- **Standards**: Quality checklist with 100+ validation points

---

## Version History Summary

| Version | Date | Key Changes | Files Added | Status |
|---------|------|-------------|-------------|--------|
| 0.2.0 | 2025-01-04 | Multi-role support, research & solutions frameworks | 23 | Current |
| 0.1.0 | 2025-01-03 | Initial framework release | 20+ | Released |

---

## Upgrade Guide

### Upgrading from 0.1.0 to 0.2.0

**New Capabilities**:
- Multi-role program orchestration
- Research framework for market analysis
- Solutions framework for all content types

**Breaking Changes**: None - all v0.1.0 workflows remain compatible

**Migration Steps**:
1. Pull latest changes: `git pull origin main`
2. Review new `workflows/multi-role-program.md` for multi-role features
3. Optional: Set up research templates for your role(s)
4. Optional: Configure repository strategy using `templates/curriculum/repository-strategy-template.yaml`

**New Files to Explore**:
- `workflows/multi-role-program.md` - Start here for multi-role orchestration
- `templates/research/` - Market research templates
- `templates/curriculum/` - Curriculum planning templates
- `templates/solutions/` - Solution packaging templates

---

## Contributing to This Changelog

When contributing to this project:

1. **Add your changes** to the `[Unreleased]` section under the appropriate category:
   - `Added` for new features
   - `Changed` for changes in existing functionality
   - `Deprecated` for soon-to-be removed features
   - `Removed` for now removed features
   - `Fixed` for any bug fixes
   - `Security` for vulnerability fixes

2. **Include details**:
   - File names or paths affected
   - Brief description of the change
   - Impact on users (if significant)

3. **On release**, a maintainer will:
   - Move `[Unreleased]` items to a new version section
   - Add release date
   - Update version links at bottom of file

---

## Links

- [Repository](https://github.com/ai-infra-curriculum/ai-infra-content-generator)
- [Issues](https://github.com/ai-infra-curriculum/ai-infra-content-generator/issues)
- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

---

[Unreleased]: https://github.com/ai-infra-curriculum/ai-infra-content-generator/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ai-infra-curriculum/ai-infra-content-generator/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ai-infra-curriculum/ai-infra-content-generator/releases/tag/v0.1.0
