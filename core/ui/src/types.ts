// Hand-written TS mirrors of core/smt/api/schemas.py. Keep in sync by hand — this is a
// small internal tool, not worth an OpenAPI codegen step for this MVP.

export interface ConnectionOut {
  connection_id: string;
  description: string;
  session_ids: string[];
}

export interface ConnectionsResponse {
  reachable: boolean;
  connections: ConnectionOut[];
  error: string | null;
}

/** "input" (a script SETs this) | "output" (this attribute's action is expected to
 * produce a capturable result, e.g. pressing Save then parsing the statusbar). */
export type AttributeDirection = "input" | "output";

export interface ModuleAttributeOut {
  id: string;
  semantic_name: string;
  component_id: string;
  sap_type: string;
  sap_sub_type: string;
  label: string;
  caption: string;
  window_title: string;
  supported_action_modes: string[];
  direction: AttributeDirection;
}

export interface ModuleSummary {
  id: string;
  name: string;
  tcode: string;
  screen_number: string;
  scanned_at: string;
  attribute_count: number;
  folder: string;
}

export interface ModuleDetail extends ModuleSummary {
  root_id: string;
  attributes: ModuleAttributeOut[];
}

export interface ScanModuleRequest {
  module_name: string;
  tcode: string;
  root_id?: string;
  navigate?: boolean;
  prefill?: Record<string, string>;
  vkeys_before_scan?: string[];
  connection_id?: string | null;
}

export interface ScanModuleResponse {
  module_id: string;
  module_name: string;
  attribute_count: number;
}

export interface ScanPreviewRequest {
  tcode: string;
  root_id?: string;
  navigate?: boolean;
  prefill?: Record<string, string>;
  vkeys_before_scan?: string[];
  connection_id?: string | null;
}

export interface ScannedComponentOut {
  component_id: string;
  window: string;
  semantic_name: string;
  sap_type: string;
  sap_sub_type: string;
  label: string;
  caption: string;
  window_title: string;
  supported_action_modes: string[];
}

export interface ScanPreviewResponse {
  tcode: string;
  screen_number: string;
  root_id: string;
  components: ScannedComponentOut[];
}

export interface SelectedAttribute {
  semantic_name: string;
  component_id: string;
  sap_type?: string;
  sap_sub_type?: string;
  label?: string;
  caption?: string;
  window_title?: string;
  supported_action_modes?: string[];
  direction?: AttributeDirection;
}

export interface SaveModuleRequest {
  module_name: string;
  tcode: string;
  root_id?: string;
  screen_number?: string;
  attributes: SelectedAttribute[];
  folder?: string;
}

export interface StartCaptureRequest {
  tcode: string;
  navigate?: boolean;
  prefill?: Record<string, string>;
  vkeys_before_scan?: string[];
  connection_id?: string | null;
}

export interface StartCaptureResponse {
  capture_id: string;
}

export interface PollCaptureResponse {
  components: ScannedComponentOut[];
  active: boolean;
  error?: string | null;
}

export interface StopCaptureResponse {
  components: ScannedComponentOut[];
}

export type BindingType = "literal" | "column" | "buffer";

export interface BindingSpec {
  type: BindingType;
  value: string;
}

/** TABLE_GET_CELL/TABLE_SET_CELL only: which row to target. No "buffer" option — a
 * table row index isn't something an earlier step would plausibly have captured. */
export type RowBindingType = "literal" | "column";

export interface RowBindingSpec {
  type: RowBindingType;
  value: string;
}

export type CaptureFrom = "actual_value" | "statusbar";

export interface CaptureSpec {
  buffer: string;
  from: CaptureFrom;
  pattern?: string | null;
}

/** The four actions the UI's Step editor treats as first-class; any other ActionOp
 * name is still accepted by the backend via the free-text "other…" escape hatch. */
export const PRIMARY_ACTIONS = ["SET", "SEND_VKEY", "PRESS", "SELECT"] as const;

/** Actions that target one row of a table instead of a fixed component — the step's
 * "attribute" must be a captured table-cell (an id ending "...[col,row]"); the row to
 * actually hit is supplied separately per data row via row_binding. */
export const TABLE_ACTIONS = ["TABLE_GET_CELL", "TABLE_SET_CELL"] as const;

/** Actions whose ActionParams actually carry binding.value through to the agent (see
 * executor._build_params) — every other action (PRESS, TABLE_GET_CELL, READ, ...)
 * silently ignores it, so the UI shouldn't imply an input is in play for those. */
export const BINDING_CONSUMING_ACTIONS = ["SET", "SEND_VKEY", "SELECT", "TABLE_SET_CELL"] as const;

export interface StepSpec {
  module?: string | null;
  attribute?: string | null;
  component_id?: string | null;
  action: string;
  binding: BindingSpec;
  row_binding: RowBindingSpec;
  optional: boolean;
  capture?: CaptureSpec | null;
}

export interface TestCaseSpec {
  name: string;
  description: string;
  steps: StepSpec[];
}

export interface TestStepOut {
  id: string;
  sequence_order: number;
  module_name: string;
  attribute_semantic_name: string;
  raw_component_id: string;
  action_mode: string;
  binding_type: BindingType;
  binding_value: string;
  optional: boolean;
  capture_buffer_key: string;
  capture_from: CaptureFrom;
  capture_pattern: string;
  row_binding_type: RowBindingType;
  row_binding_value: string;
}

export interface TestCaseSummary {
  id: string;
  name: string;
  description: string;
  created_at: string;
  step_count: number;
}

export interface TestCaseDetail extends TestCaseSummary {
  steps: TestStepOut[];
}

export interface DefinedTestCaseOut {
  id: string;
  name: string;
}

export interface RowResultOut {
  row_index: number;
  success: boolean;
  failed_at_step: number | null;
  message: string;
  values: Record<string, string>;
  test_case_name: string;
  buffer: Record<string, string>;
}

export interface RunTestCaseRequest {
  test_case_name: string;
  rows: Record<string, string>[];
  connection_id?: string | null;
}

export interface RunTestCaseResponse {
  results: RowResultOut[];
}

export interface ChainStage {
  test_case_name: string;
  rows: Record<string, string>[];
}

export interface RunChainRequest {
  stages: ChainStage[];
  connection_id?: string | null;
}

export interface RunChainResponse {
  results: RowResultOut[][];
}
