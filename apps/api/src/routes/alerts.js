import { Router } from "express";
import { Alert } from "../models/Alert.js";
import { Patient } from "../models/Patient.js";
import { requireAuth } from "../middleware/auth.js";

export const alertsRouter = Router();

alertsRouter.get("/", requireAuth, async (req, res, next) => {
  try {
    const myPatients = await Patient.find({ clinician: req.user.sub }).select("_id");
    const patientIds = myPatients.map((p) => p._id);

    const limit = Math.min(Number(req.query.limit) || 50, 200);
    const alerts = await Alert.find({ patient: { $in: patientIds } })
      .populate("patient", "name")
      .sort({ createdAt: -1 })
      .limit(limit);
    res.json({ alerts });
  } catch (err) {
    next(err);
  }
});

alertsRouter.post("/:id/acknowledge", requireAuth, async (req, res, next) => {
  try {
    const alert = await Alert.findById(req.params.id).populate("patient");
    if (!alert || alert.patient.clinician.toString() !== req.user.sub) {
      return res.status(404).json({ error: "Alert not found" });
    }
    alert.acknowledged = true;
    await alert.save();
    res.json({ alert });
  } catch (err) {
    next(err);
  }
});
