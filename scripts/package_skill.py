#!/usr/bin/env python3
"""Package the CircuiteX (circtex) skill into a distributable .skill (zip) bundle.

Usage: python scripts/package_skill.py [--out PATH]
"""
import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def package_skill(output_path=None):
    if output_path is None:
        output_path = ROOT / "circtex.skill"
    else:
        output_path = Path(output_path)

    files_to_pack = [
        "SKILL.md",
        "README.md",
        "TUTORIAL.md",
        "LICENSE",
        "plugin.json",
        "spec/note-schema.json",
        "spec/theme.json",
        "assets/preamble.tex",
        "library/sources.json",
        "library/circuits.json",
        "library/components.json",
        "scripts/build.py",
        "scripts/setup_compiler.py",
        "scripts/package_skill.py",
    ]

    # Add all circuit snippets
    for p in sorted((ROOT / "assets" / "circuits").glob("*.tex")):
        rel = p.relative_to(ROOT).as_posix()
        files_to_pack.append(rel)

    # Add all examples
    for p in sorted((ROOT / "examples").glob("*.json")):
        rel = p.relative_to(ROOT).as_posix()
        files_to_pack.append(rel)

    print(f"Packaging {len(files_to_pack)} files into {output_path}...")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in files_to_pack:
            file_on_disk = ROOT / rel_path
            if not file_on_disk.exists():
                print(f"Warning: {file_on_disk} does not exist, skipping.")
                continue
            arcname = f"circtex/{rel_path}"
            zf.write(file_on_disk, arcname=arcname)
            print(f"  + {arcname}")

    print(f"Successfully packaged {output_path} ({output_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package circtex skill.")
    parser.add_argument("--out", default=None, help="Output file path (default: circtex.skill in root)")
    args = parser.parse_args()
    sys.exit(package_skill(args.out))
