# OpenRoads Designer Add-In Research and Handoff

**Project:** Superelevation Calculator  
**Repository:** <https://github.com/colewinstead/Super_Elevation_Calculator>  
**Research date:** July 13, 2026  
**Current assumption:** The target product is believed to be OpenRoads Designer 2025, but the complete installed version/build has not yet been confirmed.

## Purpose

This document captures the research and decisions made while evaluating how to turn the existing Python Superelevation Calculator into an OpenRoads Designer (ORD) add-in. It is intended to be sufficient handoff material for continuing development on another computer.

The desired end-state is an ORD add-in that follows the existing calculator workflow but automates the input and output steps:

1. Select an alignment in ORD.
2. Read its geometry, stationing, curves, and project units.
3. Run the existing superelevation calculations.
4. Generate LandXML, an ORD superelevation CSV, an overlay DXF, and optionally a PDF report in one operation.
5. Potentially create native ORD superelevation sections, lanes, and transitions after a preview/confirmation step.

## Current repository assessment

The existing program is a Windows desktop Python application using Tkinter. It already provides:

- MDOT-oriented superelevation calculations.
- Manual curve entry and LandXML alignment input.
- Normal crown and full-superelevation cases.
- Station equation handling.
- Lane-by-lane transition stations and signed cross slopes.
- ORD-compatible CSV output.
- Real-coordinate overlay DXF output.
- PDF calculation reports.
- Project JSON persistence.
- Optional MDOT East/West coordinate transformations.

The code is already separated well enough to support an add-in migration:

| Existing file | Responsibility | Add-in disposition |
|---|---|---|
| `Super.py` | Core criteria tables, station conversion, and calculations | Port to a testable C# core library |
| `super_lane.py` | Lane profiles and slope interpolation | Port to the C# core library |
| `super_exports.py` | Lane-event normalization and ORD CSV mapping | Port or share through golden test vectors |
| `super_landxml.py` | LandXML parsing and station-to-coordinate geometry | Replace input side with an ORD model adapter; retain/extend for file support |
| `super_dxf.py` | Detail and overlay DXF creation | Initially retain as a sidecar or port later |
| `super_pdf.py` | PDF report generation | Initially retain as a sidecar or port later |
| `super_project.py` | JSON project persistence | Retain compatibility or replace with a C# model |
| `super_app.py` | Current Tkinter interface | Replace with an ORD-hosted C# UI |

At the time of the assessment, all **35 automated tests passed** with:

```powershell
python -m unittest -v
```

The existing tests cover calculation sharing, lane signs, station formatting, station equations, LandXML parsing, coordinate transforms, ORD CSV mapping, project compatibility, and DXF generation. These tests should serve as the behavior baseline for the C# port.

## Feasibility conclusion

The requested workflow is feasible. Bentley supports managed OpenRoads add-ins written in C# or managed C++, compiled as x64 DLLs and loaded into ORD. The managed SDK provides access to the active DGN and the civil geometry model. Bentley also documents an Edit SDK with superelevation-related types, including concepts such as:

- `SuperElevationSectionEdit`
- `SuperElevationEdit`
- `SuperElevationTransitionEdit`

The exact constructors, methods, restrictions, and transaction requirements must be verified in the documentation installed with the **exact matching ORD SDK**. Public web documentation is not detailed enough to design the native writer without the installed SDK reference and examples.

## Recommended repository strategy

Use the existing repository for the prototype and initial implementation.

The add-in is another interface to the same engineering engine, so keeping both implementations together provides:

- One source of truth for calculation behavior.
- Shared fixtures and expected results.
- Easier Python-versus-C# parity testing.
- Coordinated changes to criteria, formulas, and output formats.
- Continued availability of the standalone desktop application.

Suggested structure:

