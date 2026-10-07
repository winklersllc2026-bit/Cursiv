// Builds dist/ from an allowlist of public files, then publishes to Cloudflare.
//   node publish.mjs              build + deploy
//   node publish.mjs --build-only build only (for `npx wrangler dev`)
// Only the files listed here are ever uploaded. Everything else in the repo (secrets.bat,
// family profiles, training data, .cursiv/) stays on this machine.
import { cpSync, mkdirSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { execSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..");
const dist = join(here, "dist");

// [source (relative to repo root), published name]
const PAGES = [
  ["index.html", "index.html"],
  ["system_vision.html", "vision.html"],
  ["chat.html", "chat.html"],
  ["profile.html", "profile.html"],
  ["board.html", "board.html"],
  ["mailbox.html", "mailbox.html"],
  ["start.html", "start.html"],
  ["cloudflare/letters.html", "letters.html"],
  ["cloudflare/app.html", "app.html"],
  ["cloudflare/app.webmanifest", "app.webmanifest"],
];
const FOLDERS = ["assets"];

const HEADERS = `/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), geolocation=()
`;

const ROBOTS = "User-agent: *\nDisallow: /api/\nDisallow: /remote/\n";

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

for (const [src, name] of PAGES) {
  const from = join(repo, src);
  if (!existsSync(from)) throw new Error(`Missing page: ${src}`);
  cpSync(from, join(dist, name));
}
for (const folder of FOLDERS) cpSync(join(repo, folder), join(dist, folder), { recursive: true });
writeFileSync(join(dist, "_headers"), HEADERS);
writeFileSync(join(dist, "robots.txt"), ROBOTS);

console.log(`Built dist/ with ${PAGES.length} pages + ${FOLDERS.join(", ")}`);

if (!process.argv.includes("--build-only")) {
  execSync("npx wrangler deploy", { cwd: here, stdio: "inherit" });
}
