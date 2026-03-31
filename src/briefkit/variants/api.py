"""
briefkit.variants.api — REST / GraphQL API documentation variant.

Adds: endpoint reference table, authentication reference section,
request/response schema summary.
"""

from __future__ import annotations

import re

from reportlab.platypus import PageBreak, Spacer

from briefkit.styles import _safe_para, build_styles
from briefkit.elements.tables import build_data_table
from briefkit.elements.callout import build_callout_box
from briefkit.variants import DocSetVariant, _register, collect_text

from reportlab.lib.units import mm

# HTTP verbs for endpoint detection
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

# Common auth scheme names
_AUTH_SCHEMES = [
    "Bearer token", "JWT", "OAuth 2.0", "OAuth", "API key", "HMAC",
    "Basic Auth", "mTLS", "Session cookie", "SAML", "OpenID Connect",
]

_AUTH_PATTERNS = {
    "Bearer token":    r'\bBearer\b',
    "JWT":             r'\bJWT\b|JSON\s+Web\s+Token',
    "OAuth 2.0":       r'\bOAuth\s+2\.0\b',
    "OAuth":           r'\bOAuth\b',
    "API key":         r'\bAPI\s+key\b|apikey\b|api_key\b',
    "HMAC":            r'\bHMAC\b',
    "Basic Auth":      r'\bBasic\s+Auth(?:entication)?\b',
    "mTLS":            r'\bmTLS\b|mutual\s+TLS',
    "Session cookie":  r'\bsession\s+cookie\b|cookie-based\b',
    "SAML":            r'\bSAML\b',
    "OpenID Connect":  r'\bOpenID\s+Connect\b|OIDC\b',
}


@_register
class APIVariant(DocSetVariant):
    """REST / GraphQL API documentation variant."""

    name = "api"
    auto_detect_keywords = [
        "endpoint", "REST", "GET", "POST",
        "authentication", "API", "response", "request",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("API Documentation Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Endpoint table ---
        flowables.append(_safe_para("Endpoint Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        endpoint_rows = self._extract_endpoints(content, all_content)
        if endpoint_rows:
            flowables.extend(build_data_table(
                ["Method", "Path", "Description", "Auth Required"],
                endpoint_rows[:20],
                title="API Endpoint Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No structured endpoint definitions found — see numbered documents.",
                s_body,
            ))

        # --- Authentication reference ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Authentication Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        auth_rows = self._extract_auth_schemes(all_content)
        if auth_rows:
            flowables.extend(build_data_table(
                ["Scheme", "Description", "Notes"],
                auth_rows,
                title="Authentication Mechanisms",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No authentication scheme documentation found — see source documents.",
                s_body,
            ))

        # --- Response codes summary ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("HTTP Response Codes", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        code_rows = self._extract_response_codes(content, all_content)
        if code_rows:
            flowables.extend(build_data_table(
                ["Status Code", "Meaning", "Notes"],
                code_rows[:12],
                title="Response Code Reference",
                brand=brand,
            ))
        else:
            # Provide standard reference
            flowables.extend(build_data_table(
                ["Status Code", "Meaning", "Notes"],
                [
                    ["200", "OK", "Success"],
                    ["201", "Created", "Resource created"],
                    ["400", "Bad Request", "Invalid input"],
                    ["401", "Unauthorized", "Authentication required"],
                    ["403", "Forbidden", "Insufficient permissions"],
                    ["404", "Not Found", "Resource does not exist"],
                    ["429", "Too Many Requests", "Rate limit exceeded"],
                    ["500", "Internal Server Error", "Server-side failure"],
                ],
                title="Standard HTTP Response Codes",
                brand=brand,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_endpoints(self, content, all_content):
        rows = []
        seen = set()

        # Check structured tables
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("endpoint", "path", "method", "route", "url")):
                    for row in tbl.get("rows", [])[:12]:
                        padded = (list(row) + ["", "", "", ""])[:4]
                        key = str(padded[0]).lower() + str(padded[1]).lower()
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Scan for inline endpoint patterns: "GET /api/v1/resource"
        ep_pat = re.compile(
            r'\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[^\s\)\]\}]{1,80})',
            re.IGNORECASE,
        )
        for m in ep_pat.finditer(all_content):
            method = m.group(1).upper()
            path   = m.group(2).strip()
            key    = method + path
            if key not in seen:
                rows.append([method, path, "—", "—"])
                seen.add(key)

        return rows

    def _extract_auth_schemes(self, all_content):
        rows = []
        for scheme, pattern in _AUTH_PATTERNS.items():
            if re.search(pattern, all_content, re.IGNORECASE):
                rows.append([scheme, "Detected in source", ""])
        return rows

    def _extract_response_codes(self, content, all_content):
        rows = []
        seen = set()

        # Check tables
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("status", "code", "response", "error")):
                    for row in tbl.get("rows", [])[:10]:
                        padded = (list(row) + ["", "", ""])[:3]
                        key = str(padded[0])
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Scan for status code mentions: "returns 404", "HTTP 200", "status 401"
        code_pat = re.compile(
            r'(?:HTTP|returns?|status|code)\s+([1-5]\d{2})\b',
            re.IGNORECASE,
        )
        _http_meanings = {
            "200": "OK", "201": "Created", "204": "No Content",
            "400": "Bad Request", "401": "Unauthorized", "403": "Forbidden",
            "404": "Not Found", "405": "Method Not Allowed",
            "422": "Unprocessable Entity", "429": "Too Many Requests",
            "500": "Internal Server Error", "502": "Bad Gateway",
            "503": "Service Unavailable",
        }
        for m in code_pat.finditer(all_content):
            code = m.group(1)
            if code not in seen:
                rows.append([code, _http_meanings.get(code, "—"), ""])
                seen.add(code)

        return sorted(rows, key=lambda r: r[0])
