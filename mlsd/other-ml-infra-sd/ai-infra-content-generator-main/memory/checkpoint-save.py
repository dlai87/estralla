#!/usr/bin/env python3
"""
Checkpoint Save Tool

Saves the current state of content generation work to enable resuming later.
Useful for long-running content generation tasks that span multiple sessions.

Usage:
    python checkpoint-save.py --name "module-05-progress" --stage "case-studies"
    python checkpoint-save.py --name "curriculum-design" --stage "module-03" --notes "Completed lecture notes"
    python checkpoint-save.py --auto --context ./working-dir

Features:
- Saves work-in-progress files with metadata
- Records current stage and completion status
- Tracks word counts and progress metrics
- Supports custom notes and context
- Creates timestamped checkpoints
- Validates checkpoint integrity
"""

import argparse
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class CheckpointManager:
    """Manages saving content generation checkpoints."""

    def __init__(self, checkpoint_dir: Path = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints (default: ./memory/checkpoints)
        """
        if checkpoint_dir is None:
            checkpoint_dir = Path(__file__).parent / "checkpoints"

        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def count_words(self, file_path: Path) -> int:
        """Count words in a markdown file."""
        if not file_path.exists() or file_path.suffix not in ['.md', '.txt']:
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove code blocks
                content = '\n'.join(line for line in content.split('\n')
                                   if not line.strip().startswith('```'))
                words = len(content.split())
                return words
        except Exception:
            return 0

    def scan_directory(self, context_dir: Path, patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Scan directory for content files and gather metadata.

        Args:
            context_dir: Directory to scan
            patterns: File patterns to include (default: ['*.md', '*.py', '*.yaml', '*.json'])

        Returns:
            List of file metadata dictionaries
        """
        if patterns is None:
            patterns = ['*.md', '*.py', '*.yaml', '*.json']

        files_data = []
        context_path = Path(context_dir)

        if not context_path.exists():
            return files_data

        for pattern in patterns:
            for file_path in context_path.rglob(pattern):
                if '.git' in file_path.parts or '__pycache__' in file_path.parts:
                    continue

                rel_path = file_path.relative_to(context_path)
                file_info = {
                    'path': str(rel_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat(),
                    'hash': self.calculate_file_hash(file_path),
                }

                if file_path.suffix == '.md':
                    file_info['word_count'] = self.count_words(file_path)

                files_data.append(file_info)

        return files_data

    def save_checkpoint(
        self,
        name: str,
        stage: str,
        context_dir: Path = None,
        notes: str = "",
        metadata: Dict[str, Any] = None,
        files_to_save: List[Path] = None
    ) -> Path:
        """Save a checkpoint.

        Args:
            name: Checkpoint name (e.g., 'module-05-progress')
            stage: Current stage (e.g., 'case-studies', 'code-examples')
            context_dir: Directory containing work in progress
            notes: Optional notes about current state
            metadata: Additional metadata to save
            files_to_save: Specific files to checkpoint (if None, scans context_dir)

        Returns:
            Path to created checkpoint directory
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"{name}_{timestamp}"
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # Create checkpoint metadata
        checkpoint_data = {
            'name': name,
            'timestamp': datetime.datetime.now().isoformat(),
            'stage': stage,
            'notes': notes,
            'metadata': metadata or {},
            'files': []
        }

        # Save files
        if files_to_save:
            # Save specific files
            for file_path in files_to_save:
                if not Path(file_path).exists():
                    print(f"Warning: File not found: {file_path}", file=sys.stderr)
                    continue

                file_info = self._save_file(Path(file_path), checkpoint_path)
                checkpoint_data['files'].append(file_info)

        elif context_dir:
            # Scan and save directory
            context_path = Path(context_dir)
            if context_path.exists():
                files_metadata = self.scan_directory(context_path)

                for file_meta in files_metadata:
                    source_file = context_path / file_meta['path']
                    dest_file = checkpoint_path / 'files' / file_meta['path']
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, dest_file)
                    checkpoint_data['files'].append(file_meta)

        # Calculate total metrics
        total_words = sum(f.get('word_count', 0) for f in checkpoint_data['files'])
        total_files = len(checkpoint_data['files'])

        checkpoint_data['metrics'] = {
            'total_files': total_files,
            'total_words': total_words,
            'total_size': sum(f['size'] for f in checkpoint_data['files'])
        }

        # Save checkpoint metadata
        metadata_file = checkpoint_path / 'checkpoint.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)

        # Create human-readable summary
        summary_file = checkpoint_path / 'CHECKPOINT_SUMMARY.md'
        self._create_summary(checkpoint_data, summary_file)

        return checkpoint_path

    def _save_file(self, source: Path, checkpoint_path: Path) -> Dict[str, Any]:
        """Save a single file to checkpoint."""
        rel_path = source.name
        dest_file = checkpoint_path / 'files' / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest_file)

        file_info = {
            'path': rel_path,
            'size': source.stat().st_size,
            'modified': datetime.datetime.fromtimestamp(
                source.stat().st_mtime
            ).isoformat(),
            'hash': self.calculate_file_hash(source),
        }

        if source.suffix == '.md':
            file_info['word_count'] = self.count_words(source)

        return file_info

    def _create_summary(self, checkpoint_data: Dict[str, Any], summary_file: Path):
        """Create human-readable checkpoint summary."""
        summary = f"""# Checkpoint Summary

**Name**: {checkpoint_data['name']}
**Timestamp**: {checkpoint_data['timestamp']}
**Stage**: {checkpoint_data['stage']}

## Notes

{checkpoint_data['notes'] or 'No notes provided'}

## Metrics

- **Total Files**: {checkpoint_data['metrics']['total_files']}
- **Total Words**: {checkpoint_data['metrics']['total_words']:,}
- **Total Size**: {checkpoint_data['metrics']['total_size']:,} bytes

## Files Saved

"""

        for file_info in checkpoint_data['files']:
            summary += f"- `{file_info['path']}`"
            if 'word_count' in file_info:
                summary += f" ({file_info['word_count']:,} words)"
            summary += "\n"

        if checkpoint_data['metadata']:
            summary += "\n## Additional Metadata\n\n"
            for key, value in checkpoint_data['metadata'].items():
                summary += f"- **{key}**: {value}\n"

        summary += f"\n---\n\nTo resume from this checkpoint:\n```bash\npython checkpoint-resume.py --name {checkpoint_data['name']} --latest\n```\n"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints."""
        checkpoints = []

        for checkpoint_dir in sorted(self.checkpoint_dir.iterdir(), reverse=True):
            if not checkpoint_dir.is_dir():
                continue

            metadata_file = checkpoint_dir / 'checkpoint.json'
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['checkpoint_dir'] = str(checkpoint_dir)
                    checkpoints.append(data)
            except Exception as e:
                print(f"Warning: Could not load checkpoint {checkpoint_dir}: {e}",
                      file=sys.stderr)

        return checkpoints


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Save checkpoint for content generation work',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save checkpoint with specific name and stage
  python checkpoint-save.py --name module-05 --stage case-studies

  # Save with context directory
  python checkpoint-save.py --name curriculum-design --stage module-03 --context ./working

  # Save with notes
  python checkpoint-save.py --name project-gen --stage testing --notes "Completed code examples"

  # List existing checkpoints
  python checkpoint-save.py --list

  # Save specific files
  python checkpoint-save.py --name review --stage final --files lecture-notes.md exercises.md
        """
    )

    parser.add_argument('--name', type=str, help='Checkpoint name')
    parser.add_argument('--stage', type=str, help='Current stage/phase')
    parser.add_argument('--context', type=Path, default=Path.cwd(),
                       help='Context directory to save (default: current directory)')
    parser.add_argument('--notes', type=str, default='',
                       help='Notes about current state')
    parser.add_argument('--files', nargs='+', type=Path,
                       help='Specific files to checkpoint')
    parser.add_argument('--checkpoint-dir', type=Path,
                       help='Checkpoint storage directory')
    parser.add_argument('--list', action='store_true',
                       help='List all checkpoints')
    parser.add_argument('--metadata', type=json.loads,
                       help='Additional metadata as JSON string')

    args = parser.parse_args()

    manager = CheckpointManager(checkpoint_dir=args.checkpoint_dir)

    if args.list:
        checkpoints = manager.list_checkpoints()
        if not checkpoints:
            print("No checkpoints found.")
            return 0

        print(f"\nFound {len(checkpoints)} checkpoint(s):\n")
        for cp in checkpoints:
            print(f"  {cp['name']}")
            print(f"    Timestamp: {cp['timestamp']}")
            print(f"    Stage: {cp['stage']}")
            print(f"    Files: {cp['metrics']['total_files']}")
            print(f"    Words: {cp['metrics']['total_words']:,}")
            print(f"    Location: {cp['checkpoint_dir']}")
            print()
        return 0

    if not args.name or not args.stage:
        parser.error("--name and --stage are required (unless using --list)")

    print(f"Creating checkpoint '{args.name}' at stage '{args.stage}'...")

    checkpoint_path = manager.save_checkpoint(
        name=args.name,
        stage=args.stage,
        context_dir=args.context if not args.files else None,
        notes=args.notes,
        metadata=args.metadata,
        files_to_save=args.files
    )

    print(f"\n✓ Checkpoint saved successfully!")
    print(f"  Location: {checkpoint_path}")
    print(f"\nTo resume:")
    print(f"  python checkpoint-resume.py --name {args.name} --latest")

    # Show summary
    summary_file = checkpoint_path / 'CHECKPOINT_SUMMARY.md'
    if summary_file.exists():
        print(f"\nSummary saved to: {summary_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
