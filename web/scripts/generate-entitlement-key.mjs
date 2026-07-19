import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const destination = process.argv[2];
if (!destination) throw new Error("Provide an absolute private-key output path outside the repository.");
const absolute = resolve(destination);
await mkdir(dirname(absolute), { recursive: true });
const pair = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
const [privateJwk, publicJwk] = await Promise.all([
  crypto.subtle.exportKey("jwk", pair.privateKey),
  crypto.subtle.exportKey("jwk", pair.publicKey),
]);
await writeFile(absolute, `${JSON.stringify(privateJwk)}\n`, { encoding: "utf8", mode: 0o600, flag: "wx" });
process.stdout.write(`${JSON.stringify(publicJwk)}\n`);
