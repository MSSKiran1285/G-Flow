"""Small reference-data endpoints the UI needs for dropdowns."""

from __future__ import annotations

from fastapi import APIRouter

from smt.engine import message_patterns

router = APIRouter(tags=["meta"])


@router.get("/message-patterns", response_model=list[str])
def list_message_patterns() -> list[str]:
    return sorted(message_patterns.PATTERNS)
