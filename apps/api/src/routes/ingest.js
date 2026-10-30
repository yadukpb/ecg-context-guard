import { Router } from "express";
import { Patient } from "../models/Patient.js";
import { Segment } from "../models/Segment.js";
import { Alert } from "../models/Alert.js";
import { decryptBlob } from "../services/cryptoChannel.js";

export const ingestRouter = Router();

// Receives one encrypted window per tick from the detector service's streamer. No auth —
// this is the simulated secure device channel itself; the encryption/decryption IS the
// security control here, not a session cookie. See docs/building/01-architecture.md.
ingestRouter.post("/", async (req, res, next) => {
  try {
    const { patient_id: patientId, blob } = req.body;
    if (!patientId || !blob) {
      return res.status(400).json({ error: "patient_id and blob are required" });
    }

    let payload;
    try {
      payload = decryptBlob(blob);
    } catch {
      // A failed decrypt/auth-tag check means the "transmission" was corrupted or tampered
      // with in transit — distinct from a *semantic* manipulation attack, which decrypts
      // fine but contains altered-but-plausible values. We still record it as a hard reject.
      return res.status(400).json({ error: "Failed to decrypt/authenticate ingest payload" });
    }

    const patient = await Patient.findById(patientId);
    if (!patient) return res.status(404).json({ error: "Unknown patient_id" });

    const segment = await Segment.create({
      patient: patient._id,
      waveform: payload.waveform,
      features: payload.features,
      secondaryHrBpm: payload.secondary_hr_bpm,
      crossSensorSource: payload.cross_sensor_source || "synthetic",
      calibrating: !!payload.calibrating,
      calibrationProgress: payload.calibration_progress,
      calibrationTotal: payload.calibration_total,
      attackEnabled: !!payload.attack_enabled,
      attackType: payload.attack_type || "none",
      detection: payload.detection || null,
    });

    if (payload.detection && payload.detection.verdict !== "genuine") {
      await Alert.create({
        patient: patient._id,
        segment: segment._id,
        verdict: payload.detection.verdict,
        combinedScore: payload.detection.combined_score,
      });
    }

    res.status(201).json({ stored: true });
  } catch (err) {
    next(err);
  }
});
