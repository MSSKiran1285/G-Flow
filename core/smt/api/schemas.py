"""Pydantic request/response models for the script-builder HTTP API. Field shapes
mirror smt.repository.models and smt.engine.executor.RowResult directly — this module
has no logic of its own beyond validation, all real behavior stays in executor.py/
scanning.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from smt.adapter.generated import uiadapter_pb2 as pb


# --- connections ---

class ConnectionOut(BaseModel):
    connection_id: str
    description: str
    session_ids: list[str]


class ConnectionsResponse(BaseModel):
    reachable: bool
    connections: list[ConnectionOut] = []
    error: str | None = None


# --- modules ---

class ModuleAttributeOut(BaseModel):
    id: str
    semantic_name: str
    component_id: str
    sap_type: str
    sap_sub_type: str
    label: str
    caption: str = ""
    supported_action_modes: list[str]


class ModuleSummary(BaseModel):
    id: str
    name: str
    tcode: str
    screen_number: str
    scanned_at: datetime
    attribute_count: int


class ModuleDetail(ModuleSummary):
    root_id: str
    attributes: list[ModuleAttributeOut]


class ScanModuleRequest(BaseModel):
    module_name: str
    tcode: str
    root_id: str = "wnd[0]"
    navigate: bool = True
    prefill: dict[str, str] = {}
    vkeys_before_scan: list[str] = []
    connection_id: str | None = None


class ScanModuleResponse(BaseModel):
    module_id: str
    module_name: str
    attribute_count: int


class ScanPreviewRequest(BaseModel):
    tcode: str
    root_id: str = "wnd[0]"
    navigate: bool = True
    prefill: dict[str, str] = {}
    vkeys_before_scan: list[str] = []
    connection_id: str | None = None


class ScannedComponentOut(BaseModel):
    component_id: str
    window: str
    semantic_name: str
    sap_type: str
    sap_sub_type: str
    label: str
    caption: str = ""
    supported_action_modes: list[str]


class ScanPreviewResponse(BaseModel):
    tcode: str
    screen_number: str
    root_id: str
    components: list[ScannedComponentOut]


class SelectedAttribute(BaseModel):
    semantic_name: str
    component_id: str
    sap_type: str = ""
    sap_sub_type: str = ""
    label: str = ""
    caption: str = ""
    supported_action_modes: list[str] = []


class SaveModuleRequest(BaseModel):
    module_name: str
    tcode: str
    root_id: str = "wnd[0]"
    screen_number: str = ""
    attributes: list[SelectedAttribute]


# --- live element picker (Ctrl+Click capture) ---

class StartCaptureRequest(BaseModel):
    tcode: str
    navigate: bool = True
    prefill: dict[str, str] = {}
    vkeys_before_scan: list[str] = []
    connection_id: str | None = None


class StartCaptureResponse(BaseModel):
    capture_id: str


class PollCaptureResponse(BaseModel):
    components: list[ScannedComponentOut]
    active: bool
    error: str | None = None


class StopCaptureResponse(BaseModel):
    components: list[ScannedComponentOut]


# --- test cases ---

def _is_known_action(name: str) -> bool:
    # Same check core.smt.cli.main._build_action_request already uses: ActionOp values
    # are plain int constants on the module itself (protobuf enum codegen), not members
    # of a pb.ActionOp class.
    return hasattr(pb, name) and isinstance(getattr(pb, name), int)


class BindingSpec(BaseModel):
    type: Literal["literal", "column", "buffer"] = "literal"
    value: str = ""


class CaptureSpec(BaseModel):
    buffer: str
    from_: Literal["actual_value", "statusbar"] = Field("actual_value", alias="from")
    pattern: str | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _pattern_required_for_statusbar(self) -> "CaptureSpec":
        if self.from_ == "statusbar" and not self.pattern:
            raise ValueError("capture.pattern is required when capture.from is 'statusbar'")
        return self


class StepSpec(BaseModel):
    module: str | None = None
    attribute: str | None = None
    component_id: str | None = None
    action: str
    binding: BindingSpec = BindingSpec()
    optional: bool = False
    capture: CaptureSpec | None = None

    @model_validator(mode="after")
    def _validate(self) -> "StepSpec":
        if not self.component_id and not (self.module and self.attribute):
            raise ValueError("a step needs either component_id, or both module and attribute")
        if not _is_known_action(self.action):
            raise ValueError(f"unknown action {self.action!r} — not a known ActionOp")
        return self


class TestCaseSpec(BaseModel):
    name: str
    description: str = ""
    steps: list[StepSpec] = []


class TestStepOut(BaseModel):
    id: str
    sequence_order: int
    module_name: str
    attribute_semantic_name: str
    raw_component_id: str
    action_mode: str
    binding_type: str
    binding_value: str
    optional: bool
    capture_buffer_key: str
    capture_from: str
    capture_pattern: str


class TestCaseSummary(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    step_count: int


class TestCaseDetail(TestCaseSummary):
    steps: list[TestStepOut]


class DefinedTestCaseOut(BaseModel):
    id: str
    name: str


# --- runs ---

class RowResultOut(BaseModel):
    row_index: int
    success: bool
    failed_at_step: int | None
    message: str
    values: dict[str, str]
    test_case_name: str
    buffer: dict[str, str]


class RunTestCaseRequest(BaseModel):
    test_case_name: str
    rows: list[dict[str, str]]
    connection_id: str | None = None


class RunTestCaseResponse(BaseModel):
    results: list[RowResultOut]


class ChainStage(BaseModel):
    test_case_name: str
    rows: list[dict[str, str]]


class RunChainRequest(BaseModel):
    stages: list[ChainStage]
    connection_id: str | None = None


class RunChainResponse(BaseModel):
    results: list[list[RowResultOut]]
