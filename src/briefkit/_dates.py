# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""
briefkit._dates
~~~~~~~~~~~~~~~
The one place briefkit asks what day it is.

Byte-reproducible builds need a stable date, so when ``SOURCE_DATE_EPOCH``
is set (the reproducible-builds convention ReportLab also honours for the
PDF timestamps) every date briefkit prints, from the cover to the doc-ID
registry, derives from it instead of the wall clock.
"""

from __future__ import annotations

import datetime
import os


def today() -> datetime.date:
    """Today's date, or the date of ``SOURCE_DATE_EPOCH`` (UTC) when it is set."""
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw:
        try:
            return datetime.datetime.fromtimestamp(int(raw), tz=datetime.timezone.utc).date()
        except (ValueError, OverflowError, OSError):
            pass
    return datetime.date.today()


def current_year() -> int:
    """The year of :func:`today`."""
    return today().year


__all__ = ["today", "current_year"]
