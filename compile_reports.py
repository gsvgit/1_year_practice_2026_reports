#!/usr/bin/env python3
"""Compile all LaTeX reports in subdirectories using lualatex (with latexmk)."""

import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

class CompilationResult(NamedTuple):
    tex_file: Path
    success: bool
    error: str | None = None

def find_tex_files(root: Path) -> list[Path]:
    """Find all .tex files in subdirectories of root."""
    tex_files = []
    for entry in root.iterdir():
        if entry.is_dir() and not entry.name.startswith('.'):
            tex_files_in_dir = list(entry.glob("*.tex"))
            if len(tex_files_in_dir) == 1:
                tex_files.append(tex_files_in_dir[0])
            elif len(tex_files_in_dir) > 1:
                print(f"WARNING: Multiple .tex files found in {entry}, skipping directory")
            else:
                print(f"WARNING: No .tex file found in {entry}, skipping directory")
    return sorted(tex_files)

def compile_tex(tex_file: Path, timeout: int = 300) -> CompilationResult:
    """Compile a .tex file using lualatex (with latexmk)."""
    try:
        result = subprocess.run(
            ["latexmk", "-lualatex", "-interaction=nonstopmode", "-file-line-error", "-shell-escape", tex_file.name],
            cwd=tex_file.parent,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return CompilationResult(tex_file=tex_file, success=True)
        else:
            error_lines = result.stdout.splitlines()[-50:] if result.stdout else []
            error_msg = "\n".join(error_lines)
            return CompilationResult(tex_file=tex_file, success=False, error=error_msg)

    except FileNotFoundError:
        return CompilationResult(
            tex_file=tex_file,
            success=False,
            error="latexmk command not found. Please install latexmk."
        )
    except subprocess.TimeoutExpired:
        return CompilationResult(
            tex_file=tex_file,
            success=False,
            error=f"Compilation timed out after {timeout} seconds"
        )
    except Exception as e:
        return CompilationResult(tex_file=tex_file, success=False, error=str(e))

def main():
    root = Path(__file__).parent
    tex_files = find_tex_files(root)

    if not tex_files:
        print("No .tex files found in subdirectories.")
        sys.exit(0)

    print(f"Found {len(tex_files)} report(s) to compile\n")

    results = []
    for tex_file in tex_files:
        rel_path = tex_file.relative_to(root)
        print(f"Compiling {rel_path}... ", end="", flush=True)
        result = compile_tex(tex_file)
        results.append(result)

        if result.success:
            print("OK")
        else:
            print("FAILED")

    print("\n" + "=" * 50)
    print("Compilation Summary")
    print("=" * 50)

    failed = []
    for result in results:
        rel_path = result.tex_file.relative_to(root)
        status = "OK" if result.success else "FAILED"
        print(f"  {rel_path}: {status}")
        if not result.success:
            failed.append(result)

    if failed:
        print("\n" + "=" * 50)
        print("Failed Compilations")
        print("=" * 50)
        for result in failed:
            rel_path = result.tex_file.relative_to(root)
            print(f"\n--- {rel_path} ---")
            if result.error:
                print(result.error)
        print("\nSome compilations failed!")
        sys.exit(1)
    else:
        print("\nAll compilations successful!")
        sys.exit(0)

if __name__ == "__main__":
    main()
