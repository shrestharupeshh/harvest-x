# Data collection protocol (draft v0.1)

Status: draft for review before the first plants are sown. Nothing has been collected.
Physical work in this document is **not done**; it is listed in `HARDWARE_BUILD_CHECKLIST.md`.

## 1. Identity

- Every plant gets an ID at transplant: `HX-<batch>-<rack><channel><site>-<seq>`, e.g.
  `HX-B03-R1C2S4-017`. The ID is printed as a QR/ArUco tag on the net-pot collar or beside
  the site and stored in the plant registry (SQLite, schema to be frozen in
  `experiments/` before sowing).
- A plant keeps its ID if it is moved; the registry records each move with a timestamp.
- Registry fields (minimum): plant ID, cultivar, seed lot, sowing date, transplant date, batch,
  site history, removal date and reason.

## 2. Imaging sessions

- Fixed overhead RGB-D camera on the rack bridge; same exposure/white-balance preset per
  session; a grey card and a scale target in every frame.
- Each session records: timestamp, camera serial, intrinsics file hash, extrinsic calibration
  ID, lighting state (grow lights on/off, inspection light), operator.
- Frequency: once per day at a fixed time; additional views (two camera heights, ± tilt) twice
  a week to obtain viewpoint variation. Repeated images of a plant are repeated measures.
- Files: lossless PNG (RGB), 16-bit PNG depth in 0.1 mm units, JSON sidecar with the metadata
  above and the list of plant IDs in view.

## 3. Non-destructive measurements (twice a week)

Canopy diameter along and across the channel (calliper/ruler, mm), height above the channel
(mm), leaf count (leaves > 10 mm), visual notes (tip burn, bolting, disease, mechanical damage).

## 4. Destructive ground truth (at harvest)

1. Final image set, including a close oblique view of the stem.
2. Stem position: remove the canopy above the cut, place a fiducial pin in the stem centre at
   the cutting plane and image it with the calibrated overhead camera; record its position in
   the rack frame. This is the RQ-B ground truth.
3. Stem diameter at the cutting plane (calliper).
4. Fresh shoot mass (balance, 0.1 g) within 5 minutes of cutting; optional dry mass.
5. Marketable-quality grade by two raters independently, using the rubric to be fixed in
   `research/experimental_protocol.md`.

## 5. Environment log

Air temperature, relative humidity, solution temperature, pH, EC, photoperiod and light level
at canopy, at ≤ 10-minute intervals, stored with the batch ID.

## 6. Annotation

- Instance masks and stem keypoints (where visible) in COCO format; annotation guide with
  examples before labelling starts; 10 % of images double-annotated to estimate agreement.
- Maturity label is derived from measured fresh mass (primary) and from the grower grade
  (secondary); thresholds are fixed per cultivar before the test batch is harvested.

## 7. Splits and independence

- Unit of splitting: sowing batch (preferred) or plant. Never the image.
- The final test set consists of batches grown after model development stopped.
- Experimental-evaluation plants (robot trials) are never used for training.

## 8. Exclusion criteria (declared in advance)

Plants are excluded from analysis only for: death/disease before the imaging window, tag
loss with unrecoverable identity, or equipment failure during the session. Every exclusion is
logged with a reason; exclusions are reported.
