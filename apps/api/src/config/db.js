import path from "node:path";
import { fileURLToPath } from "node:url";
import mongoose from "mongoose";
import { env } from "./env.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Persistent across restarts, so the demo account/patients survive without reseeding —
// unlike an in-memory-only MongoDB, this is a real on-disk database, just not one you had
// to install yourself. Gitignored.
const EMBEDDED_DB_PATH = path.resolve(__dirname, "../../.mongo-data");

let embeddedServer = null;

async function resolveMongoUri() {
  if (env.mongoUri) {
    return env.mongoUri;
  }

  // Lazy import: this package (and the ~100MB MongoDB binary it downloads on first use) is
  // only ever needed for local/dev use, never in production, where MONGO_URI is always set.
  const { MongoMemoryServer } = await import("mongodb-memory-server");
  const fs = await import("node:fs/promises");
  await fs.mkdir(EMBEDDED_DB_PATH, { recursive: true });
  embeddedServer = await MongoMemoryServer.create({
    instance: { dbPath: EMBEDDED_DB_PATH, storageEngine: "wiredTiger" },
  });
  const uri = `${embeddedServer.getUri()}ecg_context_guard`;
  console.log("[db] no MONGO_URI set — using a self-managed embedded MongoDB instead");
  console.log(`[db] data stored at ${EMBEDDED_DB_PATH} (persists across restarts)`);
  return uri;
}

export async function connectDb() {
  mongoose.set("strictQuery", true);
  const uri = await resolveMongoUri();
  await mongoose.connect(uri);
  console.log(`[db] connected to ${embeddedServer ? "embedded MongoDB" : uri}`);
}

export async function disconnectDb() {
  await mongoose.disconnect();
  if (embeddedServer) {
    await embeddedServer.stop();
    embeddedServer = null;
  }
}
