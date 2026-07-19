import DownloadCards from "./DownloadCards";
import OutputShowcase from "./OutputShowcase";
import commercialManifest from "./generated/commercial-manifest.json";
import criteriaProfiles from "./generated/criteria-profiles.json";
import { PRO_PRICE } from "@/lib/billing/legal";

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
          <a href="#standards">DOTs supported</a>
          <a href="#plans">Plans</a>
          <a href="#workflow">Workflow</a>
          <a href="/account">Account</a>
          <a href={`${GITHUB_REPOSITORY}/releases/latest`}>Release notes</a>
        </div>
        <a className="nav-cta" href="/calculator">Open calculator <span>↗</span></a>
      </nav>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="marketing-eyebrow"><span /> Browser-first roadway design</p>
          <h1>Professional superelevation,<br /><em>local by design.</em></h1>
          <p className="hero-lede">Start with a useful manual curve calculation for free. Add LandXML corridors, multi-curve projects, and engineering exports with Pro—all without uploading project files.</p>
          <div className="hero-actions">
            <a className="marketing-button primary-action" href="/calculator">Calculate free <span>↗</span></a>
            <a className="marketing-button secondary-action" href="#plans">Compare plans <span>↓</span></a>
          </div>
          <div className="hero-trust" aria-label="Product benefits">
            <span><i /> No account</span>
            <span><i /> Files stay local</span>
            <span><i /> Shared Python engine</span>
          </div>
        </div>

        <OutputShowcase />
      </section>

      <section className="signal-strip" aria-label="Product capabilities">
        <div><span>FREE</span><strong>Manual curve calculation</strong></div>
        <i>→</i>
        <div><span>PRO</span><strong>LandXML + project workflows</strong></div>
        <i>→</i>
        <div><span>LOCAL</span><strong>PDF · ORD CSV · DXF</strong></div>
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

      <section className="standards-section" id="standards">
        <div className="section-intro">
          <p className="marketing-eyebrow"><span /> DOTs supported</p>
          <h2>Versioned criteria profiles with visible source revisions.</h2>
          <p>Every available profile records its governing authority and source revision. The responsible project PE must independently confirm applicability and current requirements.</p>
        </div>
        <div className="standards-grid">
          {criteriaProfiles.map((profile) => {
            const abbreviation = profile.profile_id.startsWith("mdot") ? "MDOT" : "TDOT";
            const plan = profile.profile_id === commercialManifest.free_criteria_profile ? "Free" : "Pro";
            return <article key={profile.profile_id}>
              <div><span className="dot-mark">{abbreviation}</span><span className={`plan-badge ${plan.toLowerCase()}`}>{plan}</span></div>
              <h3>{profile.governing_authority}</h3>
              <p>{profile.profile_name}</p>
              <dl><dt>Recorded revision</dt><dd>{profile.revision}</dd><dt>Use requirement</dt><dd>Independent project PE verification</dd></dl>
            </article>;
          })}
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

      <section className="plans-section" id="plans">
        <div className="section-intro centered">
          <p className="marketing-eyebrow"><span /> Free and Pro</p>
          <h2>One calculator. A useful Free tier and professional Pro workflows.</h2>
          <p>Free preserves engineering correctness. Pro adds professional workflows, scale, support, and exports—not different calculations.</p>
        </div>
        <div className="plan-cards">
          <article><span>FREE</span><h3>Manual calculation</h3><p>No account required</p><strong>Available now</strong><a href="/calculator">Calculate free ↗</a></article>
          <article className="featured"><span>PRO</span><h3>Professional workflow</h3><p>Local files, projects, and exports</p><strong>{PRO_PRICE.display}</strong><a href="/account">Start Pro →</a></article>
          <article><span>TEAM</span><h3>Named-user licensing</h3><p>Pro capabilities with seat administration</p><strong>Custom pilot</strong><a href="#pilot">Book a pilot ↓</a></article>
        </div>
        <div className="comparison-wrap">
          <table className="comparison-table">
            <caption>Free, Pro, and Team capability comparison</caption>
            <thead><tr><th>Capability</th><th>Free</th><th>Pro</th><th>Team</th></tr></thead>
            <tbody>
              <tr><th>Manual MDOT single curve, results, and lane diagram</th><td>Included</td><td>Included</td><td>Included</td></tr>
              <tr><th>Source revisions and calculation provenance on screen</th><td>Included</td><td>Included</td><td>Included</td></tr>
              <tr><th>LandXML, multi-curve projects, and all supported DOT profiles</th><td>—</td><td>Included</td><td>Included</td></tr>
              <tr><th>Project files, PDF, ORD CSV, and overlay DXF</th><td>—</td><td>Included</td><td>Included</td></tr>
              <tr><th>Priority support</th><td>—</td><td>Included</td><td>Included</td></tr>
              <tr><th>Desktop edition</th><td>Coming soon</td><td>Coming soon</td><td>Coming soon</td></tr>
              <tr><th>Named-user seat administration</th><td>—</td><td>—</td><td>Included</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="pilot-section" id="pilot">
        <div><p className="marketing-eyebrow"><span /> Team program</p><h2>Book a Team pilot.</h2><p>Team pilots add named-seat administration and guided onboarding. Pro subscribers can start individually through secure Stripe Checkout.</p></div>
        <div className="pilot-status"><span>LOCAL DATA PROMISE</span><strong>No engineering-file uploads</strong><p>Accounts and billing verify identity and access only. Project files and calculations continue to stay on the customer’s device.</p></div>
      </section>

      <section className="download-section" id="downloads">
        <div className="section-intro centered">
          <p className="marketing-eyebrow"><span /> Optional offline edition</p>
          <h2>Browser first.<br />Desktop when offline work requires it.</h2>
          <p>Desktop editions are coming soon.</p>
        </div>
        <DownloadCards />
      </section>

      <section className="engineering-note">
        <span>ENGINEERING AID</span>
        <p>The licensed professional responsible for the project must independently verify criteria, inputs, stationing, coordinate systems, results, and deliverables against governing standards and project requirements.</p>
      </section>

      <footer className="marketing-footer">
        <a className="site-brand" href="#top"><span className="site-brand-mark">SE</span><span><strong>Superelevation</strong><small>Calculator</small></span></a>
        <p>Roadway calculations and CAD-ready exports.<br />Built for traceable engineering workflows.</p>
        <div><a href="/calculator">Browser app</a><a href="/account">Account</a><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href={GITHUB_REPOSITORY}>GitHub</a></div>
      </footer>
    </main>
  );
}
