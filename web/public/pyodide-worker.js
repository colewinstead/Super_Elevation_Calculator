const PYODIDE_VERSION = "0.29.4";
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYTHON_BASE = new URL("./python/", self.location.href);
let runtimePromise;

function status(message, progress) {
  self.postMessage({ type: "status", message, progress });
}

async function initialize() {
  if (runtimePromise) return runtimePromise;
  runtimePromise = (async () => {
    status("Loading private browser workspace…", 12);
    importScripts(`${PYODIDE_BASE}pyodide.js`);
    const pyodide = await loadPyodide({ indexURL: PYODIDE_BASE });
    status("Loading engineering dependencies…", 36);
    await pyodide.loadPackage(["micropip", "pyproj", "numpy", "fonttools", "Pillow"]);
    await pyodide.runPythonAsync(`
import micropip
await micropip.install(["reportlab==4.4.7", "ezdxf==1.4.4"])
`);
    status("Loading shared calculation engine…", 70);
    const manifest = await (await fetch(new URL("manifest.json", PYTHON_BASE), { cache: "no-cache" })).json();
    pyodide.FS.mkdirTree("/app");
    for (const moduleName of manifest.modules) {
      const response = await fetch(new URL(moduleName, PYTHON_BASE), { cache: "no-cache" });
      if (!response.ok) throw new Error(`Could not load ${moduleName}.`);
      pyodide.FS.writeFile(`/app/${moduleName}`, await response.text(), { encoding: "utf8" });
    }
    pyodide.runPython(`
import sys
sys.path.insert(0, "/app")
import super_service
`);
    const manifestProxy = pyodide.runPython("super_service.application_manifest()");
    const appManifest = manifestProxy.toJs({ dict_converter: Object.fromEntries });
    manifestProxy.destroy();
    status("Ready — files never leave this browser", 100);
    self.postMessage({ type: "ready", manifest: appManifest });
    return pyodide;
  })();
  return runtimePromise;
}

function convertResult(result) {
  if (result && typeof result.toJs === "function") {
    const converted = result.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
    result.destroy();
    return converted;
  }
  return result;
}

self.onmessage = async (event) => {
  const { id, operation, payload = {} } = event.data || {};
  if (operation === "initialize") {
    try {
      await initialize();
    } catch (error) {
      runtimePromise = undefined;
      self.postMessage({ type: "fatal", message: error?.message || String(error) });
    }
    return;
  }
  try {
    const pyodide = await initialize();
    const payloadJson = JSON.stringify(payload);
    pyodide.globals.set("_web_operation", operation);
    pyodide.globals.set("_web_payload", payloadJson);
    const proxy = pyodide.runPython("super_service.dispatch(_web_operation, _web_payload)");
    self.postMessage({ type: "response", id, ok: true, result: convertResult(proxy) });
  } catch (error) {
    self.postMessage({
      type: "response",
      id,
      ok: false,
      error: { message: error?.message || String(error), details: error?.stack || "" },
    });
  }
};
