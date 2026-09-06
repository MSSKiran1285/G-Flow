import { useEffect, useState } from "react";
import { api } from "../../api";
import {
  PRIMARY_ACTIONS,
  TABLE_ACTIONS,
  type ModuleAttributeOut,
  type ModuleSummary,
  type StepSpec,
} from "../../types";
import { BindingPicker } from "./BindingPicker";
import { CaptureFields } from "./CaptureFields";

const OTHER_ACTIONS = [
  "READ", "VERIFY", "MENU_SELECT", "GRID_GET_CELL", "GRID_SET_CELL", "GRID_SELECT_ROWS",
  "GRID_DOUBLE_CLICK_CELL", "TABLE_GET_CELL", "TABLE_SET_CELL", "SET_FOCUS", "WINDOW_CLOSE",
];

export function StepEditor({ step, onChange }: { step: StepSpec; onChange: (s: StepSpec) => void }) {
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [attributes, setAttributes] = useState<ModuleAttributeOut[]>([]);
  const [useRawId, setUseRawId] = useState(Boolean(step.component_id));

  useEffect(() => {
    api.listModules().then(setModules).catch(() => setModules([]));
  }, []);

  useEffect(() => {
    if (!step.module) {
      setAttributes([]);
      return;
    }
    api.getModule(step.module).then((m) => setAttributes(m.attributes)).catch(() => setAttributes([]));
  }, [step.module]);

  return (
    <div>
      <div className="field">
        <label>Target</label>
        <div className="radio-row">
          <label>
            <input type="radio" checked={!useRawId} onChange={() => setUseRawId(false)} /> Module + attribute
          </label>
          <label>
            <input type="radio" checked={useRawId} onChange={() => setUseRawId(true)} /> Raw component id
          </label>
        </div>
      </div>

      {useRawId ? (
        <div className="field">
          <label htmlFor="raw-component-id">Component id</label>
          <input
            id="raw-component-id"
            type="text"
            value={step.component_id ?? ""}
            onChange={(e) => onChange({ ...step, component_id: e.target.value, module: null, attribute: null })}
            placeholder="e.g. wnd[1]/usr/btnSPOP-VAROPTION1 — for conditional elements like popups"
          />
        </div>
      ) : (
        <>
          <div className="field">
            <label htmlFor="step-module">Module</label>
            <select
              id="step-module"
              value={step.module ?? ""}
              onChange={(e) => onChange({ ...step, module: e.target.value || null, attribute: null, component_id: null })}
            >
              <option value="" disabled>
                choose a module…
              </option>
              {modules.map((m) => (
                <option key={m.id} value={m.name}>
                  {m.name} ({m.tcode})
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="step-attribute">Attribute</label>
            <select
              id="step-attribute"
              value={step.attribute ?? ""}
              disabled={!step.module}
              onChange={(e) => onChange({ ...step, attribute: e.target.value || null })}
            >
              <option value="" disabled>
                choose an attribute…
              </option>
              {attributes.map((a) => (
                <option key={a.id} value={a.semantic_name}>
                  {a.semantic_name}
                  {a.caption ? ` — ${a.caption}` : a.label ? ` — ${a.label}` : ""}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      <div className="field">
        <label htmlFor="step-action">Action</label>
        <select id="step-action" value={step.action} onChange={(e) => onChange({ ...step, action: e.target.value })}>
          {PRIMARY_ACTIONS.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
          <optgroup label="Other">
            {OTHER_ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </optgroup>
        </select>
      </div>

      <div className="field">
        <label>Binding</label>
        <BindingPicker
          value={step.binding}
          onChange={(binding) => onChange({ ...step, binding })}
          types={["literal", "column", "buffer"]}
        />
      </div>

      {(TABLE_ACTIONS as readonly string[]).includes(step.action) && (
        <div className="field">
          <label>Table row</label>
          <p className="field-hint">
            The attribute above must be a captured table cell (its id ends "…[col,row]") —
            the table and column come from that capture; this picks which row to actually
            hit, so the same step can drive a different line item per data row.
          </p>
          <BindingPicker
            value={step.row_binding}
            onChange={(row_binding) => onChange({ ...step, row_binding })}
            types={["literal", "column"]}
          />
        </div>
      )}

      <div className="field">
        <label>
          <input type="checkbox" checked={step.optional} onChange={(e) => onChange({ ...step, optional: e.target.checked })} />{" "}
          Optional — skip rather than fail if this component isn't found
        </label>
      </div>

      <CaptureFields value={step.capture ?? null} onChange={(capture) => onChange({ ...step, capture })} />
    </div>
  );
}