```text
Super_Elevation_Calculator/
|-- Super.py
|-- super_app.py
|-- tests/
|-- shared-test-data/
|-- ord-addin/
|   |-- SuperElevation.sln
|   |-- SuperElevation.Core/
|   |-- SuperElevation.OrdAddin/
|   `-- SuperElevation.Core.Tests/
`-- docs/
```

Development should begin on a branch such as `feature/ord-addin-prototype`. The existing `main` branch and Python release should remain functional throughout the work.

A separate repository should be considered if the add-in must be private while the current repository remains public, has separate commercial ownership or release management, or Bentley licensing terms create a different publication boundary.

**Do not commit Bentley SDK assemblies, installers, credentials, or license files.** Project references should resolve against a locally installed SDK through build variables.

The repository currently has no selected open-source license. Before third-party distribution, both the project license and the Bentley SDK redistribution rules need review.

## Recommended architecture

### 1. `SuperElevation.Core`

A Bentley-independent C# class library containing:

- Station parsing and formatting.
- Station-equation conversion.
- Criteria lookup tables.
- Superelevation rate, runoff, and tangent-runout calculations.
- Lane event generation.
- Input validation and engineering warnings.
- Neutral data models for alignments, curves, lanes, and results.

This library must not reference ORD assemblies. It should be testable on any development machine.

### 2. `SuperElevation.OrdAddin`

The C# managed ORD add-in containing:

- The Bentley add-in entry point.
- `CommandTable.xml` and key-ins.
- Ribbon or workflow command registration.
- An ORD-hosted WPF or WinForms panel.
- Selection of the active civil alignment.
- ORD-specific model reading and writing.
- Configuration and deployment files.

### 3. ORD model adapter

An adapter layer should convert the selected ORD civil alignment into neutral core models. It should read:

- Alignment name and civil identity.
- Start/end station and station equations.
- Lines, circular arcs, and spirals.
- Curve direction and radius.
- Linear and angular units.
- Coordinate system/context where available.
- Existing superelevation sections, lanes, and corridors where relevant.

The calculator should not require an intermediate LandXML file internally. Reading the civil alignment directly avoids round-trip losses. LandXML should be generated as an output deliverable when requested.

### 4. Output service

A single command, tentatively named **Build Superelevation Package**, should write a predictable set of deliverables:

```text
Alignment_Name.xml
Alignment_Name_Superelevation.csv
Alignment_Name_Overlay.dxf
Alignment_Name_Report.pdf
Alignment_Name_Summary.txt
```

The user should select an output folder once. File naming, overwrite policy, and enabled deliverables should be stored in project or user settings.

### 5. Native ORD writer

The native writer would use the Edit SDK to create or update:

- A superelevation section associated with the selected alignment.
- Left and right lanes.
- Lane widths, names, and offsets.
- Pivot/crown behavior.
- Transition stations and calculated cross slopes.
- Corridor assignments, if supported and requested.

This writer should run as one ORD transaction so failure or user undo does not leave partially created civil objects.

## Proposed user workflow

The add-in can closely follow the current program:

1. User selects a horizontal alignment in ORD.
2. User opens the Superelevation Calculator panel.
3. The add-in fills alignment name, station range, curves, curve direction, radius, and station equations automatically.
4. User selects or confirms a saved design preset, such as facility type, area, speed, lane layout, crown, and feature definitions.
5. User clicks **Build Superelevation Package**.
6. The add-in calculates every eligible curve and creates the selected output files.
7. The add-in displays a compact summary of outputs, warnings, and blocked items.
8. If native authoring is enabled, the add-in presents a preview such as:

   ```text
   8 curves
   2 lanes
   47 transition points
   Section limits 100+00 to 245+50
   ```

9. User clicks **Create in ORD** to write the native civil objects.

File generation can be truly one-click. A preview/confirmation is recommended before altering the DGN because feature definitions, lane mapping, and existing civil objects can make an incorrect write expensive to repair.

## Native lane configuration requirements

An alignment alone does not contain every decision required to create lanes. The add-in needs a saved organization or project preset containing:

