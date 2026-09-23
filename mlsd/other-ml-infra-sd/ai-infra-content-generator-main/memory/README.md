# Memory & Checkpoint System

This directory contains tools for saving and resuming content generation work across sessions. The checkpoint system enables you to pause long-running content generation tasks and resume them later without losing progress.

## Overview

Content generation often spans multiple sessions, especially for comprehensive modules (12,000+ words) or multi-role curricula. The checkpoint system allows you to:

- **Save Progress**: Snapshot your current work with metadata
- **Resume Work**: Restore files and context from any checkpoint
- **Track Milestones**: Record completion of major stages
- **Verify Integrity**: Ensure files are correctly restored
- **Manage Sessions**: Handle multiple parallel generation efforts

## Directory Structure

```
memory/
├── README.md                    # This file
├── checkpoint-save.py           # Save checkpoint tool
├── checkpoint-resume.py         # Resume checkpoint tool
├── checkpoints/                 # Saved checkpoints (created automatically)
│   ├── module-05_20250104_143022/
│   │   ├── checkpoint.json      # Checkpoint metadata
│   │   ├── CHECKPOINT_SUMMARY.md # Human-readable summary
│   │   └── files/               # Saved files
│   └── curriculum-design_20250104_150530/
│       ├── checkpoint.json
│       ├── CHECKPOINT_SUMMARY.md
│       └── files/
└── templates/                   # Checkpoint templates (optional)
    └── checkpoint-template.json
```

## Quick Start

### Saving a Checkpoint

```bash
# Save checkpoint for module generation
cd modules/mod-005-docker-containers
python ../../memory/checkpoint-save.py \
  --name "module-05" \
  --stage "case-studies" \
  --notes "Completed 3 case studies, working on 4th"

# Save with specific files
python memory/checkpoint-save.py \
  --name "project-review" \
  --stage "final" \
  --files lecture-notes.md exercises/*.md \
  --notes "Ready for review"

# Save entire working directory
python memory/checkpoint-save.py \
  --name "curriculum-batch" \
  --stage "module-03" \
  --context ./working-modules
```

### Resuming from Checkpoint

```bash
# Resume from latest checkpoint
python memory/checkpoint-resume.py \
  --name "module-05" \
  --latest

# Resume from specific timestamp
python memory/checkpoint-resume.py \
  --name "module-05" \
  --timestamp 20250104_143022

# Dry run (preview what would be restored)
python memory/checkpoint-resume.py \
  --name "module-05" \
  --latest \
  --dry-run

# Restore to different directory
python memory/checkpoint-resume.py \
  --name "module-05" \
  --latest \
  --target ./restored-work
```

### Listing Checkpoints

```bash
# List all checkpoints
python memory/checkpoint-save.py --list
python memory/checkpoint-resume.py --list

# List checkpoints for specific name
python memory/checkpoint-resume.py --list --name "module-05"
```

## Use Cases

### 1. Module Generation (8-12 hours)

**Scenario**: Generating a comprehensive 12,000+ word module over 2 days

```bash
# Day 1 - After completing sections 1-4
python memory/checkpoint-save.py \
  --name "mod-105-data-pipelines" \
  --stage "section-4-complete" \
  --notes "Completed foundation sections, 6,500 words"

# Day 2 - Resume work
python memory/checkpoint-resume.py \
  --name "mod-105-data-pipelines" \
  --latest

# Day 2 - After case studies
python memory/checkpoint-save.py \
  --name "mod-105-data-pipelines" \
  --stage "case-studies-complete" \
  --notes "Added 3 case studies, 9,200 words total"

# Day 2 - Final checkpoint before review
python memory/checkpoint-save.py \
  --name "mod-105-data-pipelines" \
  --stage "ready-for-review" \
  --notes "Module complete at 12,450 words"
```

### 2. Multi-Module Curriculum (65-110 hours)

**Scenario**: Building curriculum with 10 modules across multiple weeks

