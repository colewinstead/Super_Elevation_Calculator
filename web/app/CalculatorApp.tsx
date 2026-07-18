"use client";

/* Browser worker responses mirror dynamically typed Python dictionaries. */
/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-html-link-for-pages */

import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

type Dict = Record<string, any>;
type RuntimeState = "loading" | "ready" | "error";
type WritableFile = { write(data: Blob): Promise<void>; close(): Promise<void> };
type SaveFileHandle = { createWritable(): Promise<WritableFile> };
type SaveTarget = SaveFileHandle | "download";
const AUTO_CALC_DELAY_MS = 450;

const EXPORT_DETAILS: Record<string, { suffix: string; description: string }> = {
  export_pdf: { suffix: "-report", description: "PDF calculation report" },
  export_ord_csv: { suffix: "-ord", description: "OpenRoads superelevation CSV" },
  export_overlay_dxf: { suffix: "-overlay", description: "LandXML overlay DXF" },
};

const INITIAL_INPUTS: Dict = {
  project_name: "",
  route_name: "",
  alignment_name: "",
  curve_name: "",
  curve_direction: "left",
  pc: "",
  pt: "",
  speed: "",
  radius: "",
  facility: "centerline",
  area: "rural",
  lane_width: "12",
  lanes_rotated: "2",
  e_manual: "",
  friction: "",
  rel_grad: "",
  normal_crown: "0.02",
  Lr_manual: "",
  Lt_manual: "",
  station_equations: "",
  alignment_station_range: "",
  curve_notes: "",
  station_format: true,
};

function download(name: string, value: string | Uint8Array, type: string) {
  const blob = new Blob([value as BlobPart], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function chooseSaveTarget(name: string, type: string, extension: string, description: string): Promise<SaveTarget | null> {
  const picker = (window as Window & {
    showSaveFilePicker?: (options: Dict) => Promise<SaveFileHandle>;
  }).showSaveFilePicker;
  if (!picker) return "download";
  try {
    return await picker.call(window, {
      suggestedName: name,
      types: [{ description, accept: { [type]: [`.${extension}`] } }],
    });
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === "AbortError") return null;
    if (reason instanceof DOMException && ["SecurityError", "NotAllowedError"].includes(reason.name)) return "download";
    throw reason;
  }
}

async function saveExport(target: SaveTarget, name: string, value: string | Uint8Array, type: string) {
  if (target === "download") {
    download(name, value, type);
    return "downloaded";
  }
  const writable = await target.createWritable();
  await writable.write(new Blob([value as BlobPart], { type }));
  await writable.close();
  return "saved";
}

function cleanName(value: string, fallback: string) {
  const cleaned = value.trim().replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "");
  return cleaned || fallback;
}

