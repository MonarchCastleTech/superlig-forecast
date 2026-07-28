import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

test("builds a repository-subpath-safe static dashboard", async () => {
  const html = await readFile(new URL("../dist/index.html", import.meta.url), "utf8");
  const assets = await readdir(new URL("../dist/assets/", import.meta.url));

  assert.match(html, /<div id="root"><\/div>/);
  assert.match(html, /\/superlig-forecast\/assets\//);
  assert.ok(assets.some((name) => name.endsWith(".js")));
  assert.ok(assets.some((name) => name.endsWith(".css")));
  await readFile(new URL("../dist/data/dashboard.json", import.meta.url));
  await readFile(new URL("../dist/brand/mct-icon.png", import.meta.url));
  await readFile(new URL("../dist/brand/superlig-forecast-logo.png", import.meta.url));
});

test("lockfile includes cross-platform optional packages required by clean CI", async () => {
  const lockfile = JSON.parse(
    await readFile(new URL("../package-lock.json", import.meta.url), "utf8"),
  );

  assert.ok(lockfile.packages["node_modules/@emnapi/core"]);
  assert.ok(lockfile.packages["node_modules/@emnapi/runtime"]);
});
