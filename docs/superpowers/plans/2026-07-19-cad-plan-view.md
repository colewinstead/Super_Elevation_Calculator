# CAD-Accurate Plan View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render Plan View from the exact overlay DXF entity records while preserving the accepted DXF drawing and changing only the alignment layer color from ACI 55 to ACI 8.

**Architecture:** Extract the existing `export_overlay_dxf` entity construction into a shared Python builder that returns the same `DxfWriter` records. The exporter saves those records unchanged, while `super_service.plan_view` serializes them for a CAD-style SVG renderer. React handles only display, zoom, pan, fit, and entity selection.

**Tech Stack:** Python 3, ezdxf, LandXML shared engine, Pyodide, React 19, TypeScript, SVG, unittest, Node test runner.

---

## File Map

- Modify `super_dxf.py`: freeze the existing entity sequence, extract the shared overlay builder, expose preview serialization and bounds, and set alignment ACI to 8.
- Modify `super_service.py`: return the serialized shared overlay drawing from `plan_view`.
- Modify `test_super_exports.py`: preserve the accepted overlay record digest and verify the sole approved layer-color change.
- Modify `test_super_qa.py`: replace simplified preview expectations with shared CAD entity expectations.
- Modify `web/app/SuperelevationPlanView.tsx`: render shared DXF line/text entities and retain CAD navigation/selection.
- Modify `web/app/globals.css`: replace simplified plan styles with CAD model-space styles.
- Modify `web/tests/rendered-html.test.mjs`: verify entity-driven rendering and removal of event dots.
- Modify `web/tests/pyodide-parity.mjs`: verify native/Pyodide preview model fields.

### Task 1: Freeze And Extract The Accepted DXF Drawing

**Files:**
- Modify: `test_super_exports.py`
- Modify: `super_dxf.py`

- [ ] **Step 1: Add a failing golden-record regression test**

Add `hashlib`, `json`, and `super_service` imports, then add a helper that captures `DxfWriter._records` without writing a file and hashes the JSON-normalized sequence:

```python
def overlay_record_digest(self) -> tuple[int, str]:
    content = LANDXML_FIXTURE.read_text(encoding="utf-8")
    data = super_landxml.parse_landxml_text(content, LANDXML_FIXTURE.name)
    curves = super_service.build_all_landxml_curves(
        content,
        LANDXML_FIXTURE.name,
        {
            "speed": "45",
            "facility": "centerline",
            "area": "rural",
            "lane_width": "12",
            "lanes_rotated": "2",
            "normal_crown": "0.02",
        },
    )
    captured = {}
    original = super_dxf.DxfWriter.save

    def capture(writer, *_args, **_kwargs):
        captured["records"] = list(writer._records)

    super_dxf.DxfWriter.save = capture
    try:
        super_dxf.export_overlay_dxf("unused.dxf", curves, data)
    finally:
        super_dxf.DxfWriter.save = original
    encoded = json.dumps(captured["records"], separators=(",", ":")).encode("utf-8")
    return len(captured["records"]), hashlib.sha256(encoded).hexdigest()

def test_overlay_entity_sequence_is_preserved(self):
    self.assertEqual(
        self.overlay_record_digest(),
        (202, "a1c717d252b5e235ca3f01f53646a536d2c24811c08f17e4f2822e0c99a4e165"),
    )

def test_overlay_alignment_layer_uses_gray_aci(self):
    self.assertEqual(
        super_dxf.DEFAULT_CONFIG["overlay_layer_styles"]["ALI_DESIGN_ML_CURVES"]["color"],
        8,
    )
```

- [ ] **Step 2: Run the tests and verify only the color test fails**

Run: `python -m unittest -v test_super_exports.SuperExportTests.test_overlay_entity_sequence_is_preserved test_super_exports.SuperExportTests.test_overlay_alignment_layer_uses_gray_aci`

Expected: the record digest passes and the ACI assertion fails with `55 != 8`.

- [ ] **Step 3: Extract the current builder without changing record construction**

Move the entity-building body of `export_overlay_dxf` into:

