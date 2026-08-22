"""Registry of known SAP statusbar message patterns (spec §5: "message-pattern registry
auto-extracts created document numbers into buffers"), so a TestCase author references a
pattern by name instead of hand-writing a regex per document type.

Patterns for delivery/billing are carried over from the order-save wording confirmed live
(spec §5's convention: "<Document type> <number> has been saved") but haven't themselves
been confirmed against a real VL01N/VF01 save yet — treat them as VERIFY-ON-TARGET until
a live chain run confirms or corrects them, same discipline as the agent's own COM calls.
"""

from __future__ import annotations

import re

# name -> (regex, capture group index)
PATTERNS: dict[str, tuple[str, int]] = {
    "order_saved": (r"Standard Order (\d+) has been saved", 1),
    "delivery_saved": (r"Delivery (\d+) has been saved", 1),  # VERIFY-ON-TARGET
    "billing_saved": (r"Billing document (\d+) has been saved", 1),  # VERIFY-ON-TARGET
}


def extract(pattern_name: str, text: str) -> str | None:
    if pattern_name not in PATTERNS:
        raise ValueError(f"unknown message pattern '{pattern_name}' (known: {', '.join(sorted(PATTERNS))})")
    regex, group = PATTERNS[pattern_name]
    match = re.search(regex, text)
    return match.group(group) if match else None
