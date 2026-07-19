import type { Metadata } from "next";
import { IBM_Plex_Mono, Manrope } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  weight: ["400", "500", "600"],
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "localhost";
  const protocol = requestHeaders.get("x-forwarded-proto") || (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;

  return {
    metadataBase: new URL(origin),
    title: {
      default: "Superelevation Calculator | Roadway Design Toolkit",
      template: "%s | Superelevation Calculator",
    },
    description: "Browser-first roadway superelevation calculations with local project processing, Free manual curves, and planned Pro engineering workflows.",
    openGraph: {
      type: "website",
      title: "Superelevation Calculator",
      description: "Professional superelevation, local by design.",
      images: [{ url: new URL("/og.png", origin).toString(), width: 1200, height: 630, alt: "Superelevation Calculator roadway design toolkit" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Superelevation Calculator",
      description: "Professional superelevation, local by design.",
      images: [new URL("/og.png", origin).toString()],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${manrope.variable} ${plexMono.variable}`}
      >
        {children}
      </body>
    </html>
  );
}
