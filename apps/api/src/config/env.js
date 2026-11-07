import "dotenv/config";

// If MONGO_URI isn't set (the default for local/dev use), db.js starts a self-managed,
// embedded MongoDB instance instead — no Docker and no separately-installed MongoDB needed.
// Production (Render) always sets a real MONGO_URI pointing at MongoDB Atlas, so this only
// ever applies locally.
export const env = {
  port: Number(process.env.PORT || 4000),
  mongoUri: process.env.MONGO_URI || null,
  jwtSecret: process.env.JWT_SECRET || "dev-only-jwt-secret-change-me",
  transportSecret: process.env.TRANSPORT_SECRET || "dev-only-shared-secret-change-me",
  detectorBaseUrl: process.env.DETECTOR_BASE_URL || "http://localhost:8000",
  clientOrigin: process.env.CLIENT_ORIGIN || "http://localhost:5173",
};
