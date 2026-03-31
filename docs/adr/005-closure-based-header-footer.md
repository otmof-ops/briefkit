# ADR-005: Closure-Based Header/Footer State (Replacing Module Global)

**Status:** Accepted
**Date:** 2026-03-31

## Context

The original implementation used a module-level mutable dict `_hf_state` to pass section title, date, and document ID to ReportLab's header/footer callback. This worked for single-threaded execution but blocked parallel batch processing — concurrent generate() calls would overwrite each other's state.

During the v1.0 refactor, the closure-based `make_header_footer(state, brand)` pattern from elements/header_footer.py was adopted. However, the module-level `_hf_state` was retained and dual-written "for backward compatibility."

## Decision

Remove the module-level `_hf_state` entirely. Use only the closure-based pattern where state is captured as a local variable in generate() and passed to make_header_footer(). No backward compatibility shim.

## Consequences

- **Positive:** Thread-safe by construction; no shared mutable state; unblocks ProcessPoolExecutor for parallel batch processing (4-8x throughput); single code path instead of dual-write
- **Negative:** Any external code that imported `_hf_state` from `briefkit.generator` will break — verified that no such consumer exists
- **Enables:** Future parallel batch processing (batch.py ProcessPoolExecutor)
