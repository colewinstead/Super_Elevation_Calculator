import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the browser-only calculator shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  const source = await readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8");
  assert.match(html, /<title>Superelevation Calculator<\/title>/i);
  assert.match(html, /CalculatorApp-[^"']+\.js/i);
  assert.match(source, /Private browser engine/i);
  assert.match(source, /Select LandXML/i);
  assert.match(source, /Curve inputs/i);
  assert.match(source, /Review & export/i);
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
  assert.match(manifest, /super_service\.py/);
  assert.match(worker, /new URL\("\.\/python\/", self\.location\.href\)/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});

test("supports deployment beneath a GitHub Pages project path", async () => {
  const [source, pagesConfig] = await Promise.all([
    readFile(new URL("../app/CalculatorApp.tsx", import.meta.url), "utf8"),
    readFile(new URL("../vite.pages.config.ts", import.meta.url), "utf8"),
  ]);
  assert.match(source, /new Worker\("pyodide-worker\.js"\)/);
  assert.match(pagesConfig, /PAGES_BASE_PATH/);
  assert.match(pagesConfig, /dist-pages/);
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
