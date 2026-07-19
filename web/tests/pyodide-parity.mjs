import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { loadPyodide } from "pyodide";

const runtimeRoot = new URL("../public/python/", import.meta.url);
const pyodide = await loadPyodide();
await pyodide.loadPackage(["micropip", "pyproj", "numpy", "fonttools", "Pillow"]);
await pyodide.runPythonAsync(`
import micropip
await micropip.install(["reportlab==4.4.7", "ezdxf==1.4.4"])
`);

pyodide.FS.mkdirTree("/app");
const manifest = JSON.parse(await readFile(new URL("manifest.json", runtimeRoot), "utf8"));
for (const moduleName of manifest.modules) {
  pyodide.FS.writeFile(`/app/${moduleName}`, await readFile(new URL(moduleName, runtimeRoot), "utf8"), { encoding: "utf8" });
}

await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/app")
import super_service
`);

const payload = JSON.stringify({
  inputs: {
    pc: "10+00", pt: "12+00", speed: "45", radius: "1000",
    facility: "centerline", area: "rural", lane_width: "12",
    lanes_rotated: "2", normal_crown: "0.02", curve_direction: "right",
  },
});
pyodide.globals.set("payload", payload);
const calculationProxy = pyodide.runPython(`super_service.dispatch("calculate", payload)`);
const calculation = calculationProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
calculationProxy.destroy();

assert.deepEqual(
  {
    e: calculation.results.e,
    Lr: calculation.results.Lr,
    Lt: calculation.results.Lt,
    reverse_crown_ft: calculation.results.reverse_crown_ft,
    full_super_ft: calculation.results.full_super_ft,
  },
  { e: 0.08, Lr: 178, Lt: 44, reverse_crown_ft: 875.4, full_super_ft: 1053.4 },
);
assert.ok(calculation.lanes.left.length > 0);
assert.ok(calculation.lanes.right.length > 0);

pyodide.globals.set("diagram_payload", JSON.stringify({ results: calculation.results, direction: "right" }));
const diagramProxy = pyodide.runPython(`super_service.dispatch("curve_diagram", diagram_payload)`);
const diagram = diagramProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
diagramProxy.destroy();
assert.ok(diagram.profiles.left.length > 0);
assert.ok(diagram.markers.some((marker) => marker.kind === "PC"));

pyodide.globals.set("corridor_diagram_payload", JSON.stringify({
  curves: [
    { results: calculation.results, meta: { curve_name: "Curve A", curve_direction: "right" } },
    { results: calculation.results, meta: { curve_name: "Curve B", curve_direction: "left" } },
  ],
}));
const corridorDiagramProxy = pyodide.runPython(`super_service.dispatch("corridor_diagram", corridor_diagram_payload)`);
const corridorDiagram = corridorDiagramProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
corridorDiagramProxy.destroy();
assert.equal(corridorDiagram.curve_count, 2);
assert.deepEqual(corridorDiagram.curves.map((curve) => curve.curve_name), ["Curve A", "Curve B"]);

const tdotPayload = JSON.stringify({
  inputs: {
    criteria_profile: "tdot-rd11-2026-04-30",
    pc: "10+00", pt: "20+00", speed: "50", radius: "2280",
    facility: "undivided", area: "rural", lane_width: "12",
    lanes_rotated: "2", normal_crown: "0.02", curve_direction: "left",
  },
});
pyodide.globals.set("tdot_payload", tdotPayload);
const tdotProxy = pyodide.runPython(`super_service.dispatch("calculate", tdot_payload)`);
const tdot = tdotProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
tdotProxy.destroy();
assert.equal(tdot.results.calculation_metadata.criteria.profile_id, "tdot-rd11-2026-04-30");
assert.deepEqual(
  { e: tdot.results.e, Lr: tdot.results.Lr },
  { e: 0.046, Lr: 110 },
);
assert.ok(tdot.lanes.left.length > 0);
assert.ok(tdot.lanes.right.length > 0);

const landxmlPayload = JSON.stringify({
  filename: "tdot-coordinate-test.xml",
  content: `<?xml version="1.0"?>
<LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2" version="1.2">
  <Units><Imperial linearUnit="USSurveyFoot" /></Units>
  <CoordinateSystem horizontalDatum="NAD83(2011)" horizontalCoordinateSystemName="TN83/2011F" />
  <Alignments><Alignment name="TDOT Test" length="100" staStart="0"><CoordGeom>
    <Line length="100"><Start>500000 1200000 0</Start><End>500100 1200000 0</End></Line>
  </CoordGeom></Alignment></Alignments>
