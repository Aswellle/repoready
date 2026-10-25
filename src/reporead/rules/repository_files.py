"""Essential-file existence checks.

Every check receives a ScanContext and returns findings (empty list =
the rule passed). Findings are created through make_finding() so
severities stay pinned to the registry. Existence checks never open
file contents.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

from reporead.rules.registry import make_finding

from .context import ScanContext

# Case-insensitive matches against lower-cased entry names.
README_NAMES = frozenset({"readme", "readme.md"})
LICENSE_NAMES = frozenset({"license", "license.md", "license.txt"})
MANIFEST_NAMES = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "package.json",
        "cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "gemfile",
        "composer.json",
    }
)
TEST_DIRS = frozenset({"tests", "test", "e2e", "__tests__"})
TEST_CONFIG_FILES = frozenset(
    {
        # Python
        "conftest.py",
        "pytest.ini",
        "tox.ini",
        "noxfile.py",
        # JavaScript / TypeScript runners
        "playwright.config.ts",
        "playwright.config.js",
        "playwright.config.mjs",
        "vitest.config.ts",
        "vitest.config.js",
        "vitest.config.mjs",
        "jest.config.js",
        "jest.config.ts",
        "jest.config.mjs",
        "jest.config.cjs",
        "cypress.config.ts",
        "cypress.config.js",
        "karma.conf.js",
        "karma.conf.cjs",
    }
)
TEST_FILE_PATTERNS = (
    "test_*.py",
    "*_test.py",
    "*.test.ts",
    "*.test.tsx",
    "*.test.js",
    "*.test.jsx",
    "*.test.mjs",
    "*.test.cjs",
    "*.spec.ts",
    "*.spec.tsx",
    "*.spec.js",
    "*.spec.jsx",
    "*.spec.mjs",
    "*.spec.cjs",
)
# Case-insensitive root-level CI configs (GitHub Actions is handled via
# the .github/workflows listing on the context).
ROOT_CI_FILES = frozenset(
    {".gitlab-ci.yml", "azure-pipelines.yml", ".travis.yml", ".drone.yml"}
)


def check_readme(ctx: ScanContext):
    if ctx.root_files_lower & README_NAMES:
        return []
    return [
        make_finding(
            "repo.readme.missing",
            title="README file not found",
            detail=(
                "No README or README.md was found at the repository root, "
                "so the project has no front page for strangers."
            ),
            path="README.md",
            evidence=(
                "Checked the repository root for README.md or README "
                "(case-insensitive); none found."
            ),
            suggestion=(
                "Add a README.md that states what the project does, "
                "how to install it, and how to run it."
            ),
        )
    ]


def check_license(ctx: ScanContext):
    if ctx.root_files_lower & LICENSE_NAMES:
        return []
    return [
        make_finding(
            "repo.license.missing",
            title="LICENSE file not found",
            detail=(
                "No LICENSE file was found at the repository root; without a "
                "license nobody can legally use or contribute to the code."
            ),
            path="LICENSE",
            evidence=(
                "Checked the repository root for LICENSE, LICENSE.md or "
                "LICENSE.txt (case-insensitive); none found."
            ),
            suggestion=(
                "Add a LICENSE file with the license chosen by the "
                "project maintainers."
            ),
        )
    ]


def check_manifest(ctx: ScanContext):
    if ctx.root_files_lower & MANIFEST_NAMES:
        return []
    return [
        make_finding(
            "repo.manifest.missing",
            title="No dependency manifest found",
            detail=(
                "No known dependency or project manifest was found; "
                "dependencies and build tooling are not declared."
            ),
            path=None,
            evidence=(
                "Checked the repository root for pyproject.toml, setup.py, "
                "setup.cfg, requirements.txt, package.json, Cargo.toml, "
                "go.mod, pom.xml, build.gradle, build.gradle.kts, Gemfile "
                "or composer.json; none found."
            ),
            suggestion=(
                "Add the manifest that matches your ecosystem (for example "
                "pyproject.toml for Python or package.json for Node.js)."
            ),
        )
    ]


def check_gitignore(ctx: ScanContext):
    # Exact case: git only reads a file literally named ".gitignore" on
    # case-sensitive filesystems, so a case variant is not reliable.
    if any(name == ".gitignore" for name in ctx.root_file_names):
        return []
    return [
        make_finding(
            "repo.gitignore.missing",
            title=".gitignore not found",
            detail=(
                "No .gitignore file was found; generated files and local "
                "secrets can be committed by accident."
            ),
            path=".gitignore",
            evidence=(
                "Checked the repository root for a file named exactly "
                "'.gitignore'; none found."
            ),
            suggestion=(
                "Add a .gitignore covering build outputs, caches and "
                "local environment files."
            ),
        )
    ]


def check_tests(ctx: ScanContext):
    if ctx.root_dirs_lower & TEST_DIRS:
        return []
    if ctx.root_files_lower & TEST_CONFIG_FILES:
        return []
    for name in ctx.root_file_names:
        lowered = name.lower()
        if any(fnmatch.fnmatch(lowered, pattern) for pattern in TEST_FILE_PATTERNS):
            return []
    return [
        make_finding(
            "repo.tests.missing",
            title="No test directory or test configuration found",
            detail=(
                "No test directory or test configuration was detected; this "
                "does not prove tests exist elsewhere, but nothing signals "
                "runnable tests."
            ),
            path=None,
            evidence=(
                "Checked for directories 'tests', 'test', 'e2e' or "
                "'__tests__', Python files conftest.py, pytest.ini, "
                "tox.ini, noxfile.py, JS/TS runner configs such as "
                "playwright/vitest/jest/cypress configs, and root files "
                "matching test_*.py, *_test.py, *.test.* or *.spec.*; "
                "none found."
            ),
            suggestion=(
                "Add a tests/ directory with at least one runnable test "
                "and wire it into your CI."
            ),
        )
    ]


def check_ci(ctx: ScanContext):
    if any(
        name.lower().endswith((".yml", ".yaml")) for name in ctx.workflows_files
    ):
        return []
    if ctx.root_files_lower & ROOT_CI_FILES:
        return []
    return [
        make_finding(
            "repo.ci.missing",
            title="No CI workflow found",
            detail=(
                "No continuous integration workflow was detected; "
                "regressions have no automated gate."
            ),
            path=".github/workflows",
            evidence=(
                "Checked .github/workflows for *.yml or *.yaml and root "
                "files .gitlab-ci.yml, azure-pipelines.yml, .travis.yml or "
                ".drone.yml; none found."
            ),
            suggestion=(
                "Add a CI workflow (for example .github/workflows/ci.yml) "
                "that runs your test suite."
            ),
        )
    ]


# Order mirrors the §2a table in docs/spec/01-architecture-rules.md.
CHECKS = (
    check_readme,
    check_license,
    check_manifest,
    check_gitignore,
    check_tests,
    check_ci,
)


def find_readme(ctx: ScanContext) -> Path | None:
    """Return the README path if present and contained in root, else None.

    Used by the README content rules. A README whose realpath escapes
    the scan root (symlink) is treated as absent so content rules never
    read outside the boundary.
    """
    for name in sorted(ctx.root_file_names):
        if name.lower() in README_NAMES:
            path = ctx.root / name
            try:
                resolved = path.resolve()
                inside = resolved.is_relative_to(ctx.root.resolve())
            except OSError:
                return None
            return path if inside else None
    return None
