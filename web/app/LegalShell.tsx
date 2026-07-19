import Link from "next/link";

export default function LegalShell({
  title,
  effectiveDate,
  children,
}: {
  title: string;
  effectiveDate: string;
  children: React.ReactNode;
}) {
  return (
    <main className="legal-shell">
      <nav className="legal-nav" aria-label="Legal navigation">
        <Link href="/">Superelevation Calculator</Link>
        <div><Link href="/terms">Terms</Link><Link href="/privacy">Privacy</Link><Link href="/account">Account</Link></div>
      </nav>
      <article className="legal-document">
        <header><p>Customer agreement</p><h1>{title}</h1><span>Effective {effectiveDate}</span></header>
        {children}
      </article>
    </main>
  );
}