```python
def build_overlay_drawing(
    curves: Iterable[dict],
    landxml: super_landxml.LandXMLData,
    config: dict | None = None,
) -> tuple[DxfWriter, dict, list[str]]:
    cfg = _cfg(config)
    writer = DxfWriter()
    warnings = list(landxml.warnings)
    # The current export_overlay_dxf entity-construction statements are moved
    # here verbatim and remain in their current order.
    unique_warnings = []
    for warning in warnings:
        if warning not in unique_warnings:
            unique_warnings.append(warning)
    return writer, cfg, unique_warnings

def export_overlay_dxf(path, curves, landxml, config=None):
    writer, cfg, warnings = build_overlay_drawing(curves, landxml, config)
    writer.save(
        path,
        dxf_insunits(landxml.linear_unit),
        cfg.get("overlay_layer_styles"),
        cfg.get("overlay_text_styles"),
    )
    return warnings
```

Mechanically move the current segment loop, curve loop, row loop, label packing, leader creation, station/slope text creation, curve title creation, radius text creation, and warning de-duplication from the existing `export_overlay_dxf` into `build_overlay_drawing`. Do not edit any expression inside those blocks. The golden digest detects any changed record order or value.

Change only the default alignment style:

```python
"ALI_DESIGN_ML_CURVES": {"color": 8, "linetype": "CONTINUOUS", "lineweight": 40},
```

- [ ] **Step 4: Run focused export tests**

Run: `python -m unittest -v test_super_exports.py`

Expected: all export tests pass, including the unchanged 202-record digest and ACI 8 assertion.

- [ ] **Step 5: Commit the isolated shared-builder change**

```powershell
git add -- super_dxf.py test_super_exports.py
git commit -m "refactor: share overlay DXF drawing records"
```

### Task 2: Serialize The Shared CAD Model For Plan View

**Files:**
- Modify: `super_dxf.py`
- Modify: `super_service.py`
- Modify: `test_super_qa.py`

- [ ] **Step 1: Replace the simplified preview test with a failing CAD-model test**

Add assertions against `super_service.plan_view`:

```python
def test_plan_view_uses_overlay_dxf_entities(self):
    preview = super_service.plan_view(self.content, FIXTURE.name, self.curves())
    self.assertEqual(preview["background"], "#101010")
    self.assertEqual(preview["layers"]["ALI_DESIGN_ML_CURVES"]["color"], 8)
    self.assertTrue(any(entity["type"] == "LINE" for entity in preview["entities"]))
    self.assertTrue(any(entity["type"] == "TEXT" for entity in preview["entities"]))
    self.assertTrue(any(entity.get("text", "").startswith("R=") for entity in preview["entities"]))
    self.assertNotIn("curve_paths", preview)
    self.assertNotIn("events", preview)
    self.assertLess(preview["bounds"]["min_x"], preview["bounds"]["max_x"])
```

- [ ] **Step 2: Run the focused test and verify it fails on the old payload**

Run: `python -m unittest -v test_super_qa.CorridorQATests.test_plan_view_uses_overlay_dxf_entities`

Expected: FAIL because `entities`, `layers`, and `background` are absent.

- [ ] **Step 3: Add record serialization and bounds to `super_dxf.py`**

Add `DxfWriter._preview_metadata: dict[int, dict]`. Extend `add_line` and `add_text` with a keyword-only `preview: dict | None = None`; after appending each unchanged tuple record, store the metadata under that record index. In the overlay row loop, use `group_id = f"curve-{curve_index}-row-{row_index}"` and attach this metadata to both leader lines and both callout texts:

```python
preview_metadata = {
    "group_id": group_id,
    "curve_index": curve_index,
    "curve_name": meta.get("curve_name", row["curve_name"]),
    "station": row["station_label"],
    "station_ft": station,
    "side": lane_side,
    "slope": row["slope_label"],
    "event_type": row["event_type"],
}
```

Attach `group_id = f"curve-{curve_index}-title"` and curve identity metadata to title/radius text. These additions must not alter `_records` or the golden digest.

