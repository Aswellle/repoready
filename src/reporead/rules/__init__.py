"""Rule registry and check engine.

REGISTRY (rules/registry.py) is the single source of truth for rule
ids, severities and categories; it must stay consistent with the table
in docs/spec/01-architecture-rules.md §2a (enforced by tests). The
check engine wiring lands together with the rule modules.
"""
