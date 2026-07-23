import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the forecast research dashboard", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Süper Lig Forecast Lab<\/title>/i);
  assert.match(html, /Championship race/i);
  assert.match(html, /Monte Carlo convergence/i);
  assert.match(html, /Possible standings/i);
  assert.match(html, /Position probability/i);
  assert.match(html, /17th/i);
  assert.match(html, /Table backtest/i);
  assert.match(html, /Fixture explorer/i);
  assert.match(html, /Twenty-season validation/i);
  assert.match(html, /Forecast quality only/i);
  assert.match(html, /5,000,000/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("removes the disposable starter preview", async () => {
  await assert.rejects(
    access(new URL("../app/_sites-preview", import.meta.url)),
  );
});
