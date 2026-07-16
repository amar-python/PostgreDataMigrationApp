#!/usr/bin/env python3
"""Verify that file paths referenced in GitHub Actions workflows exist.

After the repository was restructured (tests/ -> backend/migration/tests/,
build/ -> backend/migration/build/, evals/ -> backend/migration/evals/), a
number of workflow steps kept pointing at the old locations and CI broke in
confusing ways. This script prevents that class of failure permanently:

  * It parses every ``.github/workflows/*.yml`` / ``*.yaml`` file.
  * For every ``run:`` block it extracts path-like tokens (tokens that contain
    a ``/`` or end in a known source extension) and checks that they exist in
    the working tree.
  * For every ``uses:`` reference to a *local* action (``./path/to/action``)
    it checks the action directory/file exists. Marketplace actions
    (``owner/repo@ref``) are ignored — they do not live in this repository.

Exit code 0 when all references resolve, 1 when at least one stale reference
is found (so CI can fail the build).

Usage:
    python3 tools/verify_workflow_paths.py [--root REPO_ROOT] [--verbose]

Stdlib-only on purpose: it must run before any dependencies are installed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Extensions that indicate a token is meant to be a file in this repository.
CHECKED_EXTENSIONS = (
    ".py", ".sh", ".ps1", ".sql", ".yml", ".yaml", ".txt", ".ini",
    ".cfg", ".toml", ".json", ".env", ".md",
)

# Paths that are *created at runtime* by workflow steps (heredocs, artifacts,
# generated reports) and therefore legitimately absent from the repository.
RUNTIME_GENERATED = {
    "backend/migration/build/config.local.env",
}

# Prefixes that are never repository paths.
IGNORED_PREFIXES = (
    "http://", "https://", "git@", "/dev/", "/tmp/", "/usr/", "/etc/",
    "/opt/", "/home/", "~/",
)

# Shell/CLI noise that looks path-like but is not a repo file.
NOISE_TOKENS = {
    "usr/bin/env", "bin/bash", "bin/sh",
}

TOKEN_RE = re.compile(r"""[A-Za-z0-9_./\\~-]+""")


def find_repo_root(start: Path) -> Path:
    """Walk upwards until a .github directory is found."""
    for candidate in [start, *start.parents]:
        if (candidate / ".github").is_dir():
            return candidate
    return start


def iter_blocks(text: str):
    """Yield (kind, value) for every ``run:`` and ``uses:`` entry.

    A tiny purpose-built YAML walk: we only need the scalar attached to
    ``run:``/``uses:`` keys, including ``run: |`` multi-line blocks. This
    avoids a PyYAML dependency so the script can run pre-install.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        m = re.match(r"(?:-\s+)?(run|uses):\s*(.*)$", stripped)
        if m:
            kind, value = m.group(1), m.group(2).strip()
            if value in ("|", ">", "|-", ">-", ""):
                # Multi-line block scalar: collect more-indented lines.
                indent = len(line) - len(line.lstrip())
                block: list[str] = []
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.strip() == "":
                        block.append("")
                        j += 1
                        continue
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent <= indent:
                        break
                    block.append(nxt.strip())
                    j += 1
                yield kind, "\n".join(block)
                i = j
                continue
            yield kind, value
        i += 1


def strip_quotes(token: str) -> str:
    return token.strip().strip("'\"")


def extract_path_candidates(command: str):
    """Extract repository-path-like tokens from a shell command string."""
    for raw_line in command.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Remove shell variable references and escape characters so they are
        # never mistaken for literal paths (e.g. \"$db\" must not yield 'db/').
        line = re.sub(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", " ", line)
        line = line.replace("\\", " ")
        for token in TOKEN_RE.findall(line):
            token = strip_quotes(token)
            if not token or token in NOISE_TOKENS:
                continue
            if token.startswith(IGNORED_PREFIXES):
                continue
            # Flags/options (e.g. --cov-report) are not literal paths.
            if token.startswith("-"):
                continue
            has_ext = token.lower().endswith(CHECKED_EXTENSIONS)
            is_dir_ref = "/" in token and token.endswith("/")
            if not has_ext and not is_dir_ref:
                continue  # only verify explicit file/directory references
            # Skip pure version-ish or numeric tokens (e.g. "3.11").
            if re.fullmatch(r"[\d.]+", token):
                continue
            token = token.lstrip("./")
            if token:
                yield token


def verify(root: Path, verbose: bool = False) -> int:
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        print(f"ERROR: no workflows directory at {workflows_dir}", file=sys.stderr)
        return 1

    failures: list[tuple[str, str]] = []
    checked = 0

    for wf in sorted(workflows_dir.glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8")
        for kind, value in iter_blocks(text):
            if kind == "uses":
                ref = strip_quotes(value)
                if ref.startswith("./"):  # local action
                    checked += 1
                    target = root / ref[2:]
                    ok = target.exists()
                    if verbose:
                        print(f"[{'OK' if ok else 'MISSING'}] {wf.name}: uses {ref}")
                    if not ok:
                        failures.append((wf.name, f"uses: {ref}"))
                continue

            for candidate in extract_path_candidates(value):
                if candidate in RUNTIME_GENERATED:
                    continue
                target = root / candidate
                checked += 1
                ok = target.exists()
                if verbose:
                    print(f"[{'OK' if ok else 'MISSING'}] {wf.name}: {candidate}")
                if not ok:
                    failures.append((wf.name, candidate))

    print(f"verify_workflow_paths: checked {checked} references "
          f"across {len(list(workflows_dir.glob('*.y*ml')))} workflow file(s).")

    if failures:
        print("\nSTALE WORKFLOW PATH REFERENCES FOUND:", file=sys.stderr)
        for wf_name, ref in failures:
            print(f"  - {wf_name}: '{ref}' does not exist in the repository",
                  file=sys.stderr)
        print("\nFix the workflow (or add the path to RUNTIME_GENERATED in "
              "tools/verify_workflow_paths.py if it is created at runtime).",
              file=sys.stderr)
        return 1

    print("All workflow path references resolve. ✔")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None,
                        help="Repository root (default: auto-detected)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print every checked reference")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else find_repo_root(
        Path(__file__).resolve().parent)
    return verify(root, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
