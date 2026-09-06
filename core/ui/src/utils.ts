import type { TestCaseDetail } from "./types";

/** The distinct "column" bindings (main value + table row) a TestCase's steps declare
 * as needed test data — e.g. VA01_CreateStandardOrder needs order_type, sales_org, ...
 * Used to auto-seed a data grid's columns the moment a script is picked, instead of
 * making the tester retype names they've already declared on the script itself. */
export function dataColumnsOf(detail: TestCaseDetail): string[] {
  const columns: string[] = [];
  const seen = new Set<string>();
  const add = (name: string) => {
    if (name && !seen.has(name)) {
      seen.add(name);
      columns.push(name);
    }
  };
  for (const step of detail.steps) {
    if (step.binding_type === "column") add(step.binding_value);
    if (step.row_binding_type === "column") add(step.row_binding_value);
  }
  return columns;
}

/** One blank row with exactly these columns — what a freshly-seeded data grid starts
 * from so the tester only has to fill in values, not invent column names. */
export function blankRow(columns: string[]): Record<string, string> {
  return Object.fromEntries(columns.map((c) => [c, ""]));
}

export interface BufferFlow {
  /** Buffer keys this TestCase reads (bound via "buffer:") — expected to already
   * exist from an earlier stage in the same chain run. */
  consumes: string[];
  /** Buffer keys this TestCase's steps capture — available to every later stage in
   * the same chain run (and to itself, for a step after the one that captured it). */
  produces: string[];
}

/** What buffers a TestCase reads from and writes to — the chain-level data flow a
 * Chain builder stage can't show from its own data columns alone, since buffer-bound
 * values are deliberately never data columns (nothing to type — see dataColumnsOf). */
export function bufferFlowOf(detail: TestCaseDetail): BufferFlow {
  const consumes: string[] = [];
  const produces: string[] = [];
  const seenConsumes = new Set<string>();
  const seenProduces = new Set<string>();
  for (const step of detail.steps) {
    if (step.binding_type === "buffer" && step.binding_value && !seenConsumes.has(step.binding_value)) {
      seenConsumes.add(step.binding_value);
      consumes.push(step.binding_value);
    }
    if (step.capture_buffer_key && !seenProduces.has(step.capture_buffer_key)) {
      seenProduces.add(step.capture_buffer_key);
      produces.push(step.capture_buffer_key);
    }
  }
  return { consumes, produces };
}
