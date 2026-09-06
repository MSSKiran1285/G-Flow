"""Browse/create/replace/delete TestCases — the "scripts" the builder UI assembles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, sessionmaker

from smt.api.deps import get_session_factory
from smt.api.schemas import (
    DefinedTestCaseOut,
    TestCaseDetail,
    TestCaseSpec,
    TestCaseSummary,
    TestStepOut,
)
from smt.engine.executor import define_test_case_from_spec
from smt.repository.models import TestCase

router = APIRouter(tags=["test-cases"])


def _to_summary(test_case: TestCase) -> TestCaseSummary:
    return TestCaseSummary(
        id=test_case.id, name=test_case.name, description=test_case.description,
        created_at=test_case.created_at, step_count=len(test_case.steps),
    )


def _to_raw_spec(spec: TestCaseSpec) -> dict:
    """Bridges the API's structured JSON contract to the plain YAML-shaped dict
    define_test_case_from_spec already knows how to persist."""
    steps = []
    for step in spec.steps:
        entry: dict = {
            "module": step.module or "",
            "attribute": step.attribute or "",
            "component_id": step.component_id or "",
            "action": step.action,
            "bind": f"{step.binding.type}:{step.binding.value}",
            "row_bind": f"{step.row_binding.type}:{step.row_binding.value}",
            "optional": step.optional,
        }
        if step.capture:
            entry["capture"] = {"buffer": step.capture.buffer, "pattern": step.capture.pattern}
        steps.append(entry)
    return {"name": spec.name, "description": spec.description, "steps": steps}


@router.get("/test-cases", response_model=list[TestCaseSummary])
def list_test_cases(session_factory: sessionmaker[Session] = Depends(get_session_factory)) -> list[TestCaseSummary]:
    with session_factory() as db:
        return [_to_summary(tc) for tc in db.query(TestCase).order_by(TestCase.name).all()]


@router.get("/test-cases/{name}", response_model=TestCaseDetail)
def get_test_case(name: str, session_factory: sessionmaker[Session] = Depends(get_session_factory)) -> TestCaseDetail:
    with session_factory() as db:
        test_case = db.query(TestCase).filter_by(name=name).one_or_none()
        if test_case is None:
            raise HTTPException(status_code=404, detail=f"no TestCase named {name!r}")
        return TestCaseDetail(
            **_to_summary(test_case).model_dump(),
            steps=[
                TestStepOut(
                    id=s.id, sequence_order=s.sequence_order, module_name=s.module_name,
                    attribute_semantic_name=s.attribute_semantic_name, raw_component_id=s.raw_component_id,
                    action_mode=s.action_mode, binding_type=s.binding_type, binding_value=s.binding_value,
                    optional=s.optional, capture_buffer_key=s.capture_buffer_key,
                    capture_from=s.capture_from, capture_pattern=s.capture_pattern,
                    row_binding_type=s.row_binding_type, row_binding_value=s.row_binding_value,
                )
                for s in test_case.steps
            ],
        )


@router.post("/test-cases", response_model=DefinedTestCaseOut)
def upsert_test_case(
    spec: TestCaseSpec, session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> DefinedTestCaseOut:
    defined = define_test_case_from_spec(session_factory, _to_raw_spec(spec))
    return DefinedTestCaseOut(id=defined.id, name=defined.name)


@router.delete("/test-cases/{name}", status_code=204, response_class=Response)
def delete_test_case(name: str, session_factory: sessionmaker[Session] = Depends(get_session_factory)) -> Response:
    with session_factory() as db:
        test_case = db.query(TestCase).filter_by(name=name).one_or_none()
        if test_case is None:
            raise HTTPException(status_code=404, detail=f"no TestCase named {name!r}")
        db.delete(test_case)
        db.commit()
    return Response(status_code=204)
