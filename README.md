# Superelevation Calculator

Superelevation calculator with MDOT-style calculations, PDF reporting, CSV exports, and DXF drawing handoff for OpenRoads Designer / MicroStation review workflows.

The desktop interface opens maximized so the calculation and export controls remain visible.

## Current workflows

The desktop app in [super_app.py](/C:/Python%20Projects/Super_Elevation_Calculator/super_app.py) now supports:

- `Export PDF`
- `Export ORD CSV`
- `Export Overlay DXF`

The original calculation path is still driven by [Super.py](/C:/Python%20Projects/Super_Elevation_Calculator/Super.py), and the PDF report still uses the same calculated curve objects as before.

## Running the app

Run:

```powershell
python -m pip install -r .\requirements.txt
python .\super_app.py
```

The PDF export depends on `reportlab`. If you skip the install step, the app will still run, but `Export PDF` will show a missing dependency warning.

## Metadata

The app now stores:

- `Project name`
- `Route name`
- `Alignment name`
- `Curve name`
- `Curve direction`
- optional `LandXML` path

These values are saved with project JSON files through [super_project.py](/C:/Python%20Projects/Super_Elevation_Calculator/super_project.py).

## CSV exports

### ORD CSV

The ORD CSV uses Bentley’s documented import header:

```text
SuperelevationLane,Station,CrossSlope,PivotAbout,PointType,TransitionType,NonLinearCurveLength
```

Current defaults:

- `TransitionType = L`
- `NonLinearCurveLength = 0`
- `PivotAbout = RS` for left lane, `LS` for right lane
- lane names default to `Left Lane` and `Right Lane` unless overridden in metadata later
- station labels after the first alignment equation receive the ORD suffix `R2`; subsequent regions use `R3`, `R4`, and so on

### ORD import checklist

Before relying on ORD import in production, verify in OpenRoads Designer that:

- the target superelevation section already exists
- the target lanes already exist
- lane names in ORD match the CSV lane names
- station formatting matches the design file civil formatting
- station equation behavior matches your reference alignment settings

The app writes a sidecar warnings file for ORD CSV exports when guidance needs to be preserved.

## DXF exports

### Overlay DXF

`Export Overlay DXF` is only enabled when:

- a LandXML file is loaded successfully
- the LandXML contains usable horizontal geometry
- no unsupported spiral handling is required
- every export station falls within the alignment limits

When the button is disabled, use **Show DXF Issues** directly beneath it. The dialog identifies each blocking curve, lane, event, and station, and separately lists non-blocking LandXML warnings such as station equations.

When enabled, the DXF is drawn in real project coordinates from the LandXML alignment geometry. This is still a graphics overlay, not native Bentley civil data.

The overlay DXF declares the LandXML linear unit (including US survey feet) in its header so CAD applications can insert/reference it at the correct scale. A coordinate-system transformation still requires coordinate-reference metadata in the LandXML or matching coordinates in the destination DGN.

LandXML points are read as Northing/Easting and written to CAD as X=Easting, Y=Northing. Curve direction is evaluated along increasing station after this conversion.

Imported LandXML curve radii are rounded to three decimal places before superelevation table lookup, preventing serialization noise such as `3499.9999999999995` from selecting the next table row.

Before every overlay DXF export, the app requires you to select the LandXML source and destination DGN coordinate systems: MDOT MS83/2011 East or West Zone (US survey foot). It preserves coordinates when the zones match and transforms all overlay geometry and labels when they differ.

For curves where the selected criteria require normal crown only, exports contain normal-crown records at the PC and PT (using the normal-crown slope) and do not create zero-slope, runoff, or full-superelevation events.

### Station equations

LandXML `StaEquation` records are applied automatically. PC/PT entry and exported labels use the displayed civil stationing, while DXF geometry continues to use continuous internal chainage. Without LandXML, enter manual equations as `Back=Ahead`, separating multiple equations with semicolons; for example, `1543+52.403=1233+15.920`. If the same displayed station can occur on both sides of an equation, also enter the continuous internal alignment range as `Start,End` so the app can resolve the intended location.

The overlay exporter now uses lane-specific leaders instead of a full cross tick through the alignment:

- each lane event gets its own leader line from the alignment out toward that lane side
- each callout shows the station plus only that lane's slope
- text is rotated perpendicular to the alignment
- nearby same-side callouts extend farther from the alignment as needed to reduce overlap
- a curve name marker is still placed near the start of each exported curve

Nearby callouts are packed along the alignment with a minimum separation, use two-segment elbow leaders, and are justified from the leader endpoint so labels consistently extend away from the roadway on either side.

Callouts located exactly at curve endpoints prefix their station with `PC` or `PT`, such as `PC 1456+68.845`.

Curve annotations use two parallel lines—such as `Curve 1 (right)` followed by `R=5,654.578'`—are slightly larger than callout text, and sit just beyond the packed label field to avoid collisions.

Overlay graphics use the MDOT ORD levels `ALI_DESIGN_ML_CURVES` (alignment), `ALI_DESIGN_ML_LABELS` (leaders), `ALI_DESIGN_ML_STA` (station text), and `ALI_DESIGN_ML_LABELS_TX` (slope and curve text), allowing project print styles to control their plotted appearance.

Those DXF layers also carry the MDOT level symbology: curves use color 55, leaders use color 10, and text uses DXF color 7 so it displays white in ORD. All use continuous style with the DXF lineweight corresponding to ORD weight 4. Overlay entities are created ByLevel.

Overlay station, slope, and curve labels use the `Engineering Regular` DXF text style backed by the MDOT workspace TrueType font file `EngineeringRegular.ttf`. The DXF includes extended TrueType family metadata so ORD does not interpret it as a missing SHX font. Text size remains controlled by the overlay export configuration.

The exporter reduces overlap automatically, but final text scale and sheet readability should still be checked in ORD / MicroStation.

### DGN / MicroStation notes

DXF is used as the handoff format because it is dependable from Python and can be referenced or imported into DGN. Native DGN civil-object generation is not part of this implementation.

Always verify in ORD / MicroStation:

- reference units
- working units
- origin / coincident placement
- rotation
- stationing assumptions
- text scale and readability

## LandXML support

The LandXML parser in [super_landxml.py](/C:/Python%20Projects/Super_Elevation_Calculator/super_landxml.py) currently supports:

- alignment name
- start station
- alignment length
- units
- line geometry
- circular arc geometry
- station equations detection
- superelevation node detection

Current first-pass limitation:

- spirals are detected and warned about, but not converted for overlay geometry

## Sign convention

The shared export/sign logic is centralized in [super_exports.py](/C:/Python%20Projects/Super_Elevation_Calculator/super_exports.py).

Current convention:

- normal crown: both lanes negative
- right-hand curve: left lane positive, right lane negative through super
- left-hand curve: left lane negative, right lane positive through super
- positive display values always show `+`

## Tests

Run:

```powershell
python -m unittest -v
```

The tests cover:

- station formatting
- sign formatting
- lane sign conventions
- normalized lane-event rows used internally by ORD and DXF exports
- ORD CSV header/mapping
- LandXML parsing
- station-to-XY conversion
- DXF export smoke coverage
