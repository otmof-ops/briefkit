# ADR-001: Use argparse Instead of click for CLI

**Status:** Accepted
**Date:** 2026-03-31

## Context

BriefKit is designed as a zero-config, minimal-dependency tool. Adding click (or typer) would double the runtime dependency count from 2 to 3. The CLI has 11 subcommands with consistent flag patterns.

## Decision

Use Python's built-in argparse module exclusively for CLI parsing. No third-party CLI framework.

## Consequences

- **Positive:** Zero additional dependencies for CLI; works anywhere Python runs; full control over help text formatting
- **Negative:** Verbose subcommand registration (~80 lines of argparse setup); no auto-completion support; no rich help formatting without manual work
- **Constraint:** Any contributor adding click/typer must justify the dependency addition against this ADR
