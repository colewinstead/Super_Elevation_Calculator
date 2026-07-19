import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the product homepage without starting the calculation runtime", async () => {
  const response = await render("/");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Superelevation Calculator \| Roadway Design Toolkit/i);
  assert.match(html, /From roadway curve/i);
  assert.match(html, /Download EXE/i);
  assert.match(html, /SuperelevationCalculator-macOS-Apple-Silicon\.dmg/i);
  assert.match(html, /SuperelevationCalculator-macOS-Intel\.dmg/i);
  assert.match(html, /http:\/\/localhost\/og\.png/i);
  await access(new URL("../public/og.png", import.meta.url));
  assert.doesNotMatch(html, /Starting private browser workspace/i);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("renders the browser-only calculator shell on its dedicated route", async () => {
  const response = await render("/calculator");
  assert.equal(response.status, 200);
  const html = await response.text();
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(html, /<title>Browser Calculator \| Superelevation Calculator<\/title>/i);
  assert.match(html, /CalculatorApp-[^"']+\.js/i);
  assert.match(source, /Private browser engine/i);
  assert.match(source, /Select LandXML/i);
  assert.match(source, /Curve inputs/i);
  assert.match(source, /Review & export/i);
  assert.match(source, /preserves the LandXML XY coordinates without reprojection/i);
  assert.doesNotMatch(source, /Destination CRS|targetCrs|coordinate_config/i);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("ships the Python worker and shared runtime manifest", async () => {
  const [worker, manifest] = await Promise.all([
    readFile(new URL("../public/pyodide-worker.js", import.meta.url), "utf8"),
    readFile(new URL("../public/python/manifest.json", import.meta.url), "utf8"),
  ]);
  assert.match(worker, /PYODIDE_VERSION = "0\.29\.4"/);
  assert.match(worker, /reportlab==4\.4\.7/);
  assert.match(worker, /ezdxf==1\.4\.4/);
  assert.match(worker, /super_service\.dispatch_safe/);
  assert.match(manifest, /super_service\.py/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});

test("debounces automatic calculations when required inputs are ready", async () => {
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(source, /AUTO_CALC_DELAY_MS = 450/);
  assert.match(source, /Calculates automatically/);
  assert.match(source, /setTimeout\(async \(\) =>/);
});

test("recalculates after reapplying an identical LandXML preset", async () => {
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(source, /const \[calculationRequest, setCalculationRequest\] = useState\(0\)/);
  assert.match(source, /setCalculationRequest\(\(request\) => request \+ 1\)/);
  assert.match(source, /\[calculationKey, calculationRequest, runtime, call\]/);
});

test("opens a save picker for exports with a download fallback", async () => {
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(source, /showSaveFilePicker/);
  assert.match(source, /suggestedName: name/);
  assert.match(source, /createWritable/);
  assert.match(source, /if \(!picker\) return "download"/);
  assert.match(source, /Superelevation project/);
  assert.match(source, /Project \$\{outcome\}/);
  assert.doesNotMatch(source, />Detail DXF</);
});

test("renders lookup results as labeled engineering content instead of JSON", async () => {
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(source, /lookup-output/);
  assert.match(source, /Full-super range|match\.label/);
  assert.doesNotMatch(source, /JSON\.stringify\(lookupResult/);
});

test("uses the dark engineering workspace theme", async () => {
  const css = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");
  assert.match(css, /color-scheme: dark/);
  assert.match(css, /--paper: #07100e/);
  assert.match(css, /\.lookup-card/);
});

test("shows concise guidance for invalid project files", async () => {
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(source, /Use Select LandXML to open XML alignment files/);
  assert.match(source, /The selected project file is empty/);
});

test("ships interactive diagram zoom and corridor QA controls", async () => {
  const source = await readFile(new URL("../app/SuperelevationAnalysis.tsx", import.meta.url), "utf8");
  const planSource = await readFile(new URL("../app/SuperelevationPlanView.tsx", import.meta.url), "utf8");
  const appSource = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(source, /addEventListener\("wheel", wheelZoom, \{ passive: false \}\)/);
  assert.match(source, /event\.preventDefault\(\)/);
  assert.match(source, /Pan toward corridor start/);
  assert.match(source, /onPointerMove={movePan}/);
  assert.match(source, /onClick={selectPoint}/);
  assert.match(source, /Array\.from\(\{ length: 721 \}/);
  assert.match(source, /Math\.min\(\(activeDomain\[1\] - activeDomain\[0\]\).*5\)/);
  assert.match(source, /Open large analysis view/);
  assert.match(source, /Plan View/);
  assert.match(planSource, /plan\.entities/);
  assert.match(planSource, /entity\.type === "LINE"/);
  assert.match(planSource, /entity\.type === "TEXT"/);
  assert.match(planSource, /rotate\(/);
  assert.match(planSource, /textAnchor/);
  assert.match(planSource, /cadColor/);
  assert.match(planSource, /selectedGroup/);
  assert.match(planSource, /getScreenCTM\(\)/);
  assert.match(planSource, /matrix\.inverse\(\)/);
  assert.match(planSource, /clientPointToDrawing/);
  assert.match(planSource, /className="cad-hit-target"/);
  assert.match(planSource, /pointerEvents="stroke"/);
  assert.doesNotMatch(planSource, /className="plan-event/);
  assert.doesNotMatch(planSource, /plan\.curve_paths/);
  assert.match(planSource, /addEventListener\("wheel", wheelZoom, \{ passive: false \}\)/);
  assert.match(planSource, /onPointerMove={movePan}/);
  assert.match(source, /diagrams\.flatMap/);
  assert.match(appSource, /No LandXML curve selected/);
  assert.match(appSource, /excluded_landxml_curve_indexes/);
  assert.match(appSource, /const removeCurve/);
  assert.match(appSource, /index === selectedCurve/);
  assert.match(appSource, /results: calculation\.results/);
  assert.match(source, /Zoom in/);
  assert.match(source, /Reset zoom/);
  assert.match(source, /Snap events/);
  assert.match(source, /Corridor QA/);
  assert.match(appSource, /diagram_lookup/);
  assert.match(appSource, /corridor_diagram/);
  assert.match(appSource, /plan_view/);
});
