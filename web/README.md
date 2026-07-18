# Superelevation Calculator browser app

This interface runs the repository's shared Python calculation, LandXML, project, PDF, CSV, and DXF modules inside a Web Worker through Pyodide. Calculation inputs and project files are processed locally in the tab and are not uploaded.

## Development

Requires Python 3.11+ and Node.js 22.13+.

```bash
npm install
npm run dev
```

The `predev` and `prebuild` hooks copy the authoritative shared Python modules from the repository root into the ignored `public/python` staging directory. Do not edit staged copies.

## Verification

```bash
npm exec tsc -- --noEmit
npm run lint
npm test
```

`npm test` creates a production build, checks the rendered application shell, runs the shared calculation engine in Pyodide, verifies an approved numeric result, and generates CSV, PDF, and DXF output.

## Production build

```bash
npm run build
```

The deployable package is written to `dist`. It requires no calculation API, database, account, or project-file storage service. The host only serves the application and its runtime assets.
