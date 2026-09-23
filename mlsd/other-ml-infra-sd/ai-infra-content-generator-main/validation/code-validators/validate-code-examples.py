#!/usr/bin/env python3
"""
Code Examples Validator

Validates code examples in lecture notes to ensure they meet quality standards.

Usage:
    python validate-code-examples.py lecture-notes.md
    python validate-code-examples.py --directory modules/
    python validate-code-examples.py --strict lecture-notes.md

Requirements:
    pip install markdown pylint bandit
"""

import argparse
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class CodeValidator:
    """Validates code examples in markdown files."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_file(self, filepath: Path) -> Dict:
        """Validate all code examples in a file."""
        print(f"\n{'='*60}")
        print(f"Validating: {filepath}")
        print(f"{'='*60}\n")

        content = filepath.read_text(encoding='utf-8')
        code_blocks = self._extract_code_blocks(content)

        print(f"Found {len(code_blocks)} code blocks")

        results = {
            'file': str(filepath),
            'total_blocks': len(code_blocks),
            'validated': 0,
            'errors': [],
            'warnings': [],
            'info': []
        }

        for idx, block in enumerate(code_blocks, 1):
            print(f"\n--- Block {idx}/{len(code_blocks)} ---")
            block_results = self._validate_code_block(block, idx)
            results['errors'].extend(block_results['errors'])
            results['warnings'].extend(block_results['warnings'])
            results['info'].extend(block_results['info'])

            if not block_results['errors']:
                results['validated'] += 1

        self._print_summary(results)
        return results

    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """Extract all code blocks from markdown content."""
        # Pattern matches: ```language\ncode\n```
        pattern = r'```(\w+)\n(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)

        blocks = []
        for match in matches:
            language = match.group(1)
            code = match.group(2)
            start_pos = match.start()

            # Count line number
            line_num = content[:start_pos].count('\n') + 1

            blocks.append({
                'language': language,
                'code': code,
                'line': line_num
            })

        return blocks

    def _validate_code_block(self, block: Dict, block_num: int) -> Dict:
        """Validate a single code block."""
        results = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        language = block['language']
        code = block['code']
        line = block['line']

        print(f"Language: {language}")
        print(f"Line: {line}")
        print(f"Length: {len(code)} characters")

        # Check for common issues
        if not code.strip():
            results['errors'].append({
                'block': block_num,
                'line': line,
                'type': 'empty_code',
                'message': 'Code block is empty'
            })
            return results

        # Language-specific validation
        if language.lower() in ['python', 'py']:
            self._validate_python(code, block_num, line, results)
        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            self._validate_javascript(code, block_num, line, results)
        elif language.lower() in ['bash', 'sh', 'shell']:
            self._validate_bash(code, block_num, line, results)
        else:
            results['info'].append({
                'block': block_num,
                'line': line,
                'message': f'Skipping validation for language: {language}'
            })

        return results

    def _validate_python(self, code: str, block_num: int, line: int, results: Dict):
        """Validate Python code."""
        print("Validating Python code...")

        # Check 1: Syntax validation
        try:
            ast.parse(code)
            results['info'].append({
                'block': block_num,
                'line': line,
                'message': '✓ Python syntax is valid'
            })
        except SyntaxError as e:
            results['errors'].append({
                'block': block_num,
                'line': line,
                'type': 'syntax_error',
                'message': f'Python syntax error: {e}'
            })
            return  # Can't continue if syntax is invalid

        # Check 2: Look for common issues
        issues = []

        # No hardcoded credentials
        if re.search(r'(password|api_key|secret)\s*=\s*["\'][^"\']+["\']', code, re.I):
            issues.append('Contains hardcoded credentials')

        # No print statements in production code (warning only)
        if 'print(' in code and '# Example' not in code:
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Contains print() statements - consider using logging'
            })

        # Has error handling
        if 'def ' in code and 'try:' not in code:
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Function without error handling'
            })

        # Has type hints (for functions)
        if 'def ' in code and '->' not in code:
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Function missing return type hint'
            })

        # Has docstrings
        if 'def ' in code or 'class ' in code:
            if '"""' not in code and "'''" not in code:
                results['warnings'].append({
                    'block': block_num,
                    'line': line,
                    'message': 'Function/class missing docstring'
                })

        if issues:
            for issue in issues:
                results['errors'].append({
                    'block': block_num,
                    'line': line,
                    'type': 'code_quality',
                    'message': issue
                })

    def _validate_javascript(self, code: str, block_num: int, line: int, results: Dict):
        """Validate JavaScript/TypeScript code."""
        print("Validating JavaScript code...")

        # Check for common issues
        # No var (should use let/const)
        if re.search(r'\bvar\b', code):
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Uses "var" instead of "let" or "const"'
            })

        # No hardcoded credentials
        if re.search(r'(password|apiKey|secret)\s*[:=]\s*["\'][^"\']+["\']', code, re.I):
            results['errors'].append({
                'block': block_num,
                'line': line,
                'type': 'security',
                'message': 'Contains hardcoded credentials'
            })

        # Has error handling
        if 'function' in code and 'try' not in code and 'catch' not in code:
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Function without error handling'
            })

        results['info'].append({
            'block': block_num,
            'line': line,
            'message': '✓ Basic JavaScript validation passed'
        })

    def _validate_bash(self, code: str, block_num: int, line: int, results: Dict):
        """Validate Bash script."""
        print("Validating Bash code...")

        # Check for common issues
        # Should have shebang if multi-line
        if '\n' in code and not code.startswith('#!'):
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Multi-line script missing shebang (#!/bin/bash)'
            })

        # Should use set -e for error handling
        if '\n' in code and 'set -e' not in code:
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': 'Script missing "set -e" for error handling'
            })

        # No unquoted variables
        unquoted = re.findall(r'\$\w+(?!["\'\}])', code)
        if unquoted:
            results['warnings'].append({
                'block': block_num,
                'line': line,
                'message': f'Unquoted variables: {", ".join(set(unquoted))}'
            })

        results['info'].append({
            'block': block_num,
            'line': line,
            'message': '✓ Basic Bash validation passed'
        })

    def _print_summary(self, results: Dict):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")

        print(f"\nFile: {results['file']}")
        print(f"Total blocks: {results['total_blocks']}")
        print(f"Validated successfully: {results['validated']}")
        print(f"Blocks with errors: {len(results['errors'])}")
        print(f"Blocks with warnings: {len(results['warnings'])}")

        if results['errors']:
            print(f"\n{'='*60}")
            print(f"ERRORS ({len(results['errors'])})")
            print(f"{'='*60}")
            for error in results['errors']:
                print(f"\n❌ Block {error['block']} (line {error['line']})")
                print(f"   Type: {error.get('type', 'unknown')}")
                print(f"   {error['message']}")

        if results['warnings']:
            print(f"\n{'='*60}")
            print(f"WARNINGS ({len(results['warnings'])})")
            print(f"{'='*60}")
            for warning in results['warnings']:
                print(f"\n⚠️  Block {warning['block']} (line {warning['line']})")
                print(f"   {warning['message']}")

        # Print pass/fail
        if results['errors']:
            print(f"\n{'='*60}")
            print("❌ VALIDATION FAILED")
            print(f"{'='*60}\n")
            return False
        elif results['warnings'] and self.strict:
            print(f"\n{'='*60}")
            print("❌ VALIDATION FAILED (strict mode - warnings treated as errors)")
            print(f"{'='*60}\n")
            return False
        else:
            print(f"\n{'='*60}")
            print("✅ VALIDATION PASSED")
            print(f"{'='*60}\n")
            return True