```bash
# Week 1 - Checkpoint after first 2 modules
python memory/checkpoint-save.py \
  --name "junior-curriculum-batch-1" \
  --stage "modules-1-2-complete" \
  --context ./modules \
  --notes "Modules 1-2 complete, validated"

# Week 2 - Resume and continue
python memory/checkpoint-resume.py \
  --name "junior-curriculum-batch-1" \
  --latest

# Week 2 - Checkpoint after modules 3-5
python memory/checkpoint-save.py \
  --name "junior-curriculum-batch-1" \
  --stage "modules-3-5-complete" \
  --context ./modules \
  --notes "Modules 3-5 complete, halfway through curriculum"
```

### 3. Project Generation (15-24 hours)

**Scenario**: Creating hands-on project with starter code, solutions, and tests

```bash
# After completing starter code
python memory/checkpoint-save.py \
  --name "project-llm-api" \
  --stage "starter-code" \
  --notes "Starter code complete, untested"

# After completing solution
python memory/checkpoint-save.py \
  --name "project-llm-api" \
  --stage "solution-complete" \
  --notes "Reference solution complete, tests passing"

# After documentation
python memory/checkpoint-save.py \
  --name "project-llm-api" \
  --stage "ready-for-review" \
  --notes "Documentation complete, deployment guide added"
```

### 4. Emergency Backup

**Scenario**: Quick backup before major refactoring

```bash
# Before making major changes
python memory/checkpoint-save.py \
  --name "module-08-backup" \
  --stage "pre-refactor" \
  --context ./modules/mod-008-monitoring \
  --notes "Backup before restructuring case studies"

# If refactor fails, restore
python memory/checkpoint-resume.py \
  --name "module-08-backup" \
  --latest
```

## Checkpoint Metadata

Each checkpoint includes:

```json
{
  "name": "module-05",
  "timestamp": "2025-01-04T14:30:22",
  "stage": "case-studies",
  "notes": "Completed 3 case studies",
  "metadata": {},
  "files": [
    {
      "path": "lecture-notes.md",
      "size": 45678,
      "modified": "2025-01-04T14:29:15",
      "hash": "sha256:abcd1234...",
      "word_count": 9200
    }
  ],
  "metrics": {
    "total_files": 5,
    "total_words": 11500,
    "total_size": 125678
  }
}
```

## Best Practices

### When to Checkpoint

✅ **Do checkpoint when**:
- Completing major sections (3,000+ words added)
- Finishing specific stage (case studies, code examples)
- Ending work session (even if not at milestone)
- Before major refactoring or changes
- Before validation runs
- After successful validation passes

❌ **Don't checkpoint when**:
- Making trivial changes (< 500 words)
- In middle of incomplete thought
- Files have syntax errors or incomplete code
- Before testing changes (wait for tests to pass)

### Naming Conventions

**Names**: Use descriptive, hierarchical names
- `module-05` - For single module work
- `curriculum-junior-batch-1` - For multi-module work
- `project-llm-api` - For project work
- `review-final` - For final review stage

**Stages**: Use milestone-based stage names
- `foundation-complete` - Core sections done
- `code-examples-complete` - All code added
- `case-studies-complete` - Case studies done
- `ready-for-review` - Complete, needs review
- `validated` - Passed all validation
- `final` - Reviewed and approved

### Notes Guidelines

Good notes include:
- **Completion status**: "Completed sections 1-4"
- **Word count**: "9,200 words total"
- **Blockers**: "Waiting for code review"
- **Next steps**: "Need to add troubleshooting section"
- **Quality state**: "All code examples tested"

Example:
```bash
python memory/checkpoint-save.py \
  --name "mod-105" \
  --stage "code-examples" \
  --notes "Added 12 code examples (all tested).
           10,500 words.
           Next: case studies with AWS, Azure, GCP"
```

## Integration with Workflows

### Module Generation Workflow

Add checkpoints at key milestones:

1. **After Research** (20% complete)
2. **After Foundation Sections** (40% complete)
3. **After Code Examples** (60% complete)
4. **After Case Studies** (80% complete)
5. **After Validation** (100% complete)

### Curriculum Design Workflow

Checkpoint after each batch:

