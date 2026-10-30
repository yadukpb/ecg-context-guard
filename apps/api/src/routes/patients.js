import { Router } from "express";
import { Patient } from "../models/Patient.js";
import { Segment } from "../models/Segment.js";
import { requireAuth } from "../middleware/auth.js";
import { detectorClient } from "../services/detectorClient.js";

export const patientsRouter = Router();

// Which MIT-BIH records can be assigned to a new patient — proxied from the detector
// service so the frontend never needs to know it exists.
patientsRouter.get("/meta/records", requireAuth, async (req, res, next) => {
  try {
    res.json(await detectorClient.listRecords());
  } catch (err) {
    next(err);
  }
});

patientsRouter.get("/", requireAuth, async (req, res, next) => {
  try {
    const patients = await Patient.find({ clinician: req.user.sub }).sort({ createdAt: -1 });
    res.json({ patients });
  } catch (err) {
    next(err);
  }
});

patientsRouter.post("/", requireAuth, async (req, res, next) => {
  try {
    const { name, cardiacHistory, recordId } = req.body;
    if (!name || !recordId) {
      return res.status(400).json({ error: "name and recordId are required" });
    }
    const patient = await Patient.create({
      name,
      cardiacHistory: cardiacHistory || "",
      recordId,
      clinician: req.user.sub,
    });
    res.status(201).json({ patient });
  } catch (err) {
    next(err);
  }
});

patientsRouter.get("/:id", requireAuth, async (req, res, next) => {
  try {
    const patient = await Patient.findOne({ _id: req.params.id, clinician: req.user.sub });
    if (!patient) return res.status(404).json({ error: "Patient not found" });
    res.json({ patient });
  } catch (err) {
    next(err);
  }
});

// --- Service-to-service endpoints, called by the Python detector service only. No auth:
// the detector has no concept of a logged-in clinician, it only knows patient ids Express
// gave it. See docs/building/01-architecture.md for why this is an acceptable
// simplification for a prototype running entirely on localhost.

patientsRouter.get("/:id/baseline", async (req, res, next) => {
  try {
    const patient = await Patient.findById(req.params.id);
    if (!patient) return res.status(404).json({ error: "Patient not found" });
    res.json({ baseline: patient.baseline || null });
  } catch (err) {
    next(err);
  }
});

patientsRouter.post("/:id/baseline", async (req, res, next) => {
  try {
    const patient = await Patient.findByIdAndUpdate(
      req.params.id,
      { baseline: req.body.baseline },
      { new: true }
    );
    if (!patient) return res.status(404).json({ error: "Patient not found" });
    res.json({ patient });
  } catch (err) {
    next(err);
  }
});

// --- Dashboard read endpoints

patientsRouter.get("/:id/latest", requireAuth, async (req, res, next) => {
  try {
    const patient = await Patient.findOne({ _id: req.params.id, clinician: req.user.sub });
    if (!patient) return res.status(404).json({ error: "Patient not found" });

    const segment = await Segment.findOne({ patient: patient._id }).sort({ createdAt: -1 });
    res.json({ segment });
  } catch (err) {
    next(err);
  }
});

patientsRouter.get("/:id/history", requireAuth, async (req, res, next) => {
  try {
    const patient = await Patient.findOne({ _id: req.params.id, clinician: req.user.sub });
    if (!patient) return res.status(404).json({ error: "Patient not found" });

    const limit = Math.min(Number(req.query.limit) || 50, 200);
    const segments = await Segment.find({ patient: patient._id })
      .select("-waveform") // history is for charting scores over time, not re-rendering old waveforms
      .sort({ createdAt: -1 })
      .limit(limit);
    res.json({ segments: segments.reverse() });
  } catch (err) {
    next(err);
  }
});
