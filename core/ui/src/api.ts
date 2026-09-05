import type {
  ChainStage,
  ConnectionsResponse,
  DefinedTestCaseOut,
  ModuleDetail,
  ModuleSummary,
  RunChainResponse,
  RunTestCaseResponse,
  ScanModuleRequest,
  ScanModuleResponse,
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