export default function CalculatorApp() {
  const workerRef = useRef<Worker | null>(null);
  const pendingRef = useRef(new Map<number, { resolve: (value: any) => void; reject: (reason: Error) => void }>());
  const requestId = useRef(0);
  const calculationSequence = useRef(0);
  const [runtime, setRuntime] = useState<RuntimeState>("loading");
  const [runtimeMessage, setRuntimeMessage] = useState("Starting private browser workspace…");
  const [progress, setProgress] = useState(4);
  const [manifest, setManifest] = useState<Dict | null>(null);
  const [inputs, setInputs] = useState<Dict>(INITIAL_INPUTS);
  const [calculation, setCalculation] = useState<Dict | null>(null);
  const [curves, setCurves] = useState<Dict[]>([]);
  const [selectedCurve, setSelectedCurve] = useState(-1);
  const [landxml, setLandxml] = useState<Dict | null>(null);
  const [landxmlPreset, setLandxmlPreset] = useState(0);
  const [calculationRequest, setCalculationRequest] = useState(0);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [lookupStation, setLookupStation] = useState("");
  const [lookupSlope, setLookupSlope] = useState("");
  const [lookupResult, setLookupResult] = useState<Dict | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");
  const [dirty, setDirty] = useState(false);
  const [sourceCrs, setSourceCrs] = useState("");
  const [targetCrs, setTargetCrs] = useState("");

  const startWorker = useCallback(() => {
    workerRef.current?.terminate();
    pendingRef.current.forEach(({ reject }) => reject(new Error("Browser workspace restarted.")));
    pendingRef.current.clear();
    setRuntime("loading");
    setProgress(4);
    const worker = new Worker("/pyodide-worker.js");
    workerRef.current = worker;
    worker.onmessage = (event) => {
      const message = event.data || {};
      if (message.type === "status") {
        setRuntimeMessage(message.message);
        setProgress(message.progress || 0);
      } else if (message.type === "ready") {
        setRuntime("ready");
        setManifest(message.manifest);
        const systems = message.manifest?.options?.coordinate_systems || [];
        setSourceCrs((value) => value || systems[0] || "");
        setTargetCrs((value) => value || systems[0] || "");
      } else if (message.type === "fatal") {
        setRuntime("error");
        setRuntimeMessage(message.message);
      } else if (message.type === "response") {
        const pending = pendingRef.current.get(message.id);
        if (!pending) return;
        pendingRef.current.delete(message.id);
        if (message.ok) {
          pending.resolve(message.result);
        } else {
          pending.reject(new Error(message.error?.message || "Operation failed."));
        }
      }
    };
    worker.postMessage({ operation: "initialize" });
  }, []);

  useEffect(() => {
    startWorker();
    return () => workerRef.current?.terminate();
  }, [startWorker]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const call = useCallback((operation: string, payload: Dict = {}) => {
    if (!workerRef.current || runtime !== "ready") return Promise.reject(new Error("The browser workspace is not ready yet."));
    const id = ++requestId.current;
    return new Promise<any>((resolve, reject) => {
      pendingRef.current.set(id, { resolve, reject });
      workerRef.current!.postMessage({ id, operation, payload });
    });
  }, [runtime]);

  const update = (key: string, value: any) => {
    setInputs((current) => ({ ...current, [key]: value }));
    setDirty(true);
  };

  const meta = useMemo(() => ({
    project_name: inputs.project_name?.trim() || "Unnamed project",
    route_name: inputs.route_name?.trim() || "Unnamed route",
    alignment_name: inputs.alignment_name?.trim() || "Unnamed alignment",
    curve_name: inputs.curve_name?.trim() || "Unnamed curve",
    curve_direction: inputs.curve_direction || "left",
  }), [inputs]);

  const run = async (label: string, task: () => Promise<any>) => {
    setError("");
    setNotice("");
    setBusy(label);
    try {
      return await task();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      return null;
    } finally {
      setBusy("");
    }
  };

  const calculate = async () => {
    const sequence = ++calculationSequence.current;
    const result = await run("Calculating", () => call("calculate", { inputs }));
    if (result && sequence === calculationSequence.current) {
      setCalculation(result);
      setLookupResult(null);
      setDirty(true);
    }
  };

  const calculationKey = useMemo(() => JSON.stringify({
    curve_direction: inputs.curve_direction,
    pc: inputs.pc,
    pt: inputs.pt,
    speed: inputs.speed,
    radius: inputs.radius,
    facility: inputs.facility,
    area: inputs.area,
    lane_width: inputs.lane_width,
    lanes_rotated: inputs.lanes_rotated,
    e_manual: inputs.e_manual,
    friction: inputs.friction,
    rel_grad: inputs.rel_grad,
    normal_crown: inputs.normal_crown,
    Lr_manual: inputs.Lr_manual,
    Lt_manual: inputs.Lt_manual,
    station_equations: inputs.station_equations,
    alignment_station_range: inputs.alignment_station_range,
    station_format: inputs.station_format,
  }), [inputs]);

  useEffect(() => {
    if (runtime !== "ready") return;
    const readyToCalculate = String(inputs.pc ?? "").trim()
      && String(inputs.speed ?? "").trim()
      && String(inputs.radius ?? "").trim();
    const sequence = ++calculationSequence.current;
    if (!readyToCalculate) {
      setCalculation(null);
      setLookupResult(null);
      setBusy("");
      return;
    }
    const timer = window.setTimeout(async () => {
      setError("");
      setNotice("");
      setBusy("Calculating");
      try {
        const result = await call("calculate", { inputs });
        if (sequence !== calculationSequence.current) return;
        setCalculation(result);
        setLookupResult(null);
      } catch (reason) {
        if (sequence === calculationSequence.current) {
          setError(reason instanceof Error ? reason.message : String(reason));
        }
      } finally {
        if (sequence === calculationSequence.current) setBusy("");
      }
    }, AUTO_CALC_DELAY_MS);
    return () => window.clearTimeout(timer);
    // calculationKey intentionally captures only values that affect calculation output.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calculationKey, calculationRequest, runtime, call]);

  const applyPreset = (index: number, parsed = landxml) => {
    const preset = parsed?.curve_presets?.[index];
    if (!preset) return;
    setLandxmlPreset(index);
    setInputs((current) => ({
      ...current,
      alignment_name: preset.alignment_name || "",
      curve_name: preset.curve_name || "",
      curve_direction: preset.curve_direction || "left",
      pc: preset.pc_station_label || "",
      pt: preset.pt_station_label || "",
      radius: String(preset.radius_ft ?? ""),
      station_equations: preset.station_equations || [],
      alignment_station_range: preset.alignment_station_range || null,
      route_name: current.route_name || parsed.summary?.alignment_name || "",
    }));
    setCalculation(null);
    setCalculationRequest((request) => request + 1);
    setDirty(true);
  };

  const selectLandxml = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (landxml && !window.confirm(`Replace embedded ${landxml.source.filename} with ${file.name}? The saved project changes only when you save.`)) return;
    const content = await file.text();
    const result = await run("Reading LandXML", () => call("parse_landxml", { content, filename: file.name }));
    if (result) {
      setLandxml(result);
      setNotice(`${file.name} is embedded in working project state. Save the project to persist it.`);
      applyPreset(0, result);
    }
  };

  const curveObject = () => calculation ? { results: calculation.results, meta, notes: inputs.curve_notes || "" } : null;

  const addCurve = () => {
    const curve = curveObject();
    if (!curve) return setError("Run a calculation before adding a curve.");
    setCurves((current) => [...current, curve]);
    setSelectedCurve(curves.length);
    setDirty(true);
  };

  const updateCurve = () => {
    const curve = curveObject();
    if (!curve || selectedCurve < 0) return setError("Select a curve and run a calculation before updating it.");
    setCurves((current) => current.map((item, index) => index === selectedCurve ? curve : item));
    setDirty(true);
  };

  const loadCurve = async (index: number) => {
    setSelectedCurve(index);
    const curve = curves[index];
    if (!curve?.results) return;
    const values = curve.results.inputs || {};
    setInputs((current) => ({
      ...current,
      ...curve.meta,
      pc: values.pc ?? "", pt: values.pt ?? "", speed: String(values.speed_mph ?? ""), radius: String(values.radius_ft ?? ""),
      facility: values.facility ?? "centerline", area: values.area_type ?? "rural", lane_width: String(values.lane_width_ft ?? "12"),
      lanes_rotated: String(values.lanes_rotated ?? "2"), e_manual: values.e_manual == null ? "" : String(values.e_manual),
      friction: values.friction_input ?? "", rel_grad: values.relative_gradient_input ?? "", normal_crown: String(values.normal_crown ?? "0.02"),
      Lr_manual: values.Lr_manual == null ? "" : String(values.Lr_manual), Lt_manual: values.Lt_manual == null ? "" : String(values.Lt_manual),
      curve_notes: curve.notes || "",
    }));
    const presented = await run("Opening curve", () => call("present_results", { results: curve.results, direction: curve.meta?.curve_direction || "left", station_format: inputs.station_format }));
    if (presented) setCalculation(presented);
  };

  const addAll = async () => {
    if (!landxml) return setError("Select LandXML first.");
    const result = await run("Building all curves", () => call("build_all_landxml_curves", {
      content: landxml.source.content,
      filename: landxml.source.filename,
      shared_inputs: inputs,
    }));
    if (result) {
      setCurves(result);
      setSelectedCurve(result.length ? 0 : -1);
      if (result.length) await loadCurveFrom(result[0]);
      setDirty(true);
      setNotice(`Built ${result.length} LandXML curves for combined export.`);
    }
  };

  const loadCurveFrom = async (curve: Dict) => {
    if (!curve?.results) return;
    const presented = await call("present_results", { results: curve.results, direction: curve.meta?.curve_direction || "left", station_format: inputs.station_format });
    setCalculation(presented);
  };

  const exportCurves = () => curves.length ? curves : (curveObject() ? [curveObject()!] : []);

  const saveProject = async () => {
    const project = {
      version: 4,
      application_version: manifest?.application_version,
      calculation_engine_version: manifest?.calculation_engine_version,
      criteria: manifest?.criteria,
      vars: inputs,
      curves,
      last_results: calculation?.results || null,
      last_meta: meta,
      landxml_source: landxml?.source || null,
    };
    const content = await run("Preparing project", () => call("project_save", { project }));
    if (content) {
      download(`${cleanName(inputs.project_name, "superelevation-project")}.json`, content, "application/json");
      setDirty(false);
      setNotice("Project downloaded with calculation provenance and embedded LandXML.");
    }
  };

  const loadProject = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const content = await file.text();
    const loaded = await run("Opening project", () => call("project_load", { content }));
    if (!loaded) return;
    setInputs({ ...INITIAL_INPUTS, ...(loaded.project.vars || {}) });
    setCurves(loaded.project.curves || []);
    if (loaded.project.last_results) {
      const presented = await run("Restoring results", () => call("present_results", { results: loaded.project.last_results, direction: loaded.project.last_meta?.curve_direction || "left", station_format: loaded.project.vars?.station_format !== false }));
      if (!presented) return;
      setCalculation(presented);
    } else {
      setCalculation(null);
    }
    setLandxml(loaded.landxml || null);
    setSelectedCurve(-1);
    setDirty(false);
    setNotice(`Opened ${file.name}${loaded.landxml ? " with embedded LandXML" : ""}.`);
  };

  const newProject = () => {
    if (dirty && !window.confirm("Discard the unsaved working project?")) return;
    setInputs(INITIAL_INPUTS); setCalculation(null); setCurves([]); setLandxml(null); setSelectedCurve(-1);
    setLookupResult(null); setError(""); setNotice(""); setDirty(false);
  };

  const performLookup = async () => {
    if (!calculation?.results) return setError("Run a calculation first.");
    const result = await run("Looking up", () => call("lookup", {
      results: calculation.results, direction: inputs.curve_direction, station: lookupStation, slope: lookupSlope,
    }));
    if (result) setLookupResult(result);
  };

  const performExport = async (operation: string, extension: string, mime: string) => {
    const available = exportCurves();
    if (!available.length) return setError("Run a calculation before exporting.");
    const payload: Dict = { curves: available };
    if (operation === "export_overlay_dxf") {
      if (!landxml) return setError("Select LandXML before exporting an overlay DXF.");
      payload.landxml_source = landxml.source;
      payload.coordinate_config = { source_coordinate_system: sourceCrs, target_coordinate_system: targetCrs };
    }
    const details = EXPORT_DETAILS[operation] || { suffix: "", description: `${extension.toUpperCase()} export` };
    const filename = `${cleanName(inputs.project_name, "superelevation")}${details.suffix}.${extension}`;
    let target: SaveTarget | null;
    try {
      target = await chooseSaveTarget(filename, mime, extension, details.description);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      return;
    }
    if (!target) return;
    const outcome = await run("Generating export", async () => {
      const result = await call(operation, payload);
      const disposition = await saveExport(target, filename, result.content, mime);
      return { ...result, disposition };
    });
    if (!outcome) return;
    const action = outcome.disposition === "saved" ? "Saved" : "Downloaded";
    setNotice(outcome.warnings?.length ? `${action} with ${outcome.warnings.length} warning(s): ${outcome.warnings[0]}` : `${action} ${extension.toUpperCase()} export.`);
  };

  const inputValue = (key: string) => {
    const value = inputs[key];
    if (key === "station_equations" && Array.isArray(value)) {
      return value.map((equation: Dict) => `${equation.staBack}=${equation.staAhead}`).join("; ");
    }
    if (Array.isArray(value)) return value.join(",");
    return value ?? "";
  };

  const input = (key: string, label: string, required = false, type = "text") => (
    <label className="field"><span>{label}{required && <b> *</b>}</span><input type={type} value={inputValue(key)} onChange={(e) => update(key, e.target.value)} /></label>
  );

  const result = calculation?.results;
  const lanes = calculation?.lanes || {};

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark">SE</div>
        <div><p className="eyebrow">Civil design workspace</p><h1>Superelevation Calculator</h1></div>
        <a className="workspace-home" href="/">Product home</a>
        <div className={`runtime ${runtime}`}><span></span>{runtime === "ready" ? "Private browser engine ready" : runtimeMessage}</div>
      </header>

      {runtime !== "ready" && <section className="runtime-gate" role="status">
        <div className="gate-card"><p className="eyebrow">Browser-only processing</p><h2>{runtime === "error" ? "The workspace could not start" : runtimeMessage}</h2>
          <div className="progress"><i style={{ width: `${progress}%` }} /></div>
          <p>{runtime === "error" ? "Check your connection and retry. No project information was transmitted." : "Python and the engineering libraries are loading into this tab. Your project files never upload to a server."}</p>
          {runtime === "error" && <button className="primary" onClick={startWorker}>Retry</button>}
        </div>
      </section>}

      <div className="privacy-strip"><strong>Local processing</strong><span>LandXML, calculations, and exports remain on this device.</span><span className="version">App {manifest?.application_version || "…"} · Engine {manifest?.calculation_engine_version || "…"}</span></div>

      {(error || notice) && <div className={`toast ${error ? "error" : "notice"}`} role="alert"><strong>{error ? "Action needed" : "Complete"}</strong><span>{error || notice}</span><button aria-label="Dismiss message" onClick={() => { setError(""); setNotice(""); }}>×</button></div>}

      <div className="workspace">
        <aside className="panel project-panel">
          <div className="panel-heading"><div><p className="step">01</p><h2>Project</h2></div>{dirty && <span className="dirty">Unsaved</span>}</div>
          <div className="button-grid"><button onClick={newProject}>New</button><label className="button">Open<input type="file" accept=".json,application/json" onChange={loadProject} /></label><button onClick={saveProject} disabled={runtime !== "ready"}>Save</button></div>
          {input("project_name", "Project name")}{input("route_name", "Route name")}
          <div className="source-card">
            <div><p className="eyebrow">Alignment source</p><strong>{landxml?.source?.filename || "No LandXML selected"}</strong></div>
            <label className="button accent">{landxml ? "Replace XML" : "Select LandXML"}<input type="file" accept=".xml,text/xml,application/xml" onChange={selectLandxml} /></label>
            {landxml && <><p>{landxml.summary.alignment_name || "Unnamed alignment"} · {landxml.summary.linear_unit || "units undeclared"}</p><p>{landxml.summary.curve_count} curves · SHA {landxml.source.sha256.slice(0, 10)}…</p><button onClick={addAll} disabled={!inputs.speed}>Add all LandXML curves</button></>}
          </div>
          <div className="curve-list"><div className="list-title"><h3>Calculated curves</h3><span>{curves.length}</span></div>
            {curves.length === 0 ? <p className="empty">Add a calculated curve to build a combined export set.</p> : curves.map((curve, index) => <button key={index} className={selectedCurve === index ? "selected" : ""} onClick={() => loadCurve(index)}><strong>{curve.meta?.curve_name || `Curve ${index + 1}`}</strong><span>{curve.meta?.alignment_name} · {curve.meta?.curve_direction}</span></button>)}
          </div>
          <div className="button-grid"><button onClick={addCurve}>Add</button><button onClick={updateCurve}>Update</button><button onClick={() => { if (selectedCurve >= 0) { setCurves((items) => items.filter((_, i) => i !== selectedCurve)); setSelectedCurve(-1); setDirty(true); } }}>Remove</button></div>
        </aside>

        <section className="panel inputs-panel">
          <div className="panel-heading"><div><p className="step">02</p><h2>Curve inputs</h2></div><span className="required-note">* Required</span></div>
          {(landxml?.curve_presets?.length || 0) > 0 && <label className="field full"><span>LandXML curve</span><select value={landxmlPreset} onChange={(e) => applyPreset(Number(e.target.value))}>{landxml?.curve_presets?.map((preset: Dict, index: number) => <option value={index} key={index}>{preset.curve_name} · {preset.curve_direction} · R {preset.radius_ft}</option>)}</select></label>}
          <div className="form-grid">{input("alignment_name", "Alignment name")}{input("curve_name", "Curve name")}
            <label className="field"><span>Curve direction</span><select value={inputs.curve_direction} onChange={(e) => update("curve_direction", e.target.value)}><option value="left">Left</option><option value="right">Right</option></select></label>
            {input("pc", "PC station", true)}{input("pt", "PT station")}
            <label className="field"><span>Design speed <b>*</b></span><select value={inputs.speed} onChange={(e) => update("speed", e.target.value)}><option value="">Select mph</option>{manifest?.options?.speed?.map((speed: string) => <option key={speed}>{speed}</option>)}</select></label>
            {input("radius", "Curve radius (ft)", true, "number")}
            <label className="field"><span>Facility / rotation</span><select value={inputs.facility} disabled={inputs.area === "local"} onChange={(e) => update("facility", e.target.value)}><option value="centerline">Centerline</option><option value="outside edge">Outside edge</option></select></label>
            <label className="field"><span>Area type</span><select value={inputs.area} onChange={(e) => update("area", e.target.value)}><option value="rural">Rural</option><option value="urban">Urban</option><option value="local">Local</option></select></label>
            {input("lane_width", "Lane width (ft)", false, "number")}{input("lanes_rotated", "Lanes rotated", false, "number")}
          </div>
          <button className="advanced-toggle" aria-expanded={advancedOpen} onClick={() => setAdvancedOpen(!advancedOpen)}><span>Advanced settings</span><small>Optional criteria overrides and stationing</small><b>{advancedOpen ? "−" : "+"}</b></button>
          {advancedOpen && <div className="advanced-grid">{input("e_manual", "Manual e")}{input("friction", "Side friction")}{input("rel_grad", "Relative gradient")}{input("normal_crown", "Normal crown")}{input("Lr_manual", "Runoff Lr (ft)")}{input("Lt_manual", "Runout Lt (ft)")}{input("station_equations", "Station equations")}{input("alignment_station_range", "Internal station range")}</div>}
          <label className="field full"><span>Curve notes</span><textarea value={inputs.curve_notes} onChange={(e) => update("curve_notes", e.target.value)} rows={3} /></label>
          <div className="compute-bar"><label className="check"><input type="checkbox" checked={inputs.station_format} onChange={(e) => update("station_format", e.target.checked)} /> Station format</label><span className="auto-status">Calculates automatically</span><button onClick={() => { setInputs((current) => ({ ...INITIAL_INPUTS, project_name: current.project_name, route_name: current.route_name })); setCalculation(null); }}>Clear curve</button><button className="primary" onClick={calculate} disabled={runtime !== "ready" || !!busy}>{busy || (calculation ? "Recompute now" : "Compute now")}</button></div>
        </section>

        <section className="panel results-panel">
          <div className="panel-heading"><div><p className="step">03</p><h2>Results</h2></div>{result && <span className="criteria-tag">{result.calculation_metadata?.criteria?.profile_id || "criteria recorded"}</span>}</div>
          {!result ? <div className="results-empty"><div className="road-crown"><i></i><i></i></div><h3>Ready for curve inputs</h3><p>Enter PC, speed, and radius to calculate transition stations and signed lane slopes.</p></div> : <>
            <div className="metric-grid"><article><span>Rate e</span><strong>{Number(result.e || 0).toFixed(4)}</strong><small>{result.e_source || "automatic"}</small></article><article><span>Runoff Lr</span><strong>{Number(result.Lr || 0).toFixed(2)}′</strong><small>{inputs.Lr_manual ? "override" : "automatic"}</small></article><article><span>Runout Lt</span><strong>{Number(result.Lt || 0).toFixed(2)}′</strong><small>{inputs.Lt_manual ? "override" : "automatic"}</small></article></div>
            <div className="result-tabs"><h3>Lane events</h3><label className="check"><input type="checkbox" checked={inputs.station_format} onChange={(e) => update("station_format", e.target.checked)} /> Station labels</label></div>
            <div className="lane-tables">{(["left", "right"] as const).map((lane) => <div key={lane}><h4>{lane} lane</h4><table><thead><tr><th>Point</th><th>Station</th><th>Slope</th></tr></thead><tbody>{(lanes[lane] || []).map((row: Dict, index: number) => <tr key={index}><td>{row.label}</td><td>{row.station}</td><td className={String(row.slope_label).startsWith("+") ? "positive" : ""}>{row.slope_label}</td></tr>)}</tbody></table></div>)}</div>
            <div className="lookup"><h3>Engineering lookup</h3><div><input aria-label="Lookup station" placeholder="Station" value={lookupStation} onChange={(e) => setLookupStation(e.target.value)} /><input aria-label="Lookup superelevation" placeholder="Super (2%, 2, or 0.02)" value={lookupSlope} onChange={(e) => setLookupSlope(e.target.value)} /><button onClick={performLookup}>Lookup</button></div>{lookupResult && <div className="lookup-output">
              {lookupResult.station && <section className="lookup-card"><div className="lookup-heading"><span>Station</span><strong>{lookupResult.station.label}</strong></div><div className="lookup-lanes">{(["left", "right"] as const).map((lane) => <article key={lane}><span>{lane} lane</span><strong>{lookupResult.station.slopes[lane].label}</strong><small>{lookupResult.station.slopes[lane].decimal} ft/ft</small></article>)}</div></section>}
              {lookupResult.slope && <section className="lookup-card"><div className="lookup-heading"><span>Slope target</span><strong>{lookupResult.slope.label}</strong><small>{lookupResult.slope.decimal} ft/ft</small></div><div className="lookup-match-grid">{(["left", "right"] as const).map((lane) => <article className="lookup-matches" key={lane}><h4>{lane} lane</h4>{(lookupResult.lanes[lane] || []).length ? <ul>{lookupResult.lanes[lane].map((match: Dict, index: number) => <li key={index}><span>{match.label}</span><strong>{match.is_range ? `${match.start} – ${match.end}` : match.start}</strong>{match.nearest && <em>Nearest</em>}</li>)}</ul> : <p>No matching station</p>}</article>)}</div></section>}
            </div>}</div>
          </>}
        </section>
      </div>

      <section className="exports panel"><div><p className="step">04</p><h2>Review & export</h2><p>Exports use the same recorded calculation results shown above. Supported browsers open a Save dialog; others use Downloads.</p></div><div className="crs-fields"><label><span>LandXML source CRS</span><select value={sourceCrs} onChange={(e) => setSourceCrs(e.target.value)}>{manifest?.options?.coordinate_systems?.map((item: string) => <option key={item}>{item}</option>)}</select></label><label><span>Destination CRS</span><select value={targetCrs} onChange={(e) => setTargetCrs(e.target.value)}>{manifest?.options?.coordinate_systems?.map((item: string) => <option key={item}>{item}</option>)}</select></label></div><div className="export-buttons"><button onClick={() => performExport("export_pdf", "pdf", "application/pdf")}>PDF report</button><button onClick={() => performExport("export_ord_csv", "csv", "text/csv")}>ORD CSV</button><button className="primary" onClick={() => performExport("export_overlay_dxf", "dxf", "application/dxf")}>Overlay DXF</button></div></section>

      <footer><p><strong>Engineering aid.</strong> Validate criteria, stationing, coordinate systems, lane naming, and exported geometry against governing standards and the project design file.</p><p>No account · No upload · Browser-only processing</p></footer>
    </main>
  );
}
