"""Single source of truth for the contract version stamped on every request.

Bump this whenever proto/uiadapter.proto changes in a way that isn't wire-compatible.
Core and agent refuse to talk on mismatch (see spec §2 contract rules).
"""

CONTRACT_VERSION = "0.1.0"
