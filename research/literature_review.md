# Literature review

Status: **first pass (2026-11-15)**. Scope and limits of this pass are stated in §9; read them
before relying on any number here.

Citation keys refer to [`bibliography.bib`](bibliography.bib). Each entry there carries a
verification flag: **[V]** confirmed against a publisher/index page, **[V\*]** confirmed with a
named gap, **[R]** recalled and not yet independently checked. Quantitative results below were
taken from abstracts and index summaries, not full texts, unless noted.

## 1. Selective harvesting robotics: where the field stands

The reference point for the whole field is the review by Bac et al. `bac2014review` [V], which
surveyed about 50 harvesting-robot projects over three decades. Averaged over the projects that
reported each metric, it found localisation success 85 %, detachment success 75 %, harvest
success 66 %, fruit damage 5 %, peduncle damage 45 % and a cycle time of 33 s; it concluded that
performance had not improved over time and that none of the robots had been commercialised. It
proposed four directions: simplify the task (modify the crop/environment), enhance the robot,
define requirements and measure performance consistently, and consider implementation
requirements. Kootstra et al. `kootstra2021selective` [V\*] updated this picture across
greenhouse, orchard and open-field systems and named three persistent obstacles: variation,
incomplete information (occlusion) and safety. Later reviews (`zhou2022fruitrobots` [V\*],
`rajendran2023selective` [V]) reach similar conclusions and note that many prototypes are never
tested outside the laboratory.

Representative integrated systems, all for crops other than lettuce:

| System | Crop / setting | Reported performance | Source |
|---|---|---|---|
| SWEEPER | Sweet pepper, greenhouse | 61 % harvest success in best-fit crop conditions, 18 % in current commercial conditions; 24 s mean cycle (≈ half logistics); 262 fruits over 4 weeks | `arad2020sweeper` [V\*] |
| Harvey | Sweet pepper, protected cropping | 46 % success unmodified crop, 58 % modified crop; 6-DOF arm + lift on differential-drive base | `lehnert2017harvey` [V\*] |
| Thorvald-based picker | Strawberry, polytunnel | First-attempt success 50–97.1 % for isolated/partially surrounded fruit depending on conditions; fully surrounded fruit not pickable; gripper actively pushes obstacles aside | `xiong2020strawberry` [V\*] |
| WSU apple harvester | Apple, orchard | Design + field evaluation (figures not retrieved in this pass) | `silwal2017apple` [V] |
| Cucumber robot | Cucumber, greenhouse | Historical baseline (figures to be re-read from full text) | `vanhenten2002cucumber` [R] |

Two lessons transfer directly to HARVEST-X. First, crop and environment conditions dominate
outcomes: SWEEPER's success rate tripled when the crop was simplified. Controlled-environment
lettuce on a fixed rack is close to the best case for "simplify the task". Second, numbers from
different papers are not comparable because success, damage and cycle time are defined
differently; a project that wants to contribute must predeclare its metrics.

## 2. Lettuce harvesting

**Field iceberg (Vegebot).** Birrell et al. `birrell2020vegebot` [V] is the only peer-reviewed,
field-tested, fully integrated lettuce harvesting robot found in this pass. It combines an
overhead camera with two CNNs (localisation, then classification of harvest suitability), a
second camera near the blade, and a custom end effector that grips the head and cuts the stem
with a pneumatically driven blade, using force feedback to detect the ground and set cut height.
Secondary summaries of the paper give ≈ 91 % localisation success, ≈ 88 % harvest success and a
38 % damage rate, with a cycle time well above a human picker's; these figures must be re-read
from the full text before being quoted in a manuscript. The crop (soil-grown iceberg, cut at
ground level, outer leaves discarded) differs substantially from hydroponic loose-leaf or
butterhead lettuce.

**Hydroponic lettuce: component studies.** Work on hydroponic lettuce is fragmented into
mechanics and handling studies rather than integrated robots:

