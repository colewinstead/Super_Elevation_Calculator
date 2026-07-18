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
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});
