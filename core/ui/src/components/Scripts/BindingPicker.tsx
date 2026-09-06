import type { BindingType } from "../../types";

const LABELS: Record<BindingType, string> = {
  literal: "Fixed value",
  column: "From test data",
  buffer: "Captured by an earlier step",
};

const PLACEHOLDERS: Record<BindingType, string> = {
  literal: "the literal value to enter",
  column: "data column name",
  buffer: "buffer key name",
};

/** Simplified ValuePicker equivalent: one colored source tag beside one text input
 * whose meaning changes with the binding type — there's no per-module declared param
 * schema here (unlike G-Stride's reference), so this stays deliberately simple.
 * `types` narrows which binding types are offered (e.g. row binding has no "buffer") —
 * generic over T so a narrower spec, like RowBindingSpec, stays type-safe end to end. */
export function BindingPicker<T extends BindingType = BindingType>({
  value,
  onChange,
  types,
}: {
  value: { type: T; value: string };
  onChange: (v: { type: T; value: string }) => void;
  types: readonly T[];
}) {
  return (
    <div>
      <div className="radio-row" role="radiogroup" aria-label="Binding type">
        {types.map((type) => (
          <label key={type}>
            <input
              type="radio"
              name="binding-type"
              checked={value.type === type}
              onChange={() => onChange({ type, value: value.value })}
            />
            <span className={`chip chip-${type}`}>{LABELS[type]}</span>
          </label>
        ))}
      </div>
      <input
        type="text"
        style={{ marginTop: 8, width: "100%" }}
        placeholder={PLACEHOLDERS[value.type]}
        value={value.value}
        onChange={(e) => onChange({ type: value.type, value: e.target.value })}
      />
    </div>
  );
}
