"use client";

import { useSyncExternalStore } from "react";

const RELEASES = "https://github.com/colewinstead/Super_Elevation_Calculator/releases/latest/download";

type PreferredPlatform = "windows" | "mac" | "browser";

const subscribe = () => () => {};

function detectPlatform(): PreferredPlatform {
  const platform = `${navigator.platform} ${navigator.userAgent}`.toLowerCase();
  if (platform.includes("win")) return "windows";
  if (platform.includes("mac")) return "mac";
  return "browser";
}

export default function DownloadCards() {
  const preferred = useSyncExternalStore(subscribe, detectPlatform, () => "browser");

  return (
    <div className="download-grid">
      <article className={preferred === "windows" ? "preferred" : ""}>
        {preferred === "windows" && <span className="recommended">Recommended for this device</span>}
        <div className="platform-mark windows-mark" aria-hidden="true"><i /><i /><i /><i /></div>
        <p>WINDOWS 10 / 11 · x64</p>
        <h3>Windows</h3>
        <span>Portable desktop executable</span>
        <a className="download-button" href={`${RELEASES}/SuperElevation.exe`}>Download EXE <b>↓</b></a>
      </article>

      <article className={preferred === "mac" ? "preferred" : ""}>
        {preferred === "mac" && <span className="recommended">Recommended for this device</span>}
        <div className="platform-mark mac-mark" aria-hidden="true">●</div>
        <p>MACOS 15+ · NATIVE BUILDS</p>
        <h3>macOS</h3>
        <span>Choose your Mac processor</span>
        <div className="mac-downloads">
          <a className="download-button" href={`${RELEASES}/SuperelevationCalculator-macOS-Apple-Silicon.dmg`}>Apple Silicon <b>↓</b></a>
          <a className="download-button secondary-download" href={`${RELEASES}/SuperelevationCalculator-macOS-Intel.dmg`}>Intel <b>↓</b></a>
        </div>
      </article>

      <article className={preferred === "browser" ? "preferred" : ""}>
        {preferred === "browser" && <span className="recommended">Works on this device</span>}
        <div className="platform-mark browser-mark" aria-hidden="true"><i /></div>
        <p>MODERN DESKTOP BROWSER</p>
        <h3>Browser</h3>
        <span>No installation or account</span>
        <a className="download-button browser-button" href="/calculator">Open calculator <b>↗</b></a>
      </article>
    </div>
  );
}
