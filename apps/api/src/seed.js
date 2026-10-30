/**
 * Seeds one demo clinician account and one demo patient, so the review demo can log in and
 * start a stream immediately instead of registering/creating a patient live.
 *
 * Run with: npm run seed --workspace apps/api
 */
import bcrypt from "bcryptjs";
import { connectDb } from "./config/db.js";
import { User } from "./models/User.js";
import { Patient } from "./models/Patient.js";
import mongoose from "mongoose";

const DEMO_EMAIL = "demo@ecg-guard.local";
const DEMO_PASSWORD = "demo1234";

async function main() {
  await connectDb();

  let user = await User.findOne({ email: DEMO_EMAIL });
  if (!user) {
    const passwordHash = await bcrypt.hash(DEMO_PASSWORD, 10);
    user = await User.create({ email: DEMO_EMAIL, passwordHash, name: "Demo Clinician" });
    console.log(`Created demo user ${DEMO_EMAIL} / ${DEMO_PASSWORD}`);
  } else {
    console.log(`Demo user ${DEMO_EMAIL} already exists`);
  }

  const existingPatient = await Patient.findOne({ clinician: user._id, name: "Demo Patient (record 100)" });
  if (!existingPatient) {
    await Patient.create({
      name: "Demo Patient (record 100)",
      cardiacHistory: "Seeded for the review demo — MIT-BIH record 100 (normal sinus rhythm).",
      recordId: "100",
      clinician: user._id,
    });
    console.log("Created demo patient on MIT-BIH record 100");
  } else {
    console.log("Demo patient already exists");
  }

  // A second demo patient backed by a BIDMC record — real concurrent ECG+PPG, so its
  // cross-sensor check is genuine rather than the synthetic stand-in the MIT-BIH-backed
  // patient above uses. See docs/mistakes-log.md for why this patient exists.
  const existingBidmcPatient = await Patient.findOne({
    clinician: user._id,
    name: "Demo Patient (BIDMC 05, real cross-sensor)",
  });
  if (!existingBidmcPatient) {
    await Patient.create({
      name: "Demo Patient (BIDMC 05, real cross-sensor)",
      cardiacHistory:
        "Seeded to demonstrate real cross-sensor detection — BIDMC record 05, real concurrent ECG + PPG from the same patient, not a simulated second sensor.",
      recordId: "bidmc:05",
      clinician: user._id,
    });
    console.log("Created demo patient on BIDMC record 05 (real cross-sensor)");
  } else {
    console.log("BIDMC demo patient already exists");
  }

  await mongoose.disconnect();
}

main().catch((err) => {
  console.error("Seed failed:", err);
  process.exit(1);
});