Implement serialization helpers with these response shapes:

```python
def overlay_preview_model(curves, landxml, config=None) -> dict:
    writer, cfg, warnings = build_overlay_drawing(curves, landxml, config)
    entities = []
    for index, record in enumerate(writer._records):
        if record[0] == "LINE":
            _, x1, y1, x2, y2, layer = record
            entities.append({"id": index, "type": "LINE", "layer": layer,
                             "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                             "preview": writer._preview_metadata.get(index)})
        else:
            _, x, y, text, height, layer, rotation, alignment, text_style = record
            entities.append({"id": index, "type": "TEXT", "layer": layer,
                             "x": x, "y": y, "text": text, "height": height,
                             "rotation": rotation, "alignment": alignment,
                             "text_style": text_style,
                             "preview": writer._preview_metadata.get(index)})
    return {
        "background": "#101010",
        "entities": entities,
        "layers": cfg["overlay_layer_styles"],
        "bounds": _overlay_preview_bounds(entities),
        "warnings": warnings,
    }
```

`_overlay_preview_bounds` must include line endpoints and conservative rotated text corners using `len(text) * height * 0.62` for width, respecting left/right alignment. This affects Fit only and must not modify DXF records.

- [ ] **Step 4: Route `super_service.plan_view` through the shared model**

```python
def plan_view(content: str, filename: str, curves: list[dict]) -> dict[str, Any]:
    data = super_landxml.parse_landxml_text(content, filename)
    preview = super_dxf.overlay_preview_model(curves, data)
    errors, diagnostic_warnings = super_dxf.overlay_export_issues(curves, data)
    return {
        **preview,
        "alignment_name": data.alignment_name,
        "coordinate_system": data.coordinate_system.as_dict(),
        "linear_unit": data.linear_unit,
        "errors": errors,
        "warnings": list(dict.fromkeys(diagnostic_warnings + preview["warnings"])),
    }
```

- [ ] **Step 5: Run Python CAD-model and export regression tests**

Run: `python -m unittest -v test_super_qa.py test_super_exports.py test_web_service.py`

Expected: all tests pass and the golden DXF record digest remains unchanged.

- [ ] **Step 6: Commit the service model**

```powershell
git add -- super_dxf.py super_service.py test_super_qa.py
git commit -m "feat: expose overlay DXF model for plan view"
```

### Task 3: Render The CAD Model In React

**Files:**
- Modify: `web/app/SuperelevationPlanView.tsx`
- Modify: `web/app/globals.css`
- Modify: `web/tests/rendered-html.test.mjs`

- [ ] **Step 1: Add failing rendered-source contracts**

Replace simplified event-dot assertions with:

```javascript
assert.match(planSource, /plan\.entities/);
assert.match(planSource, /entity\.type === "LINE"/);
assert.match(planSource, /entity\.type === "TEXT"/);
assert.match(planSource, /rotate\(/);
assert.match(planSource, /textAnchor/);
assert.match(planSource, /cadColor/);
assert.doesNotMatch(planSource, /className="plan-event/);
assert.doesNotMatch(planSource, /plan\.curve_paths/);
assert.match(planSource, /selectedGroup/);
```

- [ ] **Step 2: Run rendered tests and verify failure**

Run: `node --test tests/rendered-html.test.mjs`

Expected: FAIL because Plan View still renders `curve_paths` and event circles.

- [ ] **Step 3: Implement the SVG CAD renderer**

Keep the existing view-box, wheel, and pointer navigation. Replace polyline/event rendering with line and text entities:

