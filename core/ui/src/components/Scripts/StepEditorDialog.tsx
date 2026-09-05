import { X } from "lucide-react";
import { useState } from "react";
import type { StepSpec } from "../../types";
import { StepEditor } from "./StepEditor";

const BLANK_STEP: StepSpec = {
  module: null,
  attribute: null,
  component_id: null,
  action: "SET",
  binding: { type: "literal", value: "" },
  optional: false,
  capture: null,
};

export function StepEditorDialog({
  initial,
  onClose,
  onSave,
}: {
  initial: StepSpec | null; // null = adding a new step
  onClose: () => void;
  onSave: (step: StepSpec) => void;
}) {
  const [step, setStep] = useState<StepSpec>(initial ?? BLANK_STEP);

  const valid = Boolean(step.component_id || (step.module && step.attribute));

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="step-dialog-title">
        <div className="dialog-header">
          <h3 id="step-dialog-title">{initial ? "Edit step" : "Add step"}</h3>
          <button className="btn" aria-label="Close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <div className="dialog-body">
          <StepEditor step={step} onChange={setStep} />
        </div>
        <div className="dialog-footer">
          <button className="btn" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" disabled={!valid} onClick={() => onSave(step)}>
            Save step
          </button>
        </div>
      </div>
    </div>
  );
}