- Superelevation section feature definition.
- Number of lanes on each side.
- Lane width for each lane.
- Lane naming convention.
- Alignment-relative left/right mapping.
- Normal crown values.
- Pivot point and rotation behavior.
- Section limits and gap/overlap rules.
- Corridor assignment behavior.
- Rules for replacing or preserving existing superelevation objects.

After the initial preset is configured, these values can default automatically for subsequent alignments.

## LandXML considerations

There are two possible LandXML strategies:

1. Use an ORD-supported geometry export operation if the SDK exposes a reliable callable API for the target release.
2. Serialize LandXML directly from the geometry read through the ORD SDK.

The second approach is more deterministic for automation, but requires a proper writer and schema validation.

The current application parses lines and circular arcs and warns about spiral geometry. A production ORD add-in should add full spiral handling for:

- Reading the selected alignment.
- LandXML output.
- Station-to-coordinate evaluation.
- DXF geometry generation.
- Transition and curve-boundary validation.

This is an important production requirement because real roadway alignments commonly contain spirals.

## Python reuse versus a C# port

### Fast prototype

A small C# add-in could read ORD data and invoke the existing packaged Python application or a headless Python process using JSON files. This would reduce the initial calculation rewrite.

Advantages:

- Faster proof of concept.
- Immediate reuse of current calculations and exports.
- Easier parity with the existing application.

Disadvantages:

- Python runtime and dependency deployment inside an engineering environment.
- More difficult debugging across process boundaries.
- Increased IT approval and support burden.
- More complicated error handling and version management.

### Recommended production direction

Port the core engineering calculations and lane-event logic to C#. Keep the Python version as the reference implementation until parity tests pass. PDF and DXF generation may temporarily remain in a packaged sidecar, then be ported later if a single-DLL deployment is important.

## Implementation phases and rough effort

These estimates assume one developer with C# experience and some ORD SDK familiarity. SDK learning, organization-specific workspace behavior, or multi-version support can increase them.

| Phase | Outcome | Rough effort |
|---|---|---:|
| 1. SDK proof of concept | Add-in loads, command runs, selected alignment can be identified | 1-2 weeks |
| 2. Integrated read-only calculator | ORD panel reads alignment and runs calculations | 3-6 additional weeks |
| 3. One-click export package | LandXML, CSV, DXF, PDF, and summary output | 2-4 additional weeks |
| 4. Native authoring | Create/update sections, lanes, transitions, and optional corridor assignments | 4-8+ additional weeks |
| 5. Production hardening | Workspace presets, signing, installer, version testing, documentation | Depends on deployment scope |

A minimal launcher that only opens the current application from ORD could take approximately 1-2 weeks, but it would not provide the desired integration.

## Main risks and open questions

1. **Exact ORD version:** "2025" is not specific enough for SDK references. The full build number is required.
2. **SDK access:** Bentley states that the matching SDK is a separate download and access may require a valid Bentley Development Network contract plus appropriate download roles.
3. **Edit API availability:** Superelevation edit types are documented, but exact capabilities and restrictions must be confirmed from the installed version's reference.
4. **Spiral support:** The current Python geometry/export path does not fully support spirals.
5. **Feature definitions:** Native objects depend on organization workspace definitions and standards.
6. **Existing objects:** The replacement/update policy must avoid duplicate sections and unintended corridor changes.
7. **Station equations:** Civil/display station regions must remain consistent across ORD objects, CSV, LandXML, DXF, and reports.
8. **Units and coordinates:** US survey foot, international foot, coordinate systems, and DGN working units must be handled explicitly.
9. **Multi-version support:** Each target ORD release may require a separate build and validation cycle.
10. **Distribution:** Code signing, trusted add-in paths, configuration variables, and Bentley redistribution rules need to be addressed.

## What is required on the ORD development computer

### Essential

