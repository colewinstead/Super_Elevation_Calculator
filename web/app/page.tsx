import Link from "next/link";
import CalculatorCards from "./CalculatorCards";
import OutputShowcase from "./OutputShowcase";
import SiteHeader from "./SiteHeader";

const GITHUB_REPOSITORY = "https://github.com/colewinstead/VeriCivil";

export default function Home() {
  return (
    <main className="platform-shell">
      <SiteHeader />
      <section className="platform-hero" id="top">
        <div className="platform-hero-copy">
          <p className="marketing-eyebrow"><span /> Roadway calculation toolkit</p>
          <h1>Roadway calculations<br /><em>you can verify.</em></h1>
          <p>VeriCivil brings focused design and construction calculators into one browser-first workspace, with visible assumptions and tested Python engines.</p>
          <div className="hero-actions"><a className="marketing-button primary-action" href="/calculators">Browse calculators <span>↗</span></a><a className="marketing-button secondary-action" href="/calculators/superelevation">Open superelevation <span>→</span></a></div>
          <div className="hero-trust"><span><i /> Files stay local</span><span><i /> Methods stay visible</span><span><i /> Engineering review required</span></div>
        </div>
        <div className="platform-hero-visual" aria-label="VeriCivil calculator toolkit overview">
          <div className="platform-grid-lines" />
          <article className="platform-visual-card primary"><span>AVAILABLE TOOL 01</span><strong>Superelevation</strong><p>Transitions · lanes · LandXML · exports</p><div><i /><i /><i /></div></article>
          <article className="platform-visual-card secondary"><span>AVAILABLE TOOL 02</span><strong>Crushed Stone Base</strong><p>Segments · volume · order tons</p><div><i /><i /><i /></div></article>
          <div className="platform-visual-axis"><span>INPUT</span><i /><span>METHOD</span><i /><span>RESULT</span></div>
        </div>
      </section>

      <section className="platform-signal-strip" aria-label="VeriCivil product principles"><div><span>LOCAL</span><strong>Calculation files stay on device</strong></div><i>→</i><div><span>VISIBLE</span><strong>Assumptions and provenance</strong></div><i>→</i><div><span>TESTED</span><strong>Shared Python engines</strong></div></section>

      <section className="platform-calculators" id="calculators">
        <div className="section-intro"><p className="marketing-eyebrow"><span /> Available calculators</p><h2>One toolkit.<br />Focused engineering workspaces.</h2><p>Open a calculator directly—no account is required for free tools.</p></div>
        <CalculatorCards />
      </section>

      <section className="platform-featured">
        <div className="platform-featured-copy"><p className="marketing-eyebrow"><span /> Featured professional workflow</p><h2>Superelevation from curve input to design review.</h2><p>The original VeriCivil application remains the professional workspace for roadway transitions, LandXML corridors, lane-by-lane QA, and CAD-ready exports.</p><a className="marketing-button secondary-action" href="/calculators/superelevation">Explore Superelevation <span>↗</span></a></div>
        <OutputShowcase />
      </section>

      <section className="platform-principles">
        <div className="section-intro"><p className="marketing-eyebrow"><span /> Built for verification</p><h2>Useful results need visible context.</h2></div>
        <div className="principle-grid"><article><span>01</span><h3>Traceable methods</h3><p>Formulas, assumptions, units, source revisions, and engine versions stay connected to results.</p></article><article><span>02</span><h3>Local processing</h3><p>Engineering calculations and project files run inside the browser instead of being uploaded to a calculation server.</p></article><article><span>03</span><h3>Focused tools</h3><p>Each calculator owns its tested Python engine while sharing a consistent VeriCivil experience.</p></article></div>
      </section>

      <section className="platform-account-callout"><div><p className="marketing-eyebrow"><span /> Superelevation Pro</p><h2>Professional project workflows remain available.</h2><p>Manage Superelevation Pro for LandXML, multi-curve projects, supported DOT profiles, PDF, ORD CSV, and overlay DXF exports.</p></div><a className="marketing-button primary-action" href="/account">Manage Superelevation Pro <span>↗</span></a></section>

      <section className="engineering-note"><span>ENGINEERING AIDS</span><p>The licensed professional responsible for the project must independently verify criteria, inputs, assumptions, stationing, coordinate systems, results, quantities, and deliverables.</p></section>
      <footer className="platform-footer"><Link className="platform-brand" href="/"><span className="platform-brand-mark">VC</span><span><strong>VeriCivil</strong><small>Roadway calculation tools</small></span></Link><p>Focused calculations with visible engineering context.</p><div><Link href="/calculators">Calculators</Link><Link href="/account">Account</Link><Link href="/terms">Terms</Link><Link href="/privacy">Privacy</Link><a href={GITHUB_REPOSITORY}>GitHub</a></div></footer>
    </main>
  );
}
