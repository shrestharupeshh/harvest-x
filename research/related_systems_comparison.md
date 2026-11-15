# Related systems and studies: comparison table

Status: first pass (2026-11-15). Keys refer to [`bibliography.bib`](bibliography.bib);
V / V\* / R are the verification flags defined there. "n.r." = not retrieved in this pass
(abstract-level reading only). Performance figures use each paper's own definitions and are
**not directly comparable**.

Relevance: ★★★ directly informs a HARVEST-X design decision or baseline; ★★ method or benchmark
we will reuse; ★ context.

| # | Key | Flag | Crop / setting | Type | Mechanical configuration | Perception | Reported performance | Main limitation for our purpose | Rel. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | birrell2020vegebot | V | Iceberg lettuce, open field | Integrated robot | Arm on mobile field platform; grip + pneumatic blade; force feedback for ground detection | Overhead RGB, two CNNs (localise, classify); camera near blade | ≈91 % localisation, ≈88 % harvest success, 38 % damage (secondary summaries; verify) | Field crop, cut at ground, outer leaves discarded; high damage; not hydroponic | ★★★ |
| 2 | cui2021cutter | V\* | Hydroponic lettuce stems | Cutting mechanics | Reciprocating cutter on shear fixture / universal tester | – | Sliding-cut angle most significant; optimum reduces max shear stress 69.9 % | Bench test, no robot integration | ★★★ |
| 3 | wang2021lettuceproperties | V\* | Hydroponic lettuce | Material properties | Tensile + shear tests | – | Pulling force ≈13 N; min. mean root-cut force ≈1.4 N (from related abstract) | Cultivar- and condition-specific | ★★★ |
| 4 | ma2023grabbing | V | Hydroponic lettuce | Gripper damage study | Four-finger flexible gripper, thin-film pressure sensors | High-speed video | Grasp type changes force and injury area; min. 120.3 ± 13.6 mm² | Gripper only, no cutting, no autonomy | ★★★ |
| 5 | scarlett2025 | V\* | Lettuce, deep-water culture | System concept (thesis) | Collaborative robots, soft/magnetic end effectors | n.r. | Evaluated on a commercial hydroponic farm (figures n.r.) | Grey literature; different growing system | ★★ |
| 6 | bac2014review | V | High-value crops | Review (≈50 robots) | – | – | Mean: localisation 85 %, detachment 75 %, harvest 66 %, cycle 33 s | Pre-deep-learning | ★★★ |
| 7 | kootstra2021selective | V\* | Greenhouse / orchard / field | Review | – | – | Challenges: variation, incomplete information, safety | – | ★★ |
| 8 | zhou2022fruitrobots | V\* | Fruit | Review | – | – | Compares success, cycle time, damage | Fruit-focused | ★ |
| 9 | rajendran2023selective | V | Selective harvesting | Review (preprint) | – | – | Perception, design, planning, control overview | Preprint | ★★ |
| 10 | arad2020sweeper | V\* | Sweet pepper, greenhouse | Integrated robot | 6-DOF industrial arm on cart; cut-and-catch tool | RGB-D, eye-in-hand | 61 % (best-fit crop) / 18 % (commercial crop); 24 s cycle | Fruit with visible peduncle | ★★ |
| 11 | lehnert2017harvey | V\* | Sweet pepper, protected cropping | Integrated robot | 6-DOF arm + lift joint on differential-drive base; suction + oscillating blade | RGB-D, peduncle segmentation | 46 % unmodified / 58 % modified crop | Mobile base adds complexity; fruit crop | ★★ |
| 12 | xiong2020strawberry | V\* | Strawberry, polytunnel | Integrated robot | Arm(s) on mobile base; cable-driven gripper with internal blade | RGB-D | First-attempt 50–97.1 % depending on occlusion | Fruit crop | ★★ |
| 13 | silwal2017apple | V | Apple, orchard | Integrated robot | 7-DOF arm, under-actuated gripper | Vision-based fruit localisation | n.r. | Outdoor tree fruit | ★ |
| 14 | vanhenten2002cucumber | R | Cucumber, greenhouse | Integrated robot | 7-DOF arm on rail vehicle; thermal cutter | Stereo vision | n.r. | Historical | ★ |
| 15 | williams2019kiwifruit | R | Kiwifruit, orchard | Integrated robot | Multiple arms under canopy | Stereo + CNN | n.r. | Different crop geometry | ★ |
| 16 | zhang2020growthcnn | V | Greenhouse lettuce (3 cultivars) | Phenotyping | – | Top-view RGB, CNN regression | R² ≈0.89–0.92 for fresh/dry weight, leaf area | No harvest decision; cultivar-dependent | ★★★ |
| 17 | gang2022twostage | V | Greenhouse lettuce (AGC data) | Phenotyping | – | RGB-D, two-stage CNN | n.r. | Benchmark-specific | ★★ |
| 18 | lin2022multimodal | V | Lettuce | Phenotyping | – | RGB + depth + geometric features fusion | n.r. | No localisation | ★★ |
| 19 | hou2024maskrcnn | V\* | Lettuce | Phenotyping + harvest timing | – | Mask R-CNN (RepVGG) with trait branches | AP ≈0.87 det / 0.88 seg | RGB only; no cutting target | ★★★ |
| 20 | wang2024yoloefficientnet | V\* | Hydroponic lettuce | Status classification | – | YOLOv8n crop + EfficientNet-v2s | n.r. | Classes are health states, not maturity | ★ |
| 21 | jin2023defective | V\* | Hydroponic lettuce | Defect detection | – | Improved YOLOv5s | n.r. | Post-harvest quality | ★ |
| 22 | hu2024lettucemots | V\* | Field lettuce | Tracking/segmentation + dataset | Spraying robot, downward RGB | Instance segmentation + tracking | 1 308 frames, 314 plants, 17 562 masks | Field, no depth, no stems | ★★ |
| 23 | hemming2021agc | V\* | Greenhouse lettuce (4 cultivars) | Dataset | – | RGB-D (RealSense D415) + destructive measurements | 388 image pairs, CC BY 4.0 | Single isolated plants; no stem annotation | ★★★ |
| 24 | barth2018synthesis | V | Sweet pepper | Synthetic data method | – | Blender-rendered images + masks | 10 500 synthetic images | Different crop | ★★ |
| 25 | kabir2023verticalfarms | V\* | Vertical farms | Review | – | – | Automation listed as open issue | Broad | ★ |

## Most directly relevant, and why

1. **birrell2020vegebot** — the only field-tested integrated lettuce robot; defines the damage
   problem (38 %) that a research contribution should attack.
2. **cui2021cutter** and **wang2021lettuceproperties** — give the force scale (order 1–15 N) and
   the importance of a sliding cut; they bound actuator sizing for the end effector.
3. **ma2023grabbing** — evidence that contact location drives leaf injury; motivates stabilising
   the plant at the base/under the canopy rather than squeezing the head.
4. **hemming2021agc**, **zhang2020growthcnn**, **hou2024maskrcnn** — the maturity/biomass
   baselines and the only sizeable open RGB-D lettuce dataset with destructive ground truth.
5. **bac2014review** — the metric definitions and the "simplify the task" argument that
   justifies working in a structured CEA fixture.

## Gaps in the table

Chinese-language harvester papers (e.g. low-damage whole-plant hydroponic harvesters cited by
`cui2021cutter`), plant-factory logistics automation, and commercial systems (which publish
little) are missing. See `literature_review.md` §9.