</LandXML>`,
});
pyodide.globals.set("landxml_payload", landxmlPayload);
const landxmlProxy = pyodide.runPython(`super_service.dispatch("parse_landxml", landxml_payload)`);
const landxml = landxmlProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
landxmlProxy.destroy();
assert.equal(landxml.summary.coordinate_system.status, "recognized");
assert.equal(landxml.summary.coordinate_system.code, "6576");
assert.equal(landxml.summary.coordinate_system.preserve_xy, true);

const corridorContent = `<?xml version="1.0"?>
<LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2" version="1.2">
  <Units><Imperial linearUnit="USSurveyFoot" /></Units>
  <Alignments><Alignment name="QA Test" length="2785.398" staStart="0"><CoordGeom>
    <Line length="1000"><Start>0 0 0</Start><End>0 1000 0</End></Line>
    <Curve rot="ccw" radius="500" length="785.398"><Start>0 1000 0</Start><Center>-500 1000 0</Center><End>-500 1500 0</End></Curve>
    <Line length="1000"><Start>-500 1500 0</Start><End>-500 2500 0</End></Line>
  </CoordGeom></Alignment></Alignments>
</LandXML>`;
const batchPayload = JSON.stringify({
  content: corridorContent,
  filename: "qa-test.xml",
  shared_inputs: { speed: "30", facility: "centerline", area: "rural", lane_width: "12", lanes_rotated: "2", normal_crown: "0.02" },
});
pyodide.globals.set("batch_payload", batchPayload);
const batchProxy = pyodide.runPython(`super_service.dispatch("build_all_landxml_curves", batch_payload)`);
const batchCurves = batchProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
batchProxy.destroy();
pyodide.globals.set("qa_payload", JSON.stringify({ content: corridorContent, filename: "qa-test.xml", curves: batchCurves }));
const qaProxy = pyodide.runPython(`super_service.dispatch("corridor_qa", qa_payload)`);
const qa = qaProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
qaProxy.destroy();
assert.equal(qa.status, "pass");
assert.equal(qa.curve_count, 1);

pyodide.globals.set("plan_payload", JSON.stringify({ content: corridorContent, filename: "qa-test.xml", curves: batchCurves }));
const planProxy = pyodide.runPython(`super_service.dispatch("plan_view", plan_payload)`);
const plan = planProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
planProxy.destroy();
assert.ok(plan.entities.some((entity) => entity.type === "LINE"));
assert.ok(plan.entities.some((entity) => entity.type === "TEXT"));
assert.equal(plan.layers.ALI_DESIGN_ML_CURVES.color, 8);
assert.equal(plan.background, "#101010");
assert.equal(plan.curve_paths, undefined);

pyodide.globals.set("invalid_project_payload", JSON.stringify({ content: "" }));
const invalidProjectProxy = pyodide.runPython(`super_service.dispatch_safe("project_load", invalid_project_payload)`);
const invalidProject = invalidProjectProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
invalidProjectProxy.destroy();
assert.equal(invalidProject.ok, false);
assert.match(invalidProject.error.message, /not valid JSON/);
assert.doesNotMatch(invalidProject.error.message, /Traceback/);

pyodide.globals.set("excluded_qa_payload", JSON.stringify({
  content: corridorContent,
  filename: "qa-test.xml",
  curves: [],
  excluded_curve_indexes: [0],
}));
const excludedQaProxy = pyodide.runPython(`super_service.dispatch("corridor_qa", excluded_qa_payload)`);
const excludedQa = excludedQaProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
excludedQaProxy.destroy();
assert.equal(excludedQa.status, "pass");
assert.equal(excludedQa.curve_count, 0);
assert.equal(excludedQa.excluded_count, 1);

pyodide.globals.set("results_payload", JSON.stringify({
  curves: [{ results: calculation.results, meta: { curve_direction: "right" }, notes: "" }],
}));
const csvProxy = pyodide.runPython(`super_service.dispatch("export_ord_csv", results_payload)`);
const csv = csvProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
csvProxy.destroy();
assert.match(csv.content, /SuperelevationLane,Station,CrossSlope/);

const pdfProxy = pyodide.runPython(`super_service.dispatch("export_pdf", results_payload)`);
const pdf = pdfProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
pdfProxy.destroy();
assert.equal(String.fromCharCode(...pdf.content.slice(0, 4)), "%PDF");

const dxfProxy = pyodide.runPython(`super_service.dispatch("export_detail_dxf", results_payload)`);
const dxf = dxfProxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
dxfProxy.destroy();
assert.match(new TextDecoder().decode(dxf.content), /SECTION/);

console.log("Pyodide calculation, analysis, and export parity passed.");
