import mongoose from "mongoose";

const baselineSchema = new mongoose.Schema(
  {
    hr_mean: Number,
    hr_std: Number,
    rr_mean: Number,
    rr_std: Number,
    amp_mean: Number,
    amp_std: Number,
    n_calibration_windows: Number,
  },
  { _id: false }
);

const patientSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    cardiacHistory: { type: String, default: "" },
    // Either a bare MIT-BIH record number ("100", ECG-only, synthetic cross-sensor) or a
    // "bidmc:NN" BIDMC record (real concurrent ECG+PPG, real cross-sensor) — the prefix is
    // how the detector service and dashboard both tell which kind a patient is.
    recordId: { type: String, required: true },
    clinician: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    baseline: { type: baselineSchema, default: null },
  },
  { timestamps: true }
);

export const Patient = mongoose.model("Patient", patientSchema);