1. OpenRoads Designer installed.
2. The exact full ORD version/build from **Help > About OpenRoads Designer**.
3. The matching ORD SDK installed. Bentley documentation gives the common SDK location as:

   ```text
   C:\Program Files\Bentley\OpenRoadsDesignerCONNECTSDK
   ```

4. Visual Studio and the compiler/toolchain expected by that SDK version.
5. Access to the SDK developer shell, installed examples, reference documentation, and managed SDK example solution.
6. A sanitized test DGN containing at least one representative alignment.

### Strongly preferred test data

- One line-and-arc alignment.
- One alignment containing spirals.
- An alignment with station equations.
- A file with an existing superelevation section and lanes.
- A corridor that uses or could use the section.
- Relevant non-confidential DGN libraries, feature definitions, configuration files, and workspace dependencies.
- A known correct expected calculation/output example.
- Screenshots or documentation showing the organization's normal lane names, feature definitions, and pivot behavior.

Do not place confidential project data into the public repository. Create stripped-down fixtures or keep test projects in a separately ignored local folder.

## First tasks on the ORD computer

1. Record the full ORD version/build.
2. Confirm that the installed SDK version exactly matches the product.
3. Locate and build Bentley's managed SDK example from the SDK developer shell.
4. Load the example DLL into ORD and verify that a key-in executes.
5. Inspect the installed Geometry Model and Edit SDK documentation for:
   - Alignment selection and geometry traversal.
   - Station equations.
   - Spiral geometry.
   - Superelevation section/lane/transition read APIs.
   - Superelevation edit APIs.
   - Civil transactions, persistence, and undo.
6. Copy or create a sanitized DGN fixture.
7. Create the `feature/ord-addin-prototype` branch.
8. Scaffold the C# solution under `ord-addin/` without committing Bentley binaries.
9. Implement a proof-of-concept command that reports the selected alignment name and curve count.
10. Add golden JSON fixtures from the Python engine, then begin porting the calculation core.

## Suggested proof-of-concept acceptance criteria

The first milestone should be deliberately small:

- The add-in DLL loads successfully in the exact target ORD release.
- A command or ribbon button opens the add-in panel.
- The user can select a civil horizontal alignment.
- The add-in displays its name, station range, units, and number of curves.
- Lines, arcs, spirals, and station equations are enumerated without changing the DGN.
- The extracted neutral model can be saved as JSON for test comparison.

Only after this milestone should the project commit to the full native writer design.

## Bentley documentation consulted

- [OpenRoads Designer SDK download](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0020264)
- [How to download the matching OpenRoads Designer SDK](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0012542)
- [General SDK download access requirements](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0018646)
- [OpenRoads Designer SDK Developer Guide](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0012549)
- [Setting up managed versus unmanaged development](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0012565)
- [Developing with the Managed SDK](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0012555)
- [Installing the matching ORD SDK](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0012552)
- [Edit SDK reference overview including superelevation edit types](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0094611)
- [Superelevation feature definitions and workspace standards](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0018593)
- [LastMile Utilities as a C# ORD add-in example](https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0018872)

## Current machine status at handoff

- Repository location: `C:\Python Projects\Super_Elevation_Calculator`
- Git branch: `main`
- Remote: `https://github.com/colewinstead/Super_Elevation_Calculator`
- The repository was clean and synchronized with `origin/main` before this document was added.
- No OpenRoads Designer or matching ORD SDK installation was detected on this computer during the research.
- The user believes the eventual target is ORD 2025, but the full version/build remains unknown.
- No add-in code has been created yet.

## Recommended immediate decision

Proceed with the same repository and target the following MVP:

> Select an ORD alignment, read its geometry and stationing directly, calculate all supported curves, review the results in an ORD-hosted panel, and generate LandXML, ORD CSV, overlay DXF, and PDF outputs as one package.

Treat native creation of ORD superelevation sections and lanes as the next phase after the read-only extraction and one-click export workflow is verified against real project data.
