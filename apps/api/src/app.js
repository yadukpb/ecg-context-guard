import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import { env } from "./config/env.js";
import { authRouter } from "./routes/auth.js";
import { patientsRouter } from "./routes/patients.js";
import { ingestRouter } from "./routes/ingest.js";
import { alertsRouter } from "./routes/alerts.js";
import { controlRouter } from "./routes/control.js";
import { errorHandler } from "./middleware/errorHandler.js";

export function createApp() {
  const app = express();

  // Render (and most PaaS hosts) terminate TLS at a proxy in front of the app — without this,
  // Express sees every request as plain HTTP, so `secure: true` cookies would silently never
  // get set. Harmless locally, where there's no proxy in front at all.
  app.set("trust proxy", 1);

  app.use(cors({ origin: env.clientOrigin, credentials: true }));
  app.use(express.json({ limit: "2mb" })); // waveform arrays are small (720 floats) but give headroom
  app.use(cookieParser());

  app.get("/health", (req, res) => res.json({ status: "ok" }));

  app.use("/api/auth", authRouter);
  app.use("/api/patients", patientsRouter);
  app.use("/api/ingest", ingestRouter);
  app.use("/api/alerts", alertsRouter);
  app.use("/api/patients", controlRouter); // adds /:id/start, /:id/stop, /:id/attack, /:id/status

  app.use(errorHandler);
  return app;
}
