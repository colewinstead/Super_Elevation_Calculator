# CAD-Accurate Plan View Design

## Objective

Make the browser Plan View represent the overlay DXF model space from the same entity data used for export. Geometry, callouts, text, rotations, layers, colors, and lineweights must not be independently reconstructed in React.

The alignment layer will change from its current brown ACI 55 appearance to neutral gray ACI 8 in both Plan View and exported overlay DXFs.

## Architecture

`super_dxf` will own a shared overlay drawing model. The existing overlay construction logic will populate a `DxfWriter` with `LINE` and `TEXT` records once. Two consumers will use those records:

1. The DXF export path will write the records through ezdxf without changing the public export interface.
2. The browser plan-view service will serialize the same records, layer styles, text styles, units, warnings, errors, and drawing extents into a Pyodide response.

This keeps all engineering geometry and label-placement decisions in shared Python. React remains a renderer and interaction surface only.

## Shared Drawing Model

The model will contain:

- Entity type: `LINE` or `TEXT`.
- DXF coordinates without reprojection.
- Layer name.
- Effective ACI color, linetype, and lineweight.
- Text content, height, rotation, alignment, and text style for text entities.
- Optional curve/event metadata sufficient for browser selection and inspection.
- Drawing bounds that include line endpoints and estimated rotated text extents.
- LandXML alignment name, coordinate-system metadata, units, warnings, and blocking overlay errors.

The existing `DxfWriter` record format may be replaced with a small structured record type if that improves serialization and testing. The writer remains responsible for handles and final ezdxf output, not presentation decisions.

## Overlay Construction

Extract the body of `export_overlay_dxf` into a builder that accepts curves, parsed LandXML, and optional configuration, then returns the populated drawing model and warnings. It will continue to use the existing:

- LandXML line and circular-arc sampling.
- Normalized lane rows.
- Label station packing.
- Leader geometry.
- PC/PT station prefixes.
- Slope labels.
- Curve identity and radius titles.
- Text rotation, alignment, spacing, and font style.

`export_overlay_dxf(path, curves, landxml, config)` will call this builder and save its records. No formula, stationing, lane-event, or public export behavior changes are in scope.

## Browser Rendering

Plan View will use a dark CAD model-space canvas. SVG is retained because it supports exact world coordinates, rotations, crisp vector lines, text, wheel zoom, pointer pan, and entity selection without a new dependency.

Rendering rules:

- Lines render from shared start/end coordinates.
- Text renders at shared insertion points with DXF rotation and left/right alignment.
- SVG Y coordinates are inverted while text remains upright through the appropriate transform.
- Layer ACI colors map to explicit screen RGB values suitable for a dark CAD background.
- DXF lineweights map consistently to non-scaling SVG stroke widths.
- Text size derives from DXF text height and scales with world-space zoom, matching model-space behavior.
- Fit includes all exported geometry and callout text bounds.
- Existing zoom, pan, Fit, expanded view, error panel, and inspector remain available.
- Selecting a callout entity highlights its related leader/text group and shows station, slopes, curve identity, and event types when metadata is available.

The simplified curve highlight and event dots will be removed because they are not part of the DXF.

## Layer Presentation

The default overlay styles remain authoritative:

- `ALI_DESIGN_ML_CURVES`: ACI 8 neutral gray, continuous, lineweight 40.
- `ALI_DESIGN_ML_LABELS`: existing ACI 10, continuous, lineweight 40.
- `ALI_DESIGN_ML_STA`: existing ACI 7, continuous, lineweight 40.
- `ALI_DESIGN_ML_LABELS_TX`: existing ACI 7, continuous, lineweight 40.

Custom export configurations continue to override defaults, and Plan View will render the effective styles returned by the builder.

## Error Handling

When overlay export is blocked, Plan View will still display alignment geometry when it can be constructed and will show the same blocking issues as export. Entities that cannot be placed because a station is outside the alignment range will be omitted exactly as they are during export, with the same warnings.

An empty drawing response will show a concise CAD-preview empty state rather than a blank canvas.

## Testing

Python tests will verify:

- The preview and export paths use the same builder records.
- Representative `LINE` and `TEXT` records preserve coordinates, layers, rotations, alignments, text heights, and styles.
- ACI 8 is applied to the alignment layer in generated DXFs.
- Drawing bounds include leaders and text beyond the alignment extents.
- MDOT/TDOT and normal-crown scenarios retain their existing overlay content.

Browser tests will verify:

- Plan View renders shared line and text entities rather than simplified event dots.
- CAD colors and lineweights come from the response layer styles.
- Rotated text and right-aligned text use the serialized DXF values.
- Zoom, pan, Fit, selection, and expanded mode remain functional.
- Pyodide returns the same preview model as native Python.

The full Python suite, TypeScript check, lint, production build, rendered tests, and Pyodide parity suite must pass. A representative SR8 report will be inspected in the browser against its exported overlay DXF for visual agreement.

## Out Of Scope

- Editing DXF entities in the browser.
- Layer visibility controls.
- Paper-space layouts, title blocks, or plotting styles.
- A general-purpose DXF parser.
- Changes to calculations, formulas, lane construction, stationing, or project schema.
