import type {
  ChainStage,
  ConnectionsResponse,
  DefinedTestCaseOut,
  ModuleDetail,
  ModuleSummary,
  PollCaptureResponse,
  RunChainResponse,
  RunTestCaseResponse,
  SaveModuleRequest,
  ScanModuleRequest,
  ScanModuleResponse,
  ScanPreviewRequest,
  ScanPreviewResponse,
  StartCaptureRequest,
  StartCaptureResponse,
  StopCaptureResponse,
  TestCaseDetail,
  TestCaseSpec,
  TestCaseSummary,
} from "./types";

class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listConnections: () => request<ConnectionsResponse>("/api/connections"),
  listMessagePatterns: () => request<string[]>("/api/message-patterns"),

  listModules: () => request<ModuleSummary[]>("/api/modules"),
  getModule: (name: string) => request<ModuleDetail>(`/api/modules/${encodeURIComponent(name)}`),
  scanModule: (body: ScanModuleRequest) =>
    request<ScanModuleResponse>("/api/modules/scan", { method: "POST", body: JSON.stringify(body) }),
  scanPreview: (body: ScanPreviewRequest) =>
    request<ScanPreviewResponse>("/api/modules/scan-preview", { method: "POST", body: JSON.stringify(body) }),
  saveModule: (body: SaveModuleRequest) =>
    request<ScanModuleResponse>("/api/modules", { method: "POST", body: JSON.stringify(body) }),
  startCapture: (body: StartCaptureRequest) =>
    request<StartCaptureResponse>("/api/modules/capture/start", { method: "POST", body: JSON.stringify(body) }),
  pollCapture: (captureId: string) =>
    request<PollCaptureResponse>(`/api/modules/capture/${encodeURIComponent(captureId)}/poll`),
  stopCapture: (captureId: string) =>
    request<StopCaptureResponse>(`/api/modules/capture/${encodeURIComponent(captureId)}/stop`, { method: "POST" }),
  highlightCapture: (captureId: string, componentId: string) =>
    request<{ success: boolean }>(`/api/modules/capture/${encodeURIComponent(captureId)}/highlight`, {
      method: "POST",
      body: JSON.stringify({ component_id: componentId }),
    }),

  listTestCases: () => request<TestCaseSummary[]>("/api/test-cases"),
  getTestCase: (name: string) => request<TestCaseDetail>(`/api/test-cases/${encodeURIComponent(name)}`),
  defineTestCase: (spec: TestCaseSpec) =>
    request<DefinedTestCaseOut>("/api/test-cases", { method: "POST", body: JSON.stringify(spec) }),
  deleteTestCase: (name: string) =>
    request<void>(`/api/test-cases/${encodeURIComponent(name)}`, { method: "DELETE" }),

  runTestCase: (testCaseName: string, rows: Record<string, string>[], connectionId?: string) =>
    request<RunTestCaseResponse>("/api/runs/test-case", {
      method: "POST",
      body: JSON.stringify({ test_case_name: testCaseName, rows, connection_id: connectionId ?? null }),
    }),
  runChain: (stages: ChainStage[], connectionId?: string) =>
    request<RunChainResponse>("/api/runs/chain", {
      method: "POST",
      body: JSON.stringify({ stages, connection_id: connectionId ?? null }),
    }),
};

export { ApiError };
