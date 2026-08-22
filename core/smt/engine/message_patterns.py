"""Registry of known SAP statusbar message patterns (spec §5: "message-pattern registry
auto-extracts created document numbers into buffers"), so a TestCase author references a
pattern by name instead of hand-writing a regex per document type.

`billing_saved` is carried over from the order-save wording convention but hasn't itself
been confirmed against a real VF01 save yet (billing remains blocked on a live FI/CO
account-determination gap — see docs/assumptions.md) — treat it as VERIFY-ON-TARGET.
`delivery_saved` IS confirmed live: real VL01N wording is "Outbound Delivery 80001138 has
been saved", not just "Delivery N has been saved" as originally guessed — the existing
regex still matches correctly since `re.search` finds "Delivery 80001138 has been saved"
as a substring, but the leading "Outbound " means an exact-match regex would have missed
it, worth keeping in mind for any future pattern here.
"""

from __future__ import annotations

import re

# name -> (regex, capture group index)
PATTERNS: dict[str, tuple[str, int]] = {
    "order_saved": (r"Standard Order (\d+) has been saved", 1),
    "delivery_saved": (r"Delivery (\d+) has been saved", 1),
    "billing_saved": (r"Billing document (\d+) has been saved", 1),  # VERIFY-ON-TARGET
}


def extract(pattern_name: str, text: str) -> str | None:
    if pattern_name not in PATTERNS:
        raise ValueError(f"unknown message pattern '{pattern_name}' (known: {', '.join(sorted(PATTERNS))})")
    regex, group = PATTERNS[pattern_name]
    match = re.search(regex, text)
    return match.group(group) if match else None