- *Physical/mechanical properties.* Wang et al. `wang2021lettuceproperties` [V\*] measured
  geometry, pulling force and root-cutting force of hydroponic lettuce for harvester design; the
  related conference abstract reports an average pulling force of about 13 N and a minimum
  average root-cutting force of about 1.4 N, decreasing with cutting speed and with lower cut
  positions.
- *Cutter geometry.* Cui et al. `cui2021cutter` [V\*] used a purpose-built shear fixture on a
  universal tester to study blade distance, sliding-cutting angle, skew angle and shearing
  angle. Sliding-cutting angle was the most significant factor and the optimised combination
  reduced maximum shearing stress by 69.9 %. This directly motivates a slicing (drawn) cut over
  a straight guillotine chop in our end-effector concepts.
- *Grasp damage.* Ma et al. `ma2023grabbing` [V] instrumented a four-finger flexible gripper
  with thin-film pressure sensors and high-speed video and showed that where fingers contact
  the head (leaf surfaces vs. the junctions between leaves) changes both grasp force and
  injured leaf area (smallest reported injury area 120.3 ± 13.6 mm²).
- *System-level concepts.* The SCARLETT work `scarlett2025` [V\*] (grey literature) targets
  deep-water-culture farms with collaborative robots and reports evaluation on a commercial
  hydroponic farm. Several patents describe hydroponic harvesting with saws or shears.

No peer-reviewed, open, integrated robot for hydroponic lettuce on NFT channels or vertical racks
was found in this pass. That is a statement about this search, not proof of absence (§9).

## 3. Lettuce perception: growth, biomass and "maturity"

Most vision work on lettuce is phenotyping, i.e. estimating growth traits, not making a harvest
decision or producing a cutting target.

- Zhang et al. `zhang2020growthcnn` [V] regressed leaf fresh weight, dry weight and leaf area
  from top-view RGB with a CNN (R² ≈ 0.89–0.92 on their test set) and observed lower accuracy
  for a curled cultivar than for flat ones: cultivar matters.
- The 3rd Autonomous Greenhouse Challenge dataset `hemming2021agc` [V\*] (388 RGB-D image pairs
  with destructively measured fresh/dry weight, height, diameter, leaf area; RealSense D415;
  CC BY 4.0) became the de-facto benchmark. Gang et al. `gang2022twostage` [V] used a two-stage
  CNN on RGB-D; Lin et al. `lin2022multimodal` [V] fused RGB, depth and geometric features.
- Hou et al. `hou2024maskrcnn` [V\*] extended Mask R-CNN (RepVGG backbone, phenotype branches)
  to estimate traits and infer optimal harvest timing from RGB (reported detection/segmentation
  AP ≈ 0.87/0.88).
- Detection-oriented work on hydroponic lettuce mostly targets health or defects rather than
  harvest readiness (`wang2024yoloefficientnet` [V\*], `jin2023defective` [V\*]). Field datasets
  such as LettuceMOTS `hu2024lettucemots` [V\*] provide instance masks over three growth stages
  for spraying robots.

Observations relevant to RQ-A: (i) "maturity" is almost always operationalised as fresh weight
or growth stage; (ii) evaluation splits are often at image level, which leaks information when
a plant is imaged repeatedly (see `hurlbert1984pseudoreplication` [R] for the general problem);
(iii) confidence calibration (`guo2017calibration` [R]) is rarely reported, yet a harvest
decision needs calibrated probabilities to support refusal.

## 4. Localising the cutting region

For fruit, the cutting point (peduncle) is usually visible, and RGB-D keypoint/segmentation
pipelines dominate (`arad2020sweeper`, `lehnert2017harvey`, `xiong2020strawberry`). For rosette
lettuce viewed from above the stem is fully occluded by the canopy. Vegebot avoids the problem
by cutting at ground level with force feedback and using vision only for head position
`birrell2020vegebot`. We found no study that (a) reports stem/cutting-point error in millimetres
for hydroponic lettuce, (b) separates a plausible target from a verified one, or (c) compares
vision against the fixture prior (the stem must emerge from a net-pot hole whose position is
known from the rack geometry). Point (c) is important: in structured CEA the fixture prior is a
strong, free baseline, and a perception contribution must be measured against it.

