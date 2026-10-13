# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""Allow running as ``python -m briefkit``; the exit code is the CLI's, not always 0."""

from briefkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
