import "dotenv/config";

export const env = {
  port: Number(process.env.PORT || 4000),
  mongoUri: process.env.MONGO_URI || "mongodb://localhost:27018/ecg_context_guard",
  jwtSecret: process.env.JWT_SECRET || "dev-only-jwt-secret-change-me",
  transportSecret: process.env.TRANSPORT_SECRET || "dev-only-shared-secret-change-me",
  detectorBaseUrl: process.env.DETECTOR_BASE_URL || "http://localhost:8000",
  clientOrigin: process.env.CLIENT_ORIGIN || "http://localhost:5173",
};
