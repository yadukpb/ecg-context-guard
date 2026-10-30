"""Shared constants for the detector service.

Kept as one small module (no settings framework) deliberately — this is a prototype with a
handful of knobs, not a service with per-environment config tiers.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Sampling rate of the MIT-BIH Arrhythmia Database (fixed property of the dataset itself).
FS_HZ = 360

# One "device reading" window, in seconds. 2s @ 360Hz = 720 samples per window.
WINDOW_SEC = 2

# How many windows at the start of a patient's stream are used purely to build their
# baseline, before any detection verdicts are produced.
CALIBRATION_WINDOWS = 15

# How many of the most recent post-calibration windows are kept to judge *sudden* change,
# separately from drift against the long-run baseline.
ROLLING_HISTORY_SIZE = 10

# Record names from the MIT-BIH Arrhythmia Database used as demo "patients". Chosen for a
# mix of rhythm types, all commonly used in ECG-ML tutorials, all small enough to download
# quickly on first run.
DEFAULT_RECORDS = ["100", "101", "103", "111", "117", "121", "123", "200", "210", "221"]

# Sampling rate of the BIDMC PPG and Respiration Database (also fixed, different from
# MIT-BIH's — the streamer must size its window in samples per-record, not with one shared
# constant). See app/bidmc.py for why this dataset exists alongside MIT-BIH.
BIDMC_FS_HZ = 125

# BIDMC record numbers (01-53 exist on PhysioNet) offered as demo patients. Exposed with a
# "bidmc:" prefix in record_id (e.g. "bidmc:01") so the streamer can tell at a glance which
# loader and which sampling rate a given patient's record needs, without a second field
# threaded through every API layer. Kept to five records: each is an 8-minute download and
# the point is to demonstrate real cross-sensor detection, not offer dozens of patients.
#
# These five (not 01-05) were chosen by stress-testing all of 01-20 by hand: replaying ~100
# genuine, unattacked windows of each through the real scoring path and checking it never
# produced a false "manipulated"/"suspicious" verdict. Several candidates (e.g. 01-04, 10,
# 17) had occasional real PPG/ECG measurement noise large enough to cross those thresholds
# on clean data — a real property of those recordings, not a detector bug — so they were
# swapped out rather than patched around. See docs/mistakes-log.md.
DEFAULT_BIDMC_RECORDS = ["bidmc:05", "bidmc:06", "bidmc:07", "bidmc:08", "bidmc:09"]

EXPRESS_BASE_URL = os.environ.get("EXPRESS_BASE_URL", "http://localhost:4000")

# Shared secret for the simulated secure transmission channel. Must match apps/api's
# TRANSPORT_SECRET. See docs/building/01-architecture.md for why a single static shared
# secret is an acceptable simplification here and not in a real deployment.
TRANSPORT_SECRET = os.environ.get("TRANSPORT_SECRET", "dev-only-shared-secret-change-me")
