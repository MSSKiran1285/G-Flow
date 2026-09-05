"""Registry of known SAP statusbar message patterns (spec §5: "message-pattern registry
auto-extracts created document numbers into buffers"), so a TestCase author references a
pattern by name instead of hand-writing a regex per document type.

`delivery_saved` IS confirmed live: real VL01N wording is "Outbound Delivery 80001138 has
been saved", not just "Delivery N has been saved" as originally guessed — the existing
regex still matches correctly since `re.search` finds "Delivery 80001138 has been saved"
as a substring, but the leading "Outbound " means an exact-match regex would have missed
it, worth keeping in mind for any future pattern here.
`billing_saved` IS confirmed live (billing docs 90001003/90001004/90001005, see
docs/o2c-config-fixes.md): real VF01 wording is "Document N has been saved" — no
"Billing " prefix, unlike the originally-guessed pattern. Fixed to match.
"""

from __future__ import annotations

import re

# name -> (regex, capture group index)
PATTERNS: dict[str, tuple[str, int]] = {
    "order_saved": (r"Standard Order (\d+) has been saved", 1),
    "delivery_saved": (r"Delivery (\d+) has been saved", 1),
    "billing_saved": (r"Document (\d+) has been saved", 1),
}


def extract(pattern_name: str, text: str) -> str | None:
    if pattern_name not in PATTERNS:
        raise ValueError(f"unknown message pattern '{pattern_name}' (known: {', '.join(sorted(PATTERNS))})")
    regex, group = PATTERNS[pattern_name]
    match = re.search(regex, text)
    return match.group(group) if match else None
