"""
briefkit.presets.licenses
~~~~~~~~~~~~~~~~~~~~~~~~~~
License presets sourced from Codex Division 11
(licensing-and-intellectual-property).

Each preset defines:
  spdx        — SPDX identifier (empty for non-standard licenses)
  name        — Human-readable license name
  url         — Canonical URL for the license text
  category    — permissive | copyleft | source-available | creative-commons
                | proprietary | public-domain | unlicensed
  notice      — Short notice line for PDF back cover / footer
  commercial  — Whether commercial use is permitted (True/False/None)
"""

from __future__ import annotations

LICENSE_PRESETS: dict[str, dict[str, str | bool | None]] = {
    # ── Permissive Software Licenses ─────────────────────────────────
    "MIT": {
        "spdx": "MIT",
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
        "category": "permissive",
        "notice": "Released under the MIT License.",
        "commercial": True,
    },
    "Apache-2.0": {
        "spdx": "Apache-2.0",
        "name": "Apache License 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
        "category": "permissive",
        "notice": "Licensed under the Apache License, Version 2.0.",
        "commercial": True,
    },
    "BSD-2-Clause": {
        "spdx": "BSD-2-Clause",
        "name": "BSD 2-Clause (Simplified)",
        "url": "https://opensource.org/licenses/BSD-2-Clause",
        "category": "permissive",
        "notice": "Released under the BSD 2-Clause License.",
        "commercial": True,
    },
    "BSD-3-Clause": {
        "spdx": "BSD-3-Clause",
        "name": "BSD 3-Clause (New/Revised)",
        "url": "https://opensource.org/licenses/BSD-3-Clause",
        "category": "permissive",
        "notice": "Released under the BSD 3-Clause License.",
        "commercial": True,
    },
    "ISC": {
        "spdx": "ISC",
        "name": "ISC License",
        "url": "https://opensource.org/licenses/ISC",
        "category": "permissive",
        "notice": "Released under the ISC License.",
        "commercial": True,
    },
    "Unlicense": {
        "spdx": "Unlicense",
        "name": "The Unlicense",
        "url": "https://unlicense.org/",
        "category": "public-domain",
        "notice": "Released into the public domain.",
        "commercial": True,
    },
    "Zlib": {
        "spdx": "Zlib",
        "name": "zlib License",
        "url": "https://opensource.org/licenses/Zlib",
        "category": "permissive",
        "notice": "Released under the zlib License.",
        "commercial": True,
    },
    "BSL-1.0": {
        "spdx": "BSL-1.0",
        "name": "Boost Software License 1.0",
        "url": "https://www.boost.org/LICENSE_1_0.txt",
        "category": "permissive",
        "notice": "Released under the Boost Software License 1.0.",
        "commercial": True,
    },

    # ── Copyleft Software Licenses ───────────────────────────────────
    "GPL-2.0": {
        "spdx": "GPL-2.0-only",
        "name": "GNU General Public License v2.0",
        "url": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
        "category": "copyleft",
        "notice": "Licensed under the GNU GPL v2.0.",
        "commercial": True,
    },
    "GPL-3.0": {
        "spdx": "GPL-3.0-only",
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
        "category": "copyleft",
        "notice": "Licensed under the GNU GPL v3.0.",
        "commercial": True,
    },
    "LGPL-3.0": {
        "spdx": "LGPL-3.0-only",
        "name": "GNU Lesser General Public License v3.0",
        "url": "https://www.gnu.org/licenses/lgpl-3.0.html",
        "category": "copyleft",
        "notice": "Licensed under the GNU LGPL v3.0.",
        "commercial": True,
    },
    "AGPL-3.0": {
        "spdx": "AGPL-3.0-only",
        "name": "GNU Affero General Public License v3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
        "category": "copyleft",
        "notice": "Licensed under the GNU AGPL v3.0.",
        "commercial": True,
    },
    "MPL-2.0": {
        "spdx": "MPL-2.0",
        "name": "Mozilla Public License 2.0",
        "url": "https://www.mozilla.org/en-US/MPL/2.0/",
        "category": "copyleft",
        "notice": "Licensed under the MPL 2.0.",
        "commercial": True,
    },
    "EUPL-1.2": {
        "spdx": "EUPL-1.2",
        "name": "European Union Public Licence 1.2",
        "url": "https://joinup.ec.europa.eu/licence/eupl",
        "category": "copyleft",
        "notice": "Licensed under the EUPL 1.2.",
        "commercial": True,
    },

    # ── Source-Available Licenses ────────────────────────────────────
    "BUSL-1.1": {
        "spdx": "BUSL-1.1",
        "name": "Business Source License 1.1",
        "url": "https://mariadb.com/bsl11/",
        "category": "source-available",
        "notice": "Licensed under the Business Source License 1.1.",
        "commercial": False,
    },
    "Elastic-2.0": {
        "spdx": "Elastic-2.0",
        "name": "Elastic License 2.0",
        "url": "https://www.elastic.co/licensing/elastic-license",
        "category": "source-available",
        "notice": "Licensed under the Elastic License 2.0.",
        "commercial": False,
    },
    "SSPL-1.0": {
        "spdx": "SSPL-1.0",
        "name": "Server Side Public License v1",
        "url": "https://www.mongodb.com/licensing/server-side-public-license",
        "category": "source-available",
        "notice": "Licensed under the SSPL v1.",
        "commercial": False,
    },

    # ── Creative Commons Licenses ────────────────────────────────────
    "CC0-1.0": {
        "spdx": "CC0-1.0",
        "name": "Creative Commons Zero v1.0 Universal",
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "category": "public-domain",
        "notice": "Dedicated to the public domain under CC0 1.0.",
        "commercial": True,
    },
    "CC-BY-4.0": {
        "spdx": "CC-BY-4.0",
        "name": "Creative Commons Attribution 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/",
        "category": "creative-commons",
        "notice": "Licensed under CC BY 4.0.",
        "commercial": True,
    },
    "CC-BY-SA-4.0": {
        "spdx": "CC-BY-SA-4.0",
        "name": "Creative Commons Attribution-ShareAlike 4.0",
        "url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "category": "creative-commons",
        "notice": "Licensed under CC BY-SA 4.0.",
        "commercial": True,
    },
    "CC-BY-NC-4.0": {
        "spdx": "CC-BY-NC-4.0",
        "name": "Creative Commons Attribution-NonCommercial 4.0",
        "url": "https://creativecommons.org/licenses/by-nc/4.0/",
        "category": "creative-commons",
        "notice": "Licensed under CC BY-NC 4.0. Non-commercial use only.",
        "commercial": False,
    },
    "CC-BY-NC-SA-4.0": {
        "spdx": "CC-BY-NC-SA-4.0",
        "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "category": "creative-commons",
        "notice": "Licensed under CC BY-NC-SA 4.0. Non-commercial use only.",
        "commercial": False,
    },
    "CC-BY-ND-4.0": {
        "spdx": "CC-BY-ND-4.0",
        "name": "Creative Commons Attribution-NoDerivatives 4.0",
        "url": "https://creativecommons.org/licenses/by-nd/4.0/",
        "category": "creative-commons",
        "notice": "Licensed under CC BY-ND 4.0. No derivatives permitted.",
        "commercial": True,
    },

    # ── Specialized Licenses ─────────────────────────────────────────
    "OFL-1.1": {
        "spdx": "OFL-1.1",
        "name": "SIL Open Font License 1.1",
        "url": "https://scripts.sil.org/OFL",
        "category": "permissive",
        "notice": "Licensed under the SIL OFL 1.1.",
        "commercial": True,
    },
    "ODbL-1.0": {
        "spdx": "ODbL-1.0",
        "name": "Open Database License v1.0",
        "url": "https://opendatacommons.org/licenses/odbl/",
        "category": "copyleft",
        "notice": "Licensed under the ODbL 1.0.",
        "commercial": True,
    },

    # ── Proprietary / All Rights Reserved ────────────────────────────
    "proprietary": {
        "spdx": "",
        "name": "Proprietary — All Rights Reserved",
        "url": "",
        "category": "proprietary",
        "notice": "All rights reserved. No part of this document may be reproduced without permission.",
        "commercial": None,
    },

    # ── Unlicensed (skip) ────────────────────────────────────────────
    "unlicensed": {
        "spdx": "",
        "name": "Unlicensed Project",
        "url": "",
        "category": "unlicensed",
        "notice": "",
        "commercial": None,
    },
}

# Ordered categories for display
LICENSE_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Permissive (software)", [
        "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
        "ISC", "Zlib", "BSL-1.0",
    ]),
    ("Copyleft (software)", [
        "GPL-2.0", "GPL-3.0", "LGPL-3.0", "AGPL-3.0",
        "MPL-2.0", "EUPL-1.2",
    ]),
    ("Source-available", [
        "BUSL-1.1", "Elastic-2.0", "SSPL-1.0",
    ]),
    ("Creative Commons (content)", [
        "CC-BY-4.0", "CC-BY-SA-4.0",
        "CC-BY-NC-4.0", "CC-BY-NC-SA-4.0", "CC-BY-ND-4.0",
    ]),
    ("Public domain", [
        "CC0-1.0", "Unlicense",
    ]),
    ("Specialized", [
        "OFL-1.1", "ODbL-1.0",
    ]),
    ("Proprietary / Other", [
        "proprietary", "unlicensed",
    ]),
]


def get_license(name: str) -> dict | None:
    """Return the license preset dict for the given name, or None."""
    return LICENSE_PRESETS.get(name)


def list_licenses() -> list[str]:
    """Return all license preset names."""
    return sorted(LICENSE_PRESETS.keys())