def main():
    parser = argparse.ArgumentParser(
        description='Validate code examples in lecture notes'
    )
    parser.add_argument(
        'path',
        type=str,
        help='Path to markdown file or directory'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    parser.add_argument(
        '--directory',
        '-d',
        action='store_true',
        help='Validate all .md files in directory'
    )

    args = parser.parse_args()

    validator = CodeValidator(strict=args.strict)

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    files_to_validate = []

    if args.directory or path.is_dir():
        files_to_validate = list(path.rglob('*.md'))
        print(f"Found {len(files_to_validate)} markdown files to validate\n")
    else:
        files_to_validate = [path]

    all_passed = True
    results_summary = []

    for file in files_to_validate:
        results = validator.validate_file(file)
        results_summary.append(results)

        if results['errors'] or (args.strict and results['warnings']):
            all_passed = False

    # Print overall summary if multiple files
    if len(files_to_validate) > 1:
        print(f"\n{'='*60}")
        print("OVERALL SUMMARY")
        print(f"{'='*60}")
        print(f"Files validated: {len(files_to_validate)}")

        total_blocks = sum(r['total_blocks'] for r in results_summary)
        total_validated = sum(r['validated'] for r in results_summary)
        total_errors = sum(len(r['errors']) for r in results_summary)
        total_warnings = sum(len(r['warnings']) for r in results_summary)

        print(f"Total code blocks: {total_blocks}")
        print(f"Successfully validated: {total_validated}")
        print(f"Total errors: {total_errors}")
        print(f"Total warnings: {total_warnings}")

        if all_passed:
            print("\n✅ ALL FILES PASSED")
        else:
            print("\n❌ SOME FILES FAILED")

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
