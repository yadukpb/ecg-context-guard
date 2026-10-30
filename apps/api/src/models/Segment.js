import mongoose from "mongoose";

const detectionSchema = new mongoose.Schema(
  {
    baseline_deviation: Number,
    sudden_change: Number,
    temporal_score: Number,
    cross_sensor_score: Number,
    combined_score: Number,
    verdict: { type: String, enum: ["genuine", "suspicious", "manipulated"] },
  },
  { _id: false }
);

const segmentSchema = new mongoose.Schema(
  {
    patient: { type: mongoose.Schema.Types.ObjectId, ref: "Patient", required: true, index: true },
    waveform: { type: [Number], required: true },
    features: { type: mongoose.Schema.Types.Mixed, required: true },
    secondaryHrBpm: { type: Number },
    crossSensorSource: { type: String, enum: ["real_ppg", "synthetic"], default: "synthetic" },
    calibrating: { type: Boolean, default: false },
    calibrationProgress: { type: Number },
    calibrationTotal: { type: Number },
    attackEnabled: { type: Boolean, default: false },
    attackType: { type: String, default: "none" },
    detection: { type: detectionSchema, default: null },
  },
  { timestamps: true }
);

// Recent-first lookups per patient are the only query pattern this collection needs.
segmentSchema.index({ patient: 1, createdAt: -1 });

export const Segment = mongoose.model("Segment", segmentSchema);
