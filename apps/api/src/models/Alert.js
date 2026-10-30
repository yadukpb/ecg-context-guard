import mongoose from "mongoose";

const alertSchema = new mongoose.Schema(
  {
    patient: { type: mongoose.Schema.Types.ObjectId, ref: "Patient", required: true, index: true },
    segment: { type: mongoose.Schema.Types.ObjectId, ref: "Segment", required: true },
    verdict: { type: String, enum: ["suspicious", "manipulated"], required: true },
    combinedScore: { type: Number, required: true },
    acknowledged: { type: Boolean, default: false },
  },
  { timestamps: true }
);

alertSchema.index({ createdAt: -1 });

export const Alert = mongoose.model("Alert", alertSchema);
