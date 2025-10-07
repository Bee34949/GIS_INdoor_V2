// backend/routes/pathfinder.js
const express = require("express");
const fetch = require("node-fetch");
const fs = require("fs");
const path = require("path");

const router = express.Router();

const USE_QDRANT = process.env.USE_QDRANT === "true";
const QDRANT_URL =
  process.env.QDRANT_URL ||
  "https://84dca8b5-df3f-4363-9c84-ec41b1dcc2a6.us-east4-0.gcp.cloud.qdrant.io"; // why: align with latest repo value
const QDRANT_API_KEY = process.env.QDRANT_API_KEY || "";
const QDRANT_COLLECTION_NODES =
  process.env.QDRANT_COLLECTION_NODES || "indoor_nodes";
const QDRANT_COLLECTION_EDGES =
  process.env.QDRANT_COLLECTION_EDGES || "indoor_graph";

async function qdrantScroll(collection, filter) {
  const res = await fetch(`${QDRANT_URL}/collections/${collection}/points/scroll`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": QDRANT_API_KEY
    },
    body: JSON.stringify({ filter, limit: 10000 })
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Qdrant scroll failed: ${res.status} ${res.statusText} - ${errText}`);
  }
  const data = await res.json();
  return data.result?.points ?? [];
}

function dijkstra(nodes, edges, startId, endId) {
  const distances = {};
  const prev = {};
  const unvisited = new Set(Object.keys(nodes));
  for (const id of unvisited) {
    distances[id] = Infinity;
    prev[id] = null;
  }
  distances[startId] = 0;
  while (unvisited.size > 0) {
    let current = null;
    for (const n of unvisited) {
      if (current === null || distances[n] < distances[current]) current = n;
    }
    if (current === null || distances[current] === Infinity) break;
    if (current === endId) break;
    unvisited.delete(current);
    const neighbors = edges.filter((e) => e.from === current || e.to === current);
    for (const e of neighbors) {
      const neighborId = e.from === current ? e.to : e.from;
      if (!unvisited.has(neighborId)) continue;
      const w = Number.isFinite(e.distance) ? e.distance : 1;
      const alt = distances[current] + w;
      if (alt < distances[neighborId]) {
        distances[neighborId] = alt;
        prev[neighborId] = current;
      }
    }
  }
  const path = [];
  let u = endId;
  if (prev[u] !== null || u === startId) {
    while (u) {
      path.unshift(u);
      u = prev[u];
    }
  }
  return { path, distance: distances[endId] };
}

router.get("/route", async (req, res) => {
  const startId = String(req.query.start || "").trim();
  const endId = String(req.query.end || "").trim();
  const floor = parseInt(req.query.floor || "1", 10);
  if (!startId || !endId) {
    return res.status(400).json({ error: "start and end are required" });
  }
  try {
    let nodesMap = {};
    let edges = [];
    if (USE_QDRANT) {
      if (!QDRANT_API_KEY) throw new Error("QDRANT_API_KEY not set");
      const nodePoints = await qdrantScroll(QDRANT_COLLECTION_NODES, {
        must: [{ key: "floor", match: { value: floor } }]
      });
      const edgePoints = await qdrantScroll(QDRANT_COLLECTION_EDGES, {
        must: [{ key: "floor", match: { value: floor } }]
      });
      nodePoints.forEach((p) => {
        const n = p.payload;
        if (n?.id) nodesMap[String(n.id).trim()] = n;
      });
      edges = edgePoints.map((p) => p.payload).filter((e) => e?.from && e?.to);
    } else {
      const base = path.join(__dirname, "..", "..", "out_json", `floor${floor}`);
      const nodesRaw = JSON.parse(fs.readFileSync(path.join(base, "nodes.json"), "utf8"));
      const edgesRaw = JSON.parse(fs.readFileSync(path.join(base, "edges.json"), "utf8"));
      nodesRaw.forEach((n) => (nodesMap[String(n.id).trim()] = n));
      edges = edgesRaw;
    }
    if (!nodesMap[startId] || !nodesMap[endId]) {
      return res.status(404).json({ error: "Start or end node not found" });
    }
    const result = dijkstra(nodesMap, edges, startId, endId);
    if (!result.path.length) return res.status(404).json({ error: "No path found" });
    res.json({
      start: startId,
      end: endId,
      floor,
      distance: result.distance,
      path: result.path
    });
  } catch (err) {
    console.error("❌ Error pathfinding:", err);
    res.status(500).json({ error: "Pathfinding failed", details: err.message });
  }
});

module.exports = router;
