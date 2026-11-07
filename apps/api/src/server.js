import { createApp } from "./app.js";
import { connectDb } from "./config/db.js";
import { env } from "./config/env.js";
import { ensureDemoData } from "./seed.js";

async function main() {
  await connectDb();
  await ensureDemoData();
  const app = createApp();
  app.listen(env.port, () => {
    console.log(`[api] listening on http://localhost:${env.port}`);
  });
}

main().catch((err) => {
  console.error("Failed to start API server:", err);
  process.exit(1);
});
