/* eslint-disable @next/next/no-img-element -- fixed local showcase captures do not use an image optimization service */
import DownloadCards from "./DownloadCards";

const GITHUB_REPOSITORY = "https://github.com/colewinstead/Super_Elevation_Calculator";

const features = [
  {
    number: "01",
    title: "Curve calculations",
    copy: "Calculate rate, runoff, runout, transition stations, and signed lane slopes from practical roadway inputs.",
  },
  {
    number: "02",
    title: "LandXML intelligence",
    copy: "Read alignments, lines, circular arcs, units, curve direction, and station equations without rekeying geometry.",
  },
  {
    number: "03",
    title: "Lane-by-lane review",
    copy: "Inspect critical events for both lanes and look up the slope at a station—or the station for a target slope.",
  },
  {
    number: "04",
    title: "Portable projects",
    copy: "Save calculation provenance, curve collections, notes, and embedded alignment context in a reusable project file.",
  },
  {
    number: "05",
    title: "Coordinate-aware DXF",
    copy: "Create real-coordinate overlays with curve callouts, lane labels, stationing, and East/West zone transformation.",
  },
  {
    number: "06",
    title: "One shared engine",
    copy: "Use the same Python calculation and export modules on Windows, macOS, and in the browser.",
  },
];

export default function Home() {
  return (
    <main className="marketing-shell">
      <nav className="site-nav" aria-label="Primary navigation">
        <a className="site-brand" href="#top" aria-label="Superelevation Calculator home">
          <span className="site-brand-mark">SE</span>
          <span><strong>Superelevation</strong><small>Calculator</small></span>
        </a>
        <div className="site-nav-links">
          <a href="#features">Features</a>
          <a href="#workflow">Workflow</a>
          <a href="#downloads">Downloads</a>
          <a href={`${GITHUB_REPOSITORY}/releases/latest`}>Release notes</a>
        </div>
        <a className="nav-cta" href="/calculator">Open calculator <span>↗</span></a>
      </nav>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="marketing-eyebrow"><span /> Roadway design toolkit</p>
          <h1>From roadway curve<br />to <em>CAD-ready</em> deliverable.</h1>
          <p className="hero-lede">Superelevation calculations, LandXML review, station-aware lane profiles, and engineering exports—built for the way roadway designers actually work.</p>
          <div className="hero-actions">
            <a className="marketing-button primary-action" href="/calculator">Run in your browser <span>↗</span></a>
            <a className="marketing-button secondary-action" href="#downloads">Download desktop app <span>↓</span></a>
          </div>
          <div className="hero-trust" aria-label="Product benefits">
            <span><i /> No account</span>
            <span><i /> Local processing</span>
            <span><i /> Shared Python engine</span>
          </div>
        </div>

        <div className="output-showcase" aria-label="Real Superelevation Calculator outputs">
          <a className="output-card output-card-ui" href="/calculator">
            <figure>
              <div className="output-image output-image-ui">
                <img src="/showcase/calculator-ui.png" alt="Browser calculator showing the SR 82 project, curve inputs, calculated results, lane diagram, and export controls" width="1314" height="1649" />
              </div>
              <figcaption><span>Browser UI</span><strong>Calculate and review</strong><small>Open the live workspace ↗</small></figcaption>
            </figure>
          </a>
          <a className="output-card" href="/showcase/lane-profile-diagram.png" target="_blank" rel="noreferrer">
            <figure>
              <div className="output-image output-image-diagram">
                <img src="/showcase/lane-profile-diagram.png" alt="Expanded browser diagram showing left and right lane superelevation profiles for two SR 82 curves" width="1280" height="720" />
              </div>
              <figcaption><span>Lane diagram</span><strong>Station-aware profiles</strong><small>View full size ↗</small></figcaption>
            </figure>
          </a>
          <a className="output-card" href="/showcase/dxf-plan-view.png" target="_blank" rel="noreferrer">
            <figure>
              <div className="output-image output-image-dxf">
                <img src="/showcase/dxf-plan-view.png" alt="Zoomed CAD plan view of SR 82 transition callouts with the selected curve, station, side, slope, and event metadata" width="1280" height="720" />
              </div>
              <figcaption><span>Overlay DXF</span><strong>Transition callouts</strong><small>View full size ↗</small></figcaption>
            </figure>
          </a>
          <a className="output-card" href="/showcase/pdf-report.png" target="_blank" rel="noreferrer">
            <figure>
              <div className="output-image output-image-pdf">
                <img src="/showcase/pdf-report.png" alt="First page of the generated three-page SR 82 superelevation calculation PDF report" width="1224" height="1584" />
              </div>
              <figcaption><span>PDF report</span><strong>3-page design record</strong><small>View full size ↗</small></figcaption>
            </figure>
          </a>
        </div>
      </section>

      <section className="signal-strip" aria-label="Product capabilities">
        <div><span>INPUT</span><strong>LandXML + curve data</strong></div>
        <i>→</i>
        <div><span>CALCULATE</span><strong>Transitions + lane slopes</strong></div>
        <i>→</i>
        <div><span>DELIVER</span><strong>PDF · ORD CSV · DXF</strong></div>
      </section>

      <section className="product-story" id="workflow">
        <div className="story-heading">
          <p className="marketing-eyebrow"><span /> One focused workspace</p>
          <h2>Engineering context stays connected from input to export.</h2>
          <p>Keep curve geometry, calculation criteria, lane events, notes, and deliverables together instead of rebuilding the same information across disconnected tools.</p>
          <ol className="story-steps">
            <li><span>01</span><div><strong>Load or enter</strong><small>Select a LandXML alignment or key in a curve.</small></div></li>
            <li><span>02</span><div><strong>Calculate and review</strong><small>See transitions and signed slopes update automatically.</small></div></li>
            <li><span>03</span><div><strong>Export with context</strong><small>Create review-ready files from the recorded results.</small></div></li>
          </ol>
        </div>

        <dl className="story-evidence" aria-label="Output example details">
          <div><dt>02</dt><dd><strong>Calculated curves</strong><span>One recorded project set</span></dd></div>
          <div><dt>202</dt><dd><strong>CAD entities</strong><span>Rendered from the overlay DXF model</span></dd></div>
          <div><dt>03</dt><dd><strong>Report pages</strong><span>Criteria, stations, slopes, and provenance</span></dd></div>
          <p>Shown above: one real SR 82 example processed by the same shared Python engine used by the browser and desktop applications.</p>
        </dl>
      </section>

      <section className="feature-section" id="features">
        <div className="section-intro">
          <p className="marketing-eyebrow"><span /> Capability map</p>
          <h2>Purpose-built for roadway geometry—not generic math.</h2>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article key={feature.number}>
              <span>{feature.number}</span>
              <div className={`feature-icon feature-icon-${feature.number}`} aria-hidden="true"><i /><i /><i /></div>
              <h3>{feature.title}</h3>
              <p>{feature.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="export-section">
        <div>
          <p className="marketing-eyebrow"><span /> Deliverables</p>
          <h2>Move from calculation<br />to design review.</h2>
          <p>Every export uses the same recorded calculation results shown in the application.</p>
        </div>
        <div className="export-list">
          <article><span>PDF</span><div><strong>Calculation report</strong><p>Curve inputs, transition stations, lane slopes, notes, and version provenance.</p></div><b>01</b></article>
          <article><span>CSV</span><div><strong>OpenRoads handoff</strong><p>ORD-compatible lane, station, cross-slope, pivot, point, and transition fields.</p></div><b>02</b></article>
          <article><span>DXF</span><div><strong>Real-coordinate overlay</strong><p>Alignment geometry, station callouts, lane leaders, slope labels, and coordinate transforms.</p></div><b>03</b></article>
        </div>
      </section>

      <section className="privacy-section">
        <div className="privacy-rings"><span><i>LOCAL</i></span><span /><span /></div>
        <div><p className="marketing-eyebrow"><span /> Local by design</p><h2>Your project files stay on your device.</h2><p>The browser edition runs the shared Python engine inside your tab. LandXML, calculations, saved projects, and exports are processed locally—without an account or calculation server.</p></div>
        <a href="/calculator">Open private browser workspace <span>↗</span></a>
      </section>

      <section className="download-section" id="downloads">
        <div className="section-intro centered">
          <p className="marketing-eyebrow"><span /> Choose your workspace</p>
          <h2>Desktop when you want it.<br />Browser when you don’t.</h2>
          <p>Download the portable desktop application or start immediately in your browser.</p>
        </div>
        <DownloadCards />
        <div className="download-links">
          <a href={`${GITHUB_REPOSITORY}/releases/latest`}>Release notes ↗</a>
          <a href={`${GITHUB_REPOSITORY}/releases/latest`}>Checksums ↗</a>
          <a href={GITHUB_REPOSITORY}>Source code ↗</a>
        </div>
      </section>

      <section className="engineering-note">
        <span>ENGINEERING AID</span>
        <p>Validate criteria, stationing, coordinate systems, lane naming, and exported geometry against governing standards and the project design file.</p>
      </section>

      <footer className="marketing-footer">
        <a className="site-brand" href="#top"><span className="site-brand-mark">SE</span><span><strong>Superelevation</strong><small>Calculator</small></span></a>
        <p>Roadway calculations and CAD-ready exports.<br />Built for traceable engineering workflows.</p>
        <div><a href="/calculator">Browser app</a><a href="#downloads">Downloads</a><a href={GITHUB_REPOSITORY}>GitHub</a></div>
      </footer>
    </main>
  );
}