```tsx
function cadColor(aci: number) {
  return ({ 7: "#f2f2f2", 8: "#808080", 10: "#ff0000" } as Record<number, string>)[aci] || "#d8d8d8";
}

const layerStyle = (entity: Dict) => plan.layers?.[entity.layer] || {};

{(plan.entities || []).map((entity: Dict) => {
  const style = layerStyle(entity);
  const selected = entity.preview?.group_id === selectedGroup;
  if (entity.type === "LINE") {
    return <line key={entity.id} className="cad-line"
      x1={entity.x1} y1={-entity.y1} x2={entity.x2} y2={-entity.y2}
      stroke={cadColor(Number(style.color))}
      strokeWidth={cadLineweight(Number(style.lineweight))}
      data-selected={selected || undefined}
      onPointerDown={(event) => entity.preview?.group_id && event.stopPropagation()}
      onClick={() => entity.preview?.group_id && setSelectedGroup(entity.preview.group_id)} />;
  }
  return <text key={entity.id} className="cad-text"
    x={entity.x} y={-entity.y}
    fill={cadColor(Number(style.color))}
    fontSize={entity.height}
    textAnchor={entity.alignment === "RIGHT" ? "end" : "start"}
    transform={`rotate(${-Number(entity.rotation)} ${entity.x} ${-entity.y})`}
    data-selected={selected || undefined}
    onPointerDown={(event) => entity.preview?.group_id && event.stopPropagation()}
    onClick={() => entity.preview?.group_id && setSelectedGroup(entity.preview.group_id)}>
    {entity.text}
  </text>;
})}
```

Use `vector-effect: non-scaling-stroke` for lines, a model-space monospace/engineering font stack for text, `#101010` canvas background, square line caps, and no decorative curve highlighting or event circles. Clicking a callout line or text selects every entity with its `group_id`; the inspector displays curve, station, side, slope, and event type from shared metadata. Clicking title/radius text selects the title group and displays curve identity.

- [ ] **Step 4: Verify frontend checks**

Run:

```powershell
npx tsc --noEmit
npm run lint
node --test tests/rendered-html.test.mjs
```

Expected: all checks pass.

- [ ] **Step 5: Commit the CAD renderer**

```powershell
git add -- web/app/SuperelevationPlanView.tsx web/app/globals.css web/tests/rendered-html.test.mjs
git commit -m "feat: render plan view as CAD model space"
```

### Task 4: Pyodide Parity And End-To-End Verification

**Files:**
- Modify: `web/tests/pyodide-parity.mjs`

- [ ] **Step 1: Add failing Pyodide preview assertions**

```javascript
assert.ok(plan.entities.some((entity) => entity.type === "LINE"));
assert.ok(plan.entities.some((entity) => entity.type === "TEXT"));
assert.equal(plan.layers.ALI_DESIGN_ML_CURVES.color, 8);
assert.equal(plan.background, "#101010");
assert.equal(plan.curve_paths, undefined);
```

- [ ] **Step 2: Regenerate runtime and run parity**

Run:

```powershell
python ../scripts/prepare_web_runtime.py
node tests/pyodide-parity.mjs
```

Expected: parity passes with the shared CAD entity payload.

- [ ] **Step 3: Run all required validation**

Run:

```powershell
python -m unittest -v
Set-Location web
npx tsc --noEmit
npm run lint
$env:WRANGLER_LOG_PATH='.wrangler/wrangler.log'
npx vinext build
node --test tests/rendered-html.test.mjs
node tests/pyodide-parity.mjs
Set-Location ..
git diff --check
```

Expected: all Python tests, TypeScript, lint, production build, rendered tests, Pyodide parity, and whitespace validation pass.

- [ ] **Step 4: Compare SR8 Plan View with its exported DXF**

At `http://localhost:3000/calculator`, load `Sample Data/SR8.xml`, set the shared design speed, add all LandXML curves, and open Plan View. Verify:

- Gray alignment geometry matches exported `ALI_DESIGN_ML_CURVES` entities.
- Every leader, station label, slope label, curve title, and radius label appears at the exported coordinates and rotation.
- Fit includes all labels.
- Wheel zoom does not scroll the page.
- Drag pan works in normal and expanded views.
- No simplified event dots or teal curve overlays remain.
- Browser console has no relevant warnings or errors.

- [ ] **Step 5: Commit parity coverage**

```powershell
git add -- web/tests/pyodide-parity.mjs
git commit -m "test: verify CAD plan view Pyodide parity"
```