1. **Research Complete** - Skills matrix, role briefs
2. **Module 1-3 Complete** - First batch
3. **Module 4-6 Complete** - Second batch
4. **Module 7-10 Complete** - Third batch
5. **Review Complete** - All modules validated

## Advanced Features

### Custom Metadata

Add structured metadata for better tracking:

```bash
python memory/checkpoint-save.py \
  --name "mod-105" \
  --stage "complete" \
  --metadata '{
    "word_count": 12450,
    "code_examples": 15,
    "case_studies": 3,
    "validation_status": "passed",
    "reviewer": "jane.smith"
  }'
```

### Verification

Always verify restored files:

```bash
# Restore with verification (default)
python memory/checkpoint-resume.py --name "mod-105" --latest

# Skip verification (faster, less safe)
python memory/checkpoint-resume.py --name "mod-105" --latest --no-verify

# Generate restore report
python memory/checkpoint-resume.py \
  --name "mod-105" \
  --latest \
  --report ./restore-report.md
```

### Selective Restore

Restore only specific files by using checkpoints strategically:

```bash
# Save only specific files
python memory/checkpoint-save.py \
  --name "code-backup" \
  --stage "examples" \
  --files ./src/**/*.py ./tests/**/*.py

# Restore to different location for comparison
python memory/checkpoint-resume.py \
  --name "code-backup" \
  --latest \
  --target ./comparison
```

## Troubleshooting

### Issue: Checkpoint Not Found

```bash
# List available checkpoints
python memory/checkpoint-resume.py --list --name "module-05"

# Check checkpoint directory
ls -la memory/checkpoints/
```

### Issue: Verification Failed

Verification failures indicate file corruption or modification:

```bash
# Resume without verification (use caution)
python memory/checkpoint-resume.py \
  --name "module-05" \
  --latest \
  --no-verify

# Generate report to see which files failed
python memory/checkpoint-resume.py \
  --name "module-05" \
  --latest \
  --report ./verification-report.md
```

### Issue: Too Many Checkpoints

Clean up old checkpoints:

```bash
# List all checkpoints with dates
python memory/checkpoint-resume.py --list

# Manually remove old checkpoint directories
rm -rf memory/checkpoints/module-05_20250101_*

# Keep only last 5 checkpoints per name (manual cleanup)
```

### Issue: Large Checkpoint Size

Checkpoints include all files in context directory:

```bash
# Exclude large files/directories by saving specific files
python memory/checkpoint-save.py \
  --name "module-05" \
  --stage "current" \
  --files lecture-notes.md exercises/*.md

# Or clean working directory before checkpoint
```

## Maintenance

### Storage Management

Checkpoints are stored in `memory/checkpoints/`. Each checkpoint includes:
- Metadata JSON (~1-5 KB)
- Summary markdown (~1-2 KB)
- Copied files (varies)

**Estimate**: ~50-500 KB per module checkpoint, depending on files saved.

### Cleanup Strategy

Suggested cleanup schedule:
- Keep all checkpoints from last 7 days
- Keep final checkpoints indefinitely
- Remove intermediate checkpoints after 30 days
- Archive important milestones to separate backup

### Backup

Back up checkpoint directory periodically:

```bash
# Backup checkpoints to external storage
tar -czf checkpoints-backup-$(date +%Y%m%d).tar.gz memory/checkpoints/

# Restore from backup
tar -xzf checkpoints-backup-20250104.tar.gz
```

## Related Documentation

- [Module Generation Workflow](../workflows/module-generation.md) - Integrate checkpoints into module creation
- [Curriculum Design Workflow](../workflows/curriculum-design.md) - Checkpoint multi-module projects
- [Best Practices](../docs/best-practices.md) - Content generation best practices

## Questions?

For issues or questions about the checkpoint system:
- See [SUPPORT.md](../SUPPORT.md) for help resources
- Open an issue on GitHub
- Check existing checkpoints: `python memory/checkpoint-resume.py --list`

---

**Version**: 1.0.0
**Added**: 2025-01-04
**Last Updated**: 2025-01-04
