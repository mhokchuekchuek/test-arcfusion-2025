#!/usr/bin/env python3
"""
Update requirements.txt with currently installed package versions.

This script reads your existing requirements.txt and updates only the packages
listed there with their currently installed versions. It preserves:
- Comments
- Section organization
- Package extras (e.g., uvicorn[standard])
- Blank lines
"""

import subprocess
import re
import sys
from pathlib import Path


def get_installed_version(package_name: str) -> str | None:
    """
    Get the version of an installed package using pip show.

    Args:
        package_name: Name of the package (without extras)

    Returns:
        Version string or None if not found
    """
    try:
        result = subprocess.run(
            ['pip', 'show', package_name],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()

        return None
    except Exception as e:
        print(f"Warning: Could not get version for {package_name}: {e}")
        return None


def parse_package_line(line: str) -> tuple[str, str | None, str | None]:
    """
    Parse a package line to extract name, extras, and version.

    Args:
        line: Package line from requirements.txt

    Returns:
        Tuple of (package_name, extras, current_version)

    Examples:
        'fastapi' -> ('fastapi', None, None)
        'uvicorn[standard]' -> ('uvicorn', '[standard]', None)
        'pydantic==2.5.0' -> ('pydantic', None, '2.5.0')
        'fastapi>=0.95.0' -> ('fastapi', None, '0.95.0')
    """
    line = line.strip()

    # Match package with optional extras and version
    # Pattern: package_name[extras]>=version or package_name==version
    pattern = r'^([a-zA-Z0-9\-_]+)(\[[^\]]+\])?\s*([><=!]+.*)?$'
    match = re.match(pattern, line)

    if match:
        package_name = match.group(1)
        extras = match.group(2)  # e.g., [standard]
        version_spec = match.group(3)  # e.g., ==1.0.0 or >=1.0.0

        # Extract just the version number if present
        current_version = None
        if version_spec:
            version_match = re.search(r'[\d.]+', version_spec)
            if version_match:
                current_version = version_match.group(0)

        return package_name, extras, current_version

    return None, None, None


def update_requirements(
    input_file: str = 'requirements.txt',
    output_file: str = 'requirements.txt',
    backup: bool = True
) -> None:
    """
    Update requirements.txt with currently installed versions.

    Args:
        input_file: Path to input requirements.txt
        output_file: Path to output file (can be same as input)
        backup: Whether to create a backup of original file
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)

    # Create backup if requested
    if backup and input_file == output_file:
        backup_path = input_path.with_suffix('.txt.backup')
        backup_path.write_text(input_path.read_text())
        print(f"✓ Created backup: {backup_path}")

    updated_lines = []
    packages_updated = 0
    packages_not_found = []

    print(f"\nUpdating {input_file}...")
    print("-" * 60)

    with open(input_path, 'r') as f:
        for line in f:
            original_line = line.rstrip()
            stripped_line = line.strip()

            # Preserve empty lines and comments
            if not stripped_line or stripped_line.startswith('#'):
                updated_lines.append(original_line)
                continue

            # Parse package line
            package_name, extras, old_version = parse_package_line(stripped_line)

            if not package_name:
                # Couldn't parse, keep original
                updated_lines.append(original_line)
                continue

            # Get installed version
            installed_version = get_installed_version(package_name)

            if installed_version:
                # Build updated line
                extras_str = extras or ''
                new_line = f"{package_name}{extras_str}=={installed_version}"
                updated_lines.append(new_line)

                # Show what changed
                if old_version and old_version != installed_version:
                    print(f"  {package_name}: {old_version} → {installed_version}")
                elif not old_version:
                    print(f"  {package_name}: (no version) → {installed_version}")
                else:
                    print(f"  {package_name}: {installed_version} (unchanged)")

                packages_updated += 1
            else:
                # Package not found, keep original line
                updated_lines.append(original_line)
                packages_not_found.append(package_name)
                print(f"  {package_name}: NOT FOUND (kept original)")

    # Write updated requirements
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        f.write('\n'.join(updated_lines))
        if updated_lines and not updated_lines[-1].strip():
            # Don't add extra newline if last line is already blank
            pass
        else:
            f.write('\n')

    # Summary
    print("-" * 60)
    print(f"\n✓ Updated {packages_updated} packages")

    if packages_not_found:
        print(f"\n⚠ Warning: {len(packages_not_found)} packages not found:")
        for pkg in packages_not_found:
            print(f"  - {pkg}")
        print("\nThese packages might not be installed in your current environment.")

    print(f"\n✓ Saved to: {output_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Update requirements.txt with currently installed versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update requirements.txt (creates backup)
  python scripts/update_requirements.py

  # Update without backup
  python scripts/update_requirements.py --no-backup

  # Update different file
  python scripts/update_requirements.py -i dev-requirements.txt -o dev-requirements.txt
        """
    )

    parser.add_argument(
        '-i', '--input',
        default='requirements.txt',
        help='Input requirements file (default: requirements.txt)'
    )

    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output file (default: same as input)'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup file'
    )

    args = parser.parse_args()

    output_file = args.output or args.input

    update_requirements(
        input_file=args.input,
        output_file=output_file,
        backup=not args.no_backup
    )


if __name__ == '__main__':
    main()
