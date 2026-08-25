#!/usr/bin/env node
// Tiny zero-dependency local proxy + static server for the EPL Score Predictor.
//
//   node proxy.js            → serves http://localhost:8080
//   node proxy.js 9000       → serves on port 9000
//
// Why this exists: the official Fantasy Premier League API does not send CORS
// headers, so a browser can't fetch it directly from the HTML file. This relays
// the two endpoints the app needs (adding a CORS header) and serves the page
// from the same origin, so everything Just Works with no build step or signup.

"use strict";
const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = Number(process.argv[2]) || 8080;
const ROOT = __dirname;

// Only these upstream paths may be proxied (no open relay).
const FPL = {
  "/fpl/bootstrap": "https://fantasy.premierleague.com/api/bootstrap-static/",
  "/fpl/fixtures":  "https://fantasy.premierleague.com/api/fixtures/"
};

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "text/javascript; charset=utf-8",
  ".css":  "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".ico":  "image/x-icon"
};

// Fetch an upstream URL and pipe the JSON back to the client.
function relay(upstream, res) {
  https.get(upstream, {
    headers: { "User-Agent": "Mozilla/5.0", "Accept": "application/json" }
  }, up => {
    if (up.statusCode !== 200) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "upstream " + up.statusCode }));
      up.resume();
      return;
    }
    res.writeHead(200, {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=60" // brief cache; refresh button forces a reload
    });
    up.pipe(res);
  }).on("error", err => {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: String(err.message || err) }));
  });
}

// Serve a static file from the app folder (path-traversal safe).
function serveStatic(urlPath, res) {
  let rel = decodeURIComponent(urlPath.split("?")[0]);
  if (rel === "/") rel = "/index.html";
  const full = path.join(ROOT, path.normalize(rel));
  if (!full.startsWith(ROOT)) { res.writeHead(403); res.end("Forbidden"); return; }
  fs.readFile(full, (err, buf) => {
    if (err) { res.writeHead(404); res.end("Not found"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(full)] || "application/octet-stream" });
    res.end(buf);
  });
}

http.createServer((req, res) => {
  const p = req.url.split("?")[0];
  if (FPL[p]) return relay(FPL[p], res);
  return serveStatic(req.url, res);
}).listen(PORT, () => {
  console.log("EPL Score Predictor running at  http://localhost:" + PORT + "/");
  console.log("Proxying FPL endpoints:", Object.keys(FPL).join(", "));
  console.log("Press Ctrl+C to stop.");
});
