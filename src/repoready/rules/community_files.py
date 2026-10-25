"""Community-health file existence checks.

Same contract as repository_files: each check takes a ScanContext and
returns findings through make_finding(); empty list means the rule
passed. Existence checks never open file contents.
"""

from __future__ import annotations

from repoready.rules.registry import make_finding

from .context import ScanContext

CONTRIBUTING_NAMES = frozenset({"contributing.md"})
SECURITY_NAMES = frozenset({"security.md"})
COC_NAMES = frozenset({"code_of_conduct.md", "conduct.md"})
CHANGELOG_NAMES = frozenset(
    {
        "changelog.md",
        "history.md",
        "changes.md",
        "changes.rst",
        "news.md",
        "news.rst",
        "releases.md",
    }
)
# docs/releases.md is the documented alternative location.
DOCS_RELEASE_NAMES = frozenset({"releases.md"})
PR_TEMPLATE_NAMES = frozenset({"pull_request_template.md"})


def check_contributing(ctx: ScanContext):
    if (ctx.root_files_lower | ctx.github_files_lower) & CONTRIBUTING_NAMES:
        return []
    return [
        make_finding(
            "repo.contributing.missing",
            title="CONTRIBUTING.md not found",
            detail=(
                "No CONTRIBUTING.md was found; potential contributors have "
                "no guidance on how to help."
            ),
            path="CONTRIBUTING.md",
            evidence=(
                "Checked the repository root and .github/ for "
                "CONTRIBUTING.md (case-insensitive); none found."
            ),
            suggestion=(
                "Add a CONTRIBUTING.md describing how to set up the "
                "project and submit changes."
            ),
        )
    ]


def check_security(ctx: ScanContext):
    if (ctx.root_files_lower | ctx.github_files_lower) & SECURITY_NAMES:
        return []
    return [
        make_finding(
            "repo.security.missing",
            title="SECURITY.md not found",
            detail=(
                "No SECURITY.md was found; reporters have no private "
                "channel for security issues."
            ),
            path="SECURITY.md",
            evidence=(
                "Checked the repository root and .github/ for SECURITY.md "
                "(case-insensitive); none found."
            ),
            suggestion=(
                "Add a SECURITY.md explaining how to report "
                "vulnerabilities privately."
            ),
        )
    ]


def check_coc(ctx: ScanContext):
    if (ctx.root_files_lower | ctx.github_files_lower) & COC_NAMES:
        return []
    return [
        make_finding(
            "repo.coc.missing",
            title="CODE_OF_CONDUCT.md not found",
            detail=(
                "No CODE_OF_CONDUCT.md was found; community behaviour "
                "expectations are not stated."
            ),
            path="CODE_OF_CONDUCT.md",
            evidence=(
                "Checked the repository root and .github/ for "
                "CODE_OF_CONDUCT.md or CONDUCT.md (case-insensitive); "
                "none found."
            ),
            suggestion=(
                "Add a CODE_OF_CONDUCT.md defining expected behaviour and "
                "an enforcement contact."
            ),
        )
    ]


def check_changelog(ctx: ScanContext):
    if (ctx.root_files_lower & CHANGELOG_NAMES) or (
        ctx.docs_files_lower & DOCS_RELEASE_NAMES
    ):
        return []
    return [
        make_finding(
            "repo.changelog.missing",
            title="CHANGELOG not found",
            detail=(
                "No changelog file was found; release changes are not "
                "traceable."
            ),
            path="CHANGELOG.md",
            evidence=(
                "Checked the repository root for CHANGELOG.md, HISTORY.md, "
                "CHANGES.md/.rst, NEWS.md/.rst, RELEASES.md "
                "(case-insensitive) and docs/releases.md; none found."
            ),
            suggestion=(
                "Add a CHANGELOG.md (or docs/releases.md) and record "
                "user-visible changes per release."
            ),
        )
    ]


def check_issue_templates(ctx: ScanContext):
    if ctx.issue_template_files:
        return []
    return [
        make_finding(
            "repo.templates.issues.missing",
            title="No issue templates found",
            detail=(
                ".github/ISSUE_TEMPLATE/ contains no files; bug reports "
                "arrive unstructured."
            ),
            path=".github/ISSUE_TEMPLATE",
            evidence=(
                "Checked .github/ISSUE_TEMPLATE/ for at least one "
                "template file; none found."
            ),
            suggestion=(
                "Add at least one issue template (for example "
                "bug_report.md) in .github/ISSUE_TEMPLATE/."
            ),
        )
    ]


def check_pr_template(ctx: ScanContext):
    if (
        (ctx.root_files_lower & PR_TEMPLATE_NAMES)
        or (ctx.github_files_lower & PR_TEMPLATE_NAMES)
        or ("pull_request_template" in ctx.github_dirs_lower)
    ):
        return []
    return [
        make_finding(
            "repo.templates.pr.missing",
            title="No pull request template found",
            detail=(
                "No PULL_REQUEST_TEMPLATE.md was found at the root or "
                "under .github; pull requests arrive unstructured."
            ),
            path=".github/PULL_REQUEST_TEMPLATE.md",
            evidence=(
                "Checked the repository root and .github/ for "
                "PULL_REQUEST_TEMPLATE.md (case-insensitive) or a "
                ".github/PULL_REQUEST_TEMPLATE/ directory; none found."
            ),
            suggestion=(
                "Add a pull request template describing what to include "
                "in a PR."
            ),
        )
    ]


# Order mirrors the §2a table in docs/spec/01-architecture-rules.md.
CHECKS = (
    check_contributing,
    check_security,
    check_coc,
    check_changelog,
    check_issue_templates,
    check_pr_template,
)