Supporting methods: instance segmentation (`he2017maskrcnn`, `ronneberger2015unet`,
`redmon2016yolo` [R]); classical vegetation indices (`woebbecke1995exg` [R]); camera and
hand-eye calibration (`zhang2000calibration`, `tsai1989handeye` [R]).

## 5. End effectors, soft grasping and deformable objects

Harvesting end effectors fall into grip-and-cut, cut-and-catch, suction and twist/pull families
(`bac2014review`, `kootstra2021selective`). For leafy heads the product itself is the fragile
part, so contact location and pressure matter (`ma2023grabbing`) and soft/compliant contact is
attractive (`shintake2018softgrippers` [R]). Lettuce is a deformable object; general surveys
(`sanchez2018deformable` [R]) show that accurate deformable simulation is expensive and that
most practical systems rely on compliance plus sensing instead of accurate models. We therefore
plan simplified leaf-contact models in simulation and treat damage as something only physical
experiments can measure.

## 6. Motion planning, visual servoing and software stack

Sampling-based planning (`kuffner2000rrtconnect`, `sucan2012ompl` [R]) inside ROS 2
(`macenski2022ros2` [R]) is standard in the systems of §1. Several of them report that planning
and logistics, not perception, dominate cycle time (`arad2020sweeper`). Closed-loop approaches
(`chaumette2006visualservo` [R]) and eye-in-hand re-observation are used when open-loop targets
are unreliable; `xiong2020strawberry` shows that active interaction with obstacles can raise
success. For a horizontal, known cutting plane, Cartesian straight-line approach motions are a
credible baseline against sampling-based planning.

## 7. Synthetic data and simulation

Barth et al. `barth2018synthesis` [V] rendered 10 500 synthetic pepper images in Blender and
showed that synthetic pre-training reduces annotation needs; domain randomisation
(`tobin2017domain` [R]) is the common strategy for bridging the gap. Annotated plant phenotyping
datasets (`minervini2016datasets` [R]) established rosette-plant instance/leaf segmentation
benchmarks. For lettuce, no public synthetic RGB-D harvesting dataset with stem ground truth was
found in this pass.

## 8. Vertical farming and automation context

Reviews of vertical farming technology (`kabir2023verticalfarms` [V\*]) list automation,
sensing and energy as open engineering issues. Trade and consultancy sources consistently put
labour among the largest operating costs of indoor farms, but those figures are not
peer-reviewed and are not relied on here. `kamilaris2018deep` [R] surveys deep learning in
agriculture generally.

## 9. Scope and limits of this pass

- Search was performed with a general web search tool. Publisher databases (IEEE Xplore,
  ScienceDirect, SpringerLink), DOI resolvers and Google Scholar were **not directly
  accessible** from the build environment, so coverage is incomplete and full texts were not
  read. Chinese-language agricultural-engineering journals, where much hydroponic harvester
  work appears, are under-represented.
- 19 of the bibliography's 42 entries are still **[R]**; they are classics whose details are very
  likely correct but have not been machine-checked.
- At least two relevant papers were located only as index snippets and are *not* in the
  bibliography because their metadata could not be confirmed: a hydroponic-lettuce end effector
  reporting ≈ 95 % cutting and ≈ 94 % holding success with ≈ 85 % cutting-point localisation
  accuracy, and an MDPI *Agriculture* 2024 article on depth-based lettuce height measurement
  with a lightweight YOLOv8-seg model. Finding and reading these is a tracked task (TASKS.md).
- Next pass: systematic database search with a recorded query log, full-text reading of the
  ten most relevant papers, and extraction of metric definitions into
  [`related_systems_comparison.md`](related_systems_comparison.md).
