# ADR-002: Four-Level Content Hierarchy

**Status:** Accepted
**Date:** 2026-03-31

## Context

BriefKit was extracted from The Codex, which organizes 45,000+ files into a four-level hierarchy: root (entire collection) > division (16 domains) > subject (topics within domains) > doc-set (individual documentation sets with numbered markdown files). The extraction tool needed to handle all four levels with different aggregation strategies.

## Decision

Implement a four-level hierarchy model: root (level 4), division (level 1), subject (level 2), doc-set (level 3). Each level has a dedicated extraction function that aggregates content from child levels.

## Consequences

- **Positive:** Maps naturally to real documentation structures (organization > department > project > document); enables recursive batch processing at any level
- **Negative:** Baked into extractor.py (4 aggregation functions), config.py (hierarchy settings), doc_ids.py (level-based ID formatting), and all 6 templates; cannot easily change to 3 or 5 levels without touching 6+ files
- **Constraint:** New levels require new aggregation functions and template support
