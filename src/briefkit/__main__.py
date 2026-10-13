"""Allow running as ``python -m briefkit``; the exit code is the CLI's, not always 0."""

from briefkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
