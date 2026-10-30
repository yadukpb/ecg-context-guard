import { Router } from "express";
import { Patient } from "../models/Patient.js";
import { requireAuth } from "../middleware/auth.js";
import { detectorClient } from "../services/detectorClient.js";

export const controlRouter = Router();

async function loadOwnedPatient(req, res) {
  const patient = await Patient.findOne({ _id: req.params.id, clinician: req.user.sub });
  if (!patient) {
    res.status(404).json({ error: "Patient not found" });
    return null;
  }
  return patient;
}

controlRouter.post("/:id/start", requireAuth, async (req, res, next) => {
  try {
    const patient = await loadOwnedPatient(req, res);
    if (!patient) return;
    const result = await detectorClient.startStream(patient._id.toString(), patient.recordId);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

controlRouter.post("/:id/stop", requireAuth, async (req, res, next) => {
  try {
    const patient = await loadOwnedPatient(req, res);
    if (!patient) return;
    const result = await detectorClient.stopStream(patient._id.toString());
    res.json(result);
  } catch (err) {
    next(err);
  }
});

controlRouter.post("/:id/attack", requireAuth, async (req, res, next) => {
  try {
    const patient = await loadOwnedPatient(req, res);
    if (!patient) return;
    const { enabled, attackType, intensity } = req.body;
    const result = await detectorClient.setAttack(patient._id.toString(), {
      enabled: !!enabled,
      attackType: attackType || "none",
      intensity: typeof intensity === "number" ? intensity : 0.5,
    });
    res.json(result);
  } catch (err) {
    next(err);
  }
});

controlRouter.get("/:id/status", requireAuth, async (req, res, next) => {
  try {
    const patient = await loadOwnedPatient(req, res);
    if (!patient) return;
    const result = await detectorClient.status(patient._id.toString());
    res.json(result);
  } catch (err) {
    next(err);
  }
});
