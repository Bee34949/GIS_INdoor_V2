// backend/routes/floor.js
const express = require("express");
const fs = require("fs");
const path = require("path");
const fetch = require("node-fetch");

const router = express.Router();

const USE_QDRANT = process.env.USE_QDRANT === "true";
const QDRANT_URL =
  process.env.QDRANT_URL ||
  "https://84dca8b5-df3f-4363-9c84-ec41b1dcc2a6.us-east4-0.gcp.cloud.qdrant.io"; // why: align with recent commit
const QDRANT_API_KEY = process.env.QDRANT_API_KEY;
const QDRANT_COLLECTION_NODES =
  process.env.QDRANT_COLLECTION_NODES || "indoor_nodes";

async function qdrantScroll(collection, filter) {
  // why: centralized error so ops can see real server error message
  const res = await fetch(`${QDRANT_URL}/collections/${collection}/points/scroll`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": QDRANT_API_KEY || ""
    },
    body: JSON.stringify({ filter, limit: 10_000 })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Qdrant scroll failed: ${res.status} ${res.statusText} - ${text}`);
  }
  const data = await res.json();
  return data.result?.points ?? [];
}

router.get("/:floorId/nodes", async (req, res) => {
  const floorId = parseInt(req.params.floorId, 10);
  try {
    if (USE_QDRANT) {
      if (!QDRANT_API_KEY) throw new Error("QDRANT_API_KEY not set");
      const points = await qdrantScroll(QDRANT_COLLECTION_NODES, {
        must: [{ key: "floor", match: { value: floorId } }]
      });
      const nodes = points
        .map((p) => p.payload)
        .filter((n) => n && n.id);
      return res.json(nodes);
    }

    // Fallback: local JSON
    const file = path.join(
      __dirname,
      "..",
      "..",
      "out_json",
      `floor${floorId}`,
      "nodes.json"
    );
    const raw = fs.readFileSync(file, "utf8");
    return res.json(JSON.parse(raw));
  } catch (err) {
    console.error("❌ Error loading nodes:", err.message);
    return res.status(500).json({ error: "Failed to fetch nodes", details: err.message });
  }
});

module.exports = router;
