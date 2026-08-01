"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type SegmentInput = {
  id: number;
  name: string;
  length_ft: string;
  pavement_width_ft: string;
  shoulder_width_ft: string;
  shoulder_slope_percent: string;
  side_slope_h_to_v: string;
  thickness_in: string;
};

type SegmentResult = {
  name: string;
  length_ft: number;
  pavement_width_ft: number;
  shoulder_width_ft: number;
  shoulder_slope_percent: number;
  side_slope_h_to_v: number;
  thickness_in: number;
  keyout_run_per_side_ft: number;
  triangle_area_per_side_sq_ft: number;
  equivalent_width_per_side_ft: number;
  equivalent_width_both_sides_ft: number;
  effective_base_width_ft: number;
  cross_section_area_sq_ft: number;
  cubic_feet: number;
  cubic_yards: number;
  base_tons: number;
};

type CalculationResult = {
  segments: SegmentResult[];
  totals: {
    cubic_feet: number;
    cubic_yards: number;
    base_tons: number;
    waste_tons: number;
    order_tons: number;
  };
  assumptions: { tons_per_cubic_yard: number; waste_percent: number; thickness_basis: string; shoulder_count: number; keyout_basis: string; units: string };
  engine_version: string;
};

type RuntimeState = "loading" | "ready" | "error";
type Errors = Record<string, string>;

const DEFAULT_DENSITY = "1.6875";
const DEFAULT_WASTE = "0";
const AUTO_CALC_DELAY_MS = 350;

function blankSegment(id: number): SegmentInput {
  return { id, name: "", length_ft: "", pavement_width_ft: "", shoulder_width_ft: "", shoulder_slope_percent: "", side_slope_h_to_v: "", thickness_in: "" };
}

function positiveNumber(value: string, label: string) {
  if (!value.trim()) return `Enter ${label.toLowerCase()}.`;
  const number = Number(value);
  if (!Number.isFinite(number)) return `${label} must be a finite number.`;
  if (number <= 0) return `${label} must be greater than zero.`;
  return "";
}

function nonnegativeNumber(value: string, label: string) {
  if (!value.trim()) return `Enter ${label.toLowerCase()}.`;
  const number = Number(value);
  if (!Number.isFinite(number)) return `${label} must be a finite number.`;
  if (number < 0) return `${label} must be zero or greater.`;
  return "";
}

function validate(segments: SegmentInput[], density: string, waste: string): Errors {
  const errors: Errors = {};
  const densityError = positiveNumber(density, "Tons per cubic yard");
  if (densityError) errors.density = densityError;
  if (!waste.trim()) {
    errors.waste = "Enter a waste percentage, using 0 when no allowance is needed.";
  } else {
    const wasteNumber = Number(waste);
    if (!Number.isFinite(wasteNumber) || wasteNumber < 0 || wasteNumber > 100) {
      errors.waste = "Waste percentage must be between 0 and 100.";
    }
  }
  segments.forEach((segment) => {
    const fields: Array<[keyof SegmentInput, string]> = [
      ["length_ft", "Length"],
      ["pavement_width_ft", "Pavement width"],
      ["side_slope_h_to_v", "Side slope"],
      ["thickness_in", "Compacted thickness"],
    ];
    fields.forEach(([field, label]) => {
      const message = positiveNumber(String(segment[field]), label);
      if (message) errors[`${segment.id}.${field}`] = message;
    });
    const shoulderWidthError = nonnegativeNumber(segment.shoulder_width_ft, "Shoulder width");
    if (shoulderWidthError) errors[`${segment.id}.shoulder_width_ft`] = shoulderWidthError;
    const shoulderSlopeError = nonnegativeNumber(segment.shoulder_slope_percent, "Shoulder slope");
    if (shoulderSlopeError) errors[`${segment.id}.shoulder_slope_percent`] = shoulderSlopeError;
    if (!shoulderSlopeError && !errors[`${segment.id}.side_slope_h_to_v`]) {
      const shoulderSlope = Number(segment.shoulder_slope_percent) / 100;
      const sideSlope = 1 / Number(segment.side_slope_h_to_v);
      if (sideSlope <= shoulderSlope) {
        errors[`${segment.id}.side_slope_h_to_v`] = "Side slope must be steeper than the shoulder slope so the keyout closes.";
      }
    }
  });
  return errors;
}

