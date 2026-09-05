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
}

export interface ModuleSummary {
  id: string;
  name: string;
  tcode: string;
  screen_number: string;
  scanned_at: string;
  attribute_count: number;
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
}

export interface SaveModuleRequest {
  module_name: string;
  tcode: string;
  root_id?: string;
  screen_number?: string;
  attributes: SelectedAttribute[];
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

export type CaptureFrom = "actual_value" | "statusbar";

export interface CaptureSpec {
  buffer: string;
  from: CaptureFrom;
  pattern?: string | null;
}

/** The four actions the UI's Step editor treats as first-class; any other ActionOp
 * name is still accepted by the backend via the free-text "other…" escape hatch. */
export const PRIMARY_ACTIONS = ["SET", "SEND_VKEY", "PRESS", "SELECT"] as const;

export interface StepSpec {
  module?: string | null;
  attribute?: string | null;
  component_id?: string | null;
  action: string;
  binding: BindingSpec;
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
