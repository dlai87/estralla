#!/usr/bin/env python3
"""
Checkpoint Resume Tool

Restores content generation work from a saved checkpoint to enable continuing
from where you left off.

Usage:
    python checkpoint-resume.py --name "module-05-progress" --latest
    python checkpoint-resume.py --name "curriculum-design" --timestamp 20250104_143022
    python checkpoint-resume.py --list --name "module-05-progress"
    python checkpoint-resume.py --checkpoint ./memory/checkpoints/module-05_20250104_143022

Features:
- Restores files from checkpoint to working directory
- Validates file integrity using checksums
- Shows progress and completion status
- Supports resuming from specific timestamp
- Creates restore report with differences
"""

import argparse
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class CheckpointRestorer:
    """Manages resuming from content generation checkpoints."""

    def __init__(self, checkpoint_dir: Path = None):
        """Initialize checkpoint restorer.

        Args:
            checkpoint_dir: Directory containing checkpoints (default: ./memory/checkpoints)
        """
        if checkpoint_dir is None:
            checkpoint_dir = Path(__file__).parent / "checkpoints"

        self.checkpoint_dir = Path(checkpoint_dir)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        if not file_path.exists():
            return ""

        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def find_checkpoints(self, name: str) -> List[Path]:
        """Find all checkpoints matching the given name.

        Args:
            name: Checkpoint name to search for

        Returns:
            List of checkpoint directories, sorted by timestamp (newest first)
        """
        if not self.checkpoint_dir.exists():
            return []

        matching = []
        for checkpoint_path in self.checkpoint_dir.iterdir():
            if not checkpoint_path.is_dir():
                continue

            if checkpoint_path.name.startswith(f"{name}_"):
                metadata_file = checkpoint_path / 'checkpoint.json'
                if metadata_file.exists():
                    matching.append(checkpoint_path)

        return sorted(matching, reverse=True)

    def load_checkpoint_metadata(self, checkpoint_path: Path) -> Optional[Dict[str, Any]]:
        """Load checkpoint metadata.

        Args:
            checkpoint_path: Path to checkpoint directory

        Returns:
            Checkpoint metadata dictionary or None if invalid
        """
        metadata_file = checkpoint_path / 'checkpoint.json'

        if not metadata_file.exists():
            print(f"Error: No checkpoint.json found in {checkpoint_path}", file=sys.stderr)
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error: Could not load checkpoint metadata: {e}", file=sys.stderr)
            return None

    def restore_checkpoint(
        self,
        checkpoint_path: Path,
        target_dir: Path,
        verify: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Restore files from checkpoint to target directory.

        Args:
            checkpoint_path: Path to checkpoint directory
            target_dir: Target directory to restore files to
            verify: Verify file integrity using checksums
            dry_run: Show what would be restored without actually doing it

        Returns:
            Restore report dictionary
        """
        metadata = self.load_checkpoint_metadata(checkpoint_path)
        if not metadata:
            return {'success': False, 'error': 'Invalid checkpoint'}

        files_dir = checkpoint_path / 'files'
        if not files_dir.exists():
            return {'success': False, 'error': 'No files directory in checkpoint'}

        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        report = {
            'success': True,
            'checkpoint_name': metadata['name'],
            'checkpoint_timestamp': metadata['timestamp'],
            'checkpoint_stage': metadata['stage'],
            'files_restored': [],
            'files_skipped': [],
            'files_verified': [],
            'verification_failed': [],
            'dry_run': dry_run
        }

        print(f"\nRestoring checkpoint: {metadata['name']}")
        print(f"  Stage: {metadata['stage']}")
        print(f"  Created: {metadata['timestamp']}")
        print(f"  Files: {len(metadata['files'])}")
        print()

        if metadata.get('notes'):
            print(f"Notes: {metadata['notes']}\n")

        for file_info in metadata['files']:
            source_file = files_dir / file_info['path']
            target_file = target_dir / file_info['path']

            # Check if file exists in checkpoint
            if not source_file.exists():
                print(f"  ⚠ Warning: File missing from checkpoint: {file_info['path']}")
                report['files_skipped'].append({
                    'path': file_info['path'],
                    'reason': 'missing_from_checkpoint'
                })
                continue

            # Check if target file already exists
            if target_file.exists():
                current_hash = self.calculate_file_hash(target_file)
                checkpoint_hash = file_info.get('hash', '')

                if current_hash == checkpoint_hash:
                    print(f"  ⊙ Skipped (identical): {file_info['path']}")
                    report['files_skipped'].append({
                        'path': file_info['path'],
                        'reason': 'identical'
                    })
                    continue
                else:
                    print(f"  ↻ Overwriting: {file_info['path']}")

            # Restore file
            if not dry_run:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)

                # Verify if requested
                if verify:
                    restored_hash = self.calculate_file_hash(target_file)
                    expected_hash = file_info.get('hash', '')

                    if restored_hash == expected_hash:
                        report['files_verified'].append(file_info['path'])
                    else:
                        print(f"  ✗ Verification failed: {file_info['path']}")
                        report['verification_failed'].append(file_info['path'])
                        report['success'] = False
                        continue

            status = "Would restore" if dry_run else "Restored"
            print(f"  ✓ {status}: {file_info['path']}")
            report['files_restored'].append(file_info['path'])

        return report

    def list_checkpoints(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available checkpoints.

        Args:
            name: Optional name filter

        Returns:
            List of checkpoint metadata dictionaries
        """
        if not self.checkpoint_dir.exists():
            return []

        checkpoints = []

        for checkpoint_path in sorted(self.checkpoint_dir.iterdir(), reverse=True):
            if not checkpoint_path.is_dir():
                continue

            metadata = self.load_checkpoint_metadata(checkpoint_path)
            if not metadata:
                continue

            if name and not checkpoint_path.name.startswith(f"{name}_"):
                continue

            metadata['checkpoint_dir'] = str(checkpoint_path)
            metadata['checkpoint_name_full'] = checkpoint_path.name
            checkpoints.append(metadata)

        return checkpoints

    def create_restore_report(self, report: Dict[str, Any], output_file: Path):
        """Create human-readable restore report."""
        content = f"""# Checkpoint Restore Report

**Checkpoint**: {report['checkpoint_name']}
**Stage**: {report['checkpoint_stage']}
**Restored**: {datetime.datetime.now().isoformat()}
**Dry Run**: {report['dry_run']}

## Summary

- **Files Restored**: {len(report['files_restored'])}
- **Files Skipped**: {len(report['files_skipped'])}
- **Files Verified**: {len(report['files_verified'])}
- **Verification Failed**: {len(report['verification_failed'])}
- **Success**: {report['success']}

"""

        if report['files_restored']:
            content += "## Restored Files\n\n"
            for path in report['files_restored']:
                content += f"- `{path}`\n"
            content += "\n"

        if report['files_skipped']:
            content += "## Skipped Files\n\n"
            for item in report['files_skipped']:
                content += f"- `{item['path']}` (Reason: {item['reason']})\n"
            content += "\n"

        if report['verification_failed']:
            content += "## ⚠ Verification Failed\n\n"
            for path in report['verification_failed']:
                content += f"- `{path}`\n"
            content += "\n"

        content += "---\n\nRestore completed.\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Resume from a saved checkpoint',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resume from latest checkpoint with given name
  python checkpoint-resume.py --name module-05 --latest

  # Resume from specific checkpoint by timestamp
  python checkpoint-resume.py --name module-05 --timestamp 20250104_143022

  # Resume from full checkpoint path
  python checkpoint-resume.py --checkpoint ./memory/checkpoints/module-05_20250104_143022

  # List available checkpoints
  python checkpoint-resume.py --list

  # List checkpoints for specific name
  python checkpoint-resume.py --list --name module-05

  # Dry run (show what would be restored)
  python checkpoint-resume.py --name module-05 --latest --dry-run

  # Restore to different directory
  python checkpoint-resume.py --name module-05 --latest --target ./restored
        """
    )

    parser.add_argument('--name', type=str, help='Checkpoint name')
    parser.add_argument('--timestamp', type=str, help='Specific checkpoint timestamp')
    parser.add_argument('--latest', action='store_true',
                       help='Use latest checkpoint with given name')
    parser.add_argument('--checkpoint', type=Path,
                       help='Full path to checkpoint directory')
    parser.add_argument('--target', type=Path, default=Path.cwd(),
                       help='Target directory to restore to (default: current directory)')
    parser.add_argument('--checkpoint-dir', type=Path,
                       help='Checkpoint storage directory')
    parser.add_argument('--list', action='store_true',
                       help='List available checkpoints')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be restored without actually doing it')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip checksum verification')
    parser.add_argument('--report', type=Path,
                       help='Save restore report to file')

    args = parser.parse_args()

    restorer = CheckpointRestorer(checkpoint_dir=args.checkpoint_dir)

    # List checkpoints
    if args.list:
        checkpoints = restorer.list_checkpoints(name=args.name)

        if not checkpoints:
            if args.name:
                print(f"No checkpoints found for name: {args.name}")
            else:
                print("No checkpoints found.")
            return 0

        print(f"\nFound {len(checkpoints)} checkpoint(s):\n")
        for cp in checkpoints:
            print(f"  {cp['checkpoint_name_full']}")
            print(f"    Name: {cp['name']}")
            print(f"    Timestamp: {cp['timestamp']}")
            print(f"    Stage: {cp['stage']}")
            print(f"    Files: {cp['metrics']['total_files']}")
            print(f"    Words: {cp['metrics']['total_words']:,}")
            if cp.get('notes'):
                print(f"    Notes: {cp['notes']}")
            print()

        return 0

    # Determine checkpoint to restore
    checkpoint_path = None

    if args.checkpoint:
        # Use explicitly provided checkpoint path
        checkpoint_path = args.checkpoint
        if not checkpoint_path.exists():
            print(f"Error: Checkpoint not found: {checkpoint_path}", file=sys.stderr)
            return 1

    elif args.name:
        # Find checkpoint by name
        matching = restorer.find_checkpoints(args.name)

        if not matching:
            print(f"Error: No checkpoints found for name: {args.name}", file=sys.stderr)
            return 1

        if args.latest:
            checkpoint_path = matching[0]
        elif args.timestamp:
            # Find specific timestamp
            target_name = f"{args.name}_{args.timestamp}"
            for cp in matching:
                if cp.name == target_name:
                    checkpoint_path = cp
                    break

            if not checkpoint_path:
                print(f"Error: No checkpoint found with timestamp: {args.timestamp}",
                      file=sys.stderr)
                print(f"\nAvailable timestamps for '{args.name}':")
                for cp in matching:
                    ts = cp.name.split('_', 1)[1] if '_' in cp.name else 'unknown'
                    print(f"  - {ts}")
                return 1
        else:
            print(f"Error: Multiple checkpoints found for '{args.name}'", file=sys.stderr)
            print("Please specify --latest or --timestamp")
            print("\nAvailable checkpoints:")
            for cp in matching:
                ts = cp.name.split('_', 1)[1] if '_' in cp.name else 'unknown'
                print(f"  - {ts}")
            return 1
    else:
        parser.error("Specify --name, --checkpoint, or --list")

    # Restore checkpoint
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Restoring from: {checkpoint_path}")

    report = restorer.restore_checkpoint(
        checkpoint_path=checkpoint_path,
        target_dir=args.target,
        verify=not args.no_verify,
        dry_run=args.dry_run
    )

    if not report['success']:
        print(f"\n✗ Restore failed: {report.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    # Print summary
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}✓ Restore completed successfully!")
    print(f"  Files restored: {len(report['files_restored'])}")
    print(f"  Files skipped: {len(report['files_skipped'])}")

    if not args.no_verify and report['files_verified']:
        print(f"  Files verified: {len(report['files_verified'])}")

    if report['verification_failed']:
        print(f"  ⚠ Verification failed: {len(report['verification_failed'])}")

    # Save report if requested
    if args.report:
        restorer.create_restore_report(report, args.report)
        print(f"\nRestore report saved to: {args.report}")

    if not args.dry_run:
        print(f"\nFiles restored to: {args.target}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
