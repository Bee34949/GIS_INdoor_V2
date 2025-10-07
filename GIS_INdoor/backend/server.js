// backend/server.js
const express = require("express");
const path = require("path");
const dotenv = require("dotenv");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// static frontend (same-origin; ไม่ต้องใช้ CORS)
app.use(express.static(path.join(__dirname, "../frontend")));
app.use(express.json());

// routers
const floorRoutes = require("./routes/floor");
const pathfinderRoutes = require("./routes/pathfinder");
app.use("/api/floor", floorRoutes);
app.use("/api", pathfinderRoutes);

// health
app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    useQdrant: process.env.USE_QDRANT === "true",
    qdrantUrl: process.env.QDRANT_URL || null
  });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