function format(value: number) {
  return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function CrushedStoneBaseCalculator() {
  const [segments, setSegments] = useState<SegmentInput[]>([blankSegment(1)]);
  const [density, setDensity] = useState(DEFAULT_DENSITY);
  const [waste, setWaste] = useState(DEFAULT_WASTE);
  const [runtime, setRuntime] = useState<RuntimeState>("loading");
  const [runtimeMessage, setRuntimeMessage] = useState("Loading private calculation engine…");
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [serviceError, setServiceError] = useState("");
  const nextSegmentId = useRef(2);
  const workerRef = useRef<Worker | null>(null);
  const requestId = useRef(1);
  const pending = useRef(new Map<number, { resolve(value: CalculationResult): void; reject(reason: Error): void }>());
  const errors = useMemo(() => validate(segments, density, waste), [segments, density, waste]);
  const isValid = Object.keys(errors).length === 0;

  useEffect(() => {
    const worker = new Worker("/pyodide-worker.js");
    const pendingRequests = pending.current;
    workerRef.current = worker;
    worker.onmessage = (event) => {
      const message = event.data || {};
      if (message.type === "status") setRuntimeMessage(message.message);
      if (message.type === "ready") {
        setRuntime("ready");
        setRuntimeMessage("Private Python engine ready");
      }
      if (message.type === "fatal") {
        setRuntime("error");
        setRuntimeMessage(message.message || "The calculation engine could not start.");
      }
      if (message.type === "response") {
        const request = pending.current.get(message.id);
        if (!request) return;
        pending.current.delete(message.id);
        if (message.ok) request.resolve(message.result);
        else request.reject(new Error(message.error?.message || "Calculation failed."));
      }
    };
    worker.postMessage({ calculator: "crushed_stone_base", operation: "initialize" });
    return () => {
      pendingRequests.forEach(({ reject }) => reject(new Error("Calculator closed.")));
      pendingRequests.clear();
      worker.terminate();
    };
  }, []);

  const calculate = useCallback(() => {
    if (!workerRef.current || runtime !== "ready") return Promise.reject(new Error("Calculation engine is not ready."));
    const id = requestId.current++;
    const payload = {
      segments: segments.map(({ name, length_ft, pavement_width_ft, shoulder_width_ft, shoulder_slope_percent, side_slope_h_to_v, thickness_in }) => ({
        name,
        length_ft: Number(length_ft),
        pavement_width_ft: Number(pavement_width_ft),
        shoulder_width_ft: Number(shoulder_width_ft),
        shoulder_slope_percent: Number(shoulder_slope_percent),
        side_slope_h_to_v: Number(side_slope_h_to_v),
        thickness_in: Number(thickness_in),
      })),
      tons_per_cubic_yard: Number(density),
      waste_percent: Number(waste),
    };
    return new Promise<CalculationResult>((resolve, reject) => {
      pending.current.set(id, { resolve, reject });
      workerRef.current!.postMessage({ id, calculator: "crushed_stone_base", operation: "calculate", payload });
    });
  }, [density, runtime, segments, waste]);

  useEffect(() => {
    if (!isValid || runtime !== "ready") {
      return;
    }
    let active = true;
    const timer = window.setTimeout(() => {
      setServiceError("");
      calculate()
        .then((next) => { if (active) setResult(next); })
        .catch((reason) => {
          if (!active) return;
          setResult(null);
          setServiceError(reason instanceof Error ? reason.message : "Calculation failed.");
        });
    }, AUTO_CALC_DELAY_MS);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [calculate, isValid, runtime]);

  const updateSegment = (id: number, field: keyof SegmentInput, value: string) => {
    setServiceError("");
    setSegments((current) => current.map((segment) => segment.id === id ? { ...segment, [field]: value } : segment));
  };

  const addSegment = () => {
    setServiceError("");
    const id = nextSegmentId.current++;
    setSegments((current) => [...current, blankSegment(id)]);
  };

  const removeSegment = (id: number) => {
    setServiceError("");
    setSegments((current) => current.length === 1 ? [blankSegment(current[0].id)] : current.filter((segment) => segment.id !== id));
  };

  return (
    <main className="stone-shell">
      <header className="stone-header">
        <div>
          <p className="marketing-eyebrow"><span /> Free construction quantity tool</p>
          <h1>Crushed Stone Base<br /><em>Tonnage Calculator</em></h1>
          <p>Build a roadway quantity from pavement width, two matching shoulders, and the outside base keyout triangles. The calculation stays in your browser.</p>
        </div>
        <div className={`stone-runtime ${runtime}`} role="status" aria-live="polite"><i />{runtimeMessage}</div>
      </header>

      <div className="stone-workspace">
        <section className="stone-input-panel" aria-labelledby="quantity-inputs">
          <div className="stone-section-heading"><div><span>01</span><h2 id="quantity-inputs">Roadway segments</h2></div><button type="button" onClick={addSegment}>Add segment +</button></div>
          <div className="stone-segments">
            {segments.map((segment, index) => (
              <fieldset className="stone-segment" key={segment.id}>
                <legend>Segment {String(index + 1).padStart(2, "0")}</legend>
                <label className="stone-field full"><span>Name <small>Optional</small></span><input value={segment.name} onChange={(event) => updateSegment(segment.id, "name", event.target.value)} placeholder={`Roadway segment ${index + 1}`} /></label>
                {([
                  ["length_ft", "Length", "ft"],
                  ["pavement_width_ft", "Pavement width (EOP to EOP)", "ft"],
                  ["shoulder_width_ft", "Shoulder width (each side)", "ft"],
                  ["shoulder_slope_percent", "Shoulder slope (down)", "%"],
                  ["side_slope_h_to_v", "Side slope", "H:1V"],
                  ["thickness_in", "Compacted thickness", "in"],
                ] as const).map(([field, label, unit]) => {
                  const key = `${segment.id}.${field}`;
                  return <label className="stone-field" key={field}><span>{label}</span><div><input type="number" min="0" step="any" inputMode="decimal" value={segment[field]} onChange={(event) => updateSegment(segment.id, field, event.target.value)} aria-invalid={Boolean(errors[key])} aria-describedby={errors[key] ? `${key}-error` : undefined} /><b>{unit}</b></div>{errors[key] && <small className="field-error" id={`${key}-error`}>{errors[key]}</small>}</label>;
                })}
                <button className="stone-remove" type="button" onClick={() => removeSegment(segment.id)} aria-label={`Remove segment ${index + 1}`}>{segments.length === 1 ? "Clear segment" : "Remove segment"}</button>
              </fieldset>
            ))}
          </div>

          <div className="stone-factors">
            <div className="stone-section-heading"><div><span>02</span><h2>Material factors</h2></div></div>
            <label className="stone-field"><span>Tons per cubic yard</span><div><input type="number" min="0" step="any" inputMode="decimal" value={density} onChange={(event) => setDensity(event.target.value)} aria-invalid={Boolean(errors.density)} aria-describedby="density-guidance" /><b>tons/CY</b></div><small id="density-guidance" className={errors.density ? "field-error" : ""}>{errors.density || "Editable project-wide conversion factor."}</small></label>
            <label className="stone-field"><span>Waste / overrun</span><div><input type="number" min="0" max="100" step="any" inputMode="decimal" value={waste} onChange={(event) => setWaste(event.target.value)} aria-invalid={Boolean(errors.waste)} aria-describedby="waste-guidance" /><b>%</b></div><small id="waste-guidance" className={errors.waste ? "field-error" : ""}>{errors.waste || "Applied after all segment quantities are totaled."}</small></label>
          </div>
          <aside className="supplier-notice"><strong>Confirm before ordering</strong><p>Verify the tons-per-cubic-yard conversion and waste allowance with the material supplier and project requirements. The default is an estimating assumption, not a material specification.</p></aside>
        </section>

        <section className="stone-results-panel" aria-labelledby="quantity-results" aria-live="polite">
          <div className="stone-section-heading"><div><span>03</span><h2 id="quantity-results">Quantity summary</h2></div><small>US customary</small></div>
          {serviceError && <div className="stone-error" role="alert">{serviceError}</div>}
          {!isValid || !result ? (
            <div className="stone-empty"><div className="stone-layer-icon"><i /><i /><i /></div><h3>{runtime === "error" ? "Engine unavailable" : "Enter segment geometry"}</h3><p>Enter the full pavement width, one shoulder width used on both sides, the shoulder and side slopes, and compacted thickness.</p></div>
          ) : (
            <>
              <div className="stone-primary-result"><span>Order quantity</span><strong>{format(result.totals.order_tons)}</strong><b>US short tons</b></div>
              <div className="stone-metrics">
                <article><span>Total volume</span><strong>{format(result.totals.cubic_feet)}</strong><small>cubic feet</small></article>
                <article><span>Total volume</span><strong>{format(result.totals.cubic_yards)}</strong><small>cubic yards</small></article>
                <article><span>Base quantity</span><strong>{format(result.totals.base_tons)}</strong><small>tons before waste</small></article>
                <article><span>Waste allowance</span><strong>{format(result.totals.waste_tons)}</strong><small>tons at {format(result.assumptions.waste_percent)}%</small></article>
              </div>
              <div className="stone-breakdown"><h3>Segment breakdown</h3>{result.segments.map((segment, index) => <article key={index}><div><strong>{segment.name || `Segment ${index + 1}`}</strong><span>{format(segment.length_ft)} ft long · {format(segment.pavement_width_ft)} ft pavement · 2 × {format(segment.shoulder_width_ft)} ft shoulders</span><span>Triangle each side: {format(segment.keyout_run_per_side_ft)} ft run · {format(segment.triangle_area_per_side_sq_ft)} SF</span><span className="stone-keyout-value"><b>Equivalent keyout width</b>{format(segment.equivalent_width_per_side_ft)} ft per side · {format(segment.equivalent_width_both_sides_ft)} ft total for both sides</span><span>Effective base width: {format(segment.effective_base_width_ft)} ft</span></div><div><strong>{format(segment.base_tons)} tons</strong><span>{format(segment.cubic_yards)} CY</span></div></article>)}</div>
              <div className="stone-provenance"><span>Engine v{result.engine_version}</span><span>{format(result.assumptions.tons_per_cubic_yard)} tons/CY</span><span>{result.assumptions.thickness_basis}</span></div>
            </>
          )}
        </section>
      </div>

      <section className="stone-method">
        <div><p className="marketing-eyebrow"><span /> Transparent method</p><h2>Every keyout stays visible.</h2><p>The base bottom follows the pavement and shoulder surfaces. Beyond each of the two shoulders, the base tapers to the side slope as an equal triangle.</p></div>
        <ol><li><span>01</span><p><strong>Keyout run per side</strong>Thickness in feet ÷ (1 ÷ side slope H:V − shoulder slope)</p></li><li><span>02</span><p><strong>Equivalent width per side</strong>Triangle area ÷ thickness = keyout run ÷ 2</p></li><li><span>03</span><p><strong>Effective base width</strong>Pavement width + 2 × shoulder width + 2 × equivalent keyout width</p></li><li><span>04</span><p><strong>Order tons</strong>Length × effective width × thickness ÷ 27 × tons/CY × (1 + waste %)</p></li></ol>
      </section>
      <div className="engineering-note"><span>ESTIMATING AID</span><p>The responsible project professional must verify dimensions, material properties, construction allowances, quantities, and purchasing requirements.</p></div>
    </main>
  );
}
