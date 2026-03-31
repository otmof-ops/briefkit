# ADR-004: print() Over Python logging Module

**Status:** Accepted
**Date:** 2026-03-31

## Context

BriefKit is a local-only CLI tool run interactively or in CI pipelines. Python's logging module adds configuration complexity (handlers, formatters, levels) that is disproportionate for a tool that produces 3-5 lines of output per invocation.

## Decision

Use print() for all user-facing output. stdout for progress, stderr for errors and warnings. Provide --json flag for structured output in CI contexts. Provide --quiet to suppress non-error output.

## Consequences

- **Positive:** Zero logging configuration overhead; predictable output; clean stdout/stderr separation; --json provides structured alternative
- **Negative:** --verbose has limited utility (only affects exception tracebacks at top level); no log levels (DEBUG/INFO/WARNING); no file logging capability
- **Accepted tradeoff:** The init template previously included a log_dir config key that was never implemented; this has been removed to avoid confusion
