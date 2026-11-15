# System architecture

Status: v0.1 design intent (2026-11-15). Only the perception blocks marked *implemented* exist
as code today; everything else is planned. Diagrams are Mermaid sources and render on GitHub.

## 1. System overview

```mermaid
flowchart LR
  subgraph CEA["Growing fixture (NFT rack section)"]
    P[Lettuce plants<br/>site-addressed] --- CH[NFT channels + reservoir]
    ENV[Env. sensors<br/>T, RH, pH, EC, PPFD]
  end
  subgraph ROBOT["Harvesting robot (architecture A, rail-ready)"]
    CAM[Overhead RGB-D camera]
    WCAM[Wrist camera<br/>close-range verify]
    ARM[Manipulator]
    EE[End effector<br/>stabilise + cut]
    MCU[Motor / safety MCU]
  end
  subgraph COMPUTE["Main computer (ROS 2)"]
    PERC[Perception]
    DEC[Harvest decision]
    PLAN[Motion planning]
    SM[Harvest state machine]
    LOG[Experiment manager<br/>plant registry + logs]
  end
  DASH[Web dashboard]
  ESTOP((E-stop chain))

  P --> CAM --> PERC --> DEC --> SM
  WCAM --> PERC
  SM --> PLAN --> MCU --> ARM --> EE --> P
  MCU -- joint state, currents, faults --> SM
  ENV --> LOG
  SM --> LOG --> DASH
  ESTOP -. hard-wired power cut .-> MCU
  ESTOP -. status .-> SM
```

## 2. Mechanical architecture

```mermaid
flowchart TB
  FRAME[Aluminium extrusion frame<br/>levelling feet, guarding panels]
  FRAME --> RACK[Rack module<br/>2 NFT channels x 3 sites, drip tray]
  FRAME --> GANTRY[Camera + light bridge]
  FRAME --> CARR[Carriage plate<br/>fixed in v1, linear rail in v2]
  CARR --> ARMB[Arm base] --> LINKS[Links + joints<br/>kinematics TBD in Phase 2]
  LINKS --> FLANGE[Tool flange<br/>standardised bolt pattern + connector]
  FLANGE --> EE1[EE concept 1: scissor / guillotine]
  FLANGE --> EE2[EE concept 2: enclosing gripper + blade]
  FLANGE --> EE3[EE concept 3: compliant stabiliser + slicing blade]
  FRAME --> TRAY[Collection tray on load cell]
  GANTRY --> CAM[RGB-D camera] & LED[LED grow / inspection light]
```

## 3. Electrical architecture (preliminary)

```mermaid
flowchart LR
  AC[Mains] --> PSU[24 V DC supply<br/>fused] --> ESR[Safety relay / contactor]
  ES((E-stop<br/>NC, dual channel)) --> ESR
  DOOR[Guard interlock] --> ESR
  ESR -- 24 V motor bus --> DRV[Motor drivers] --> MOT[Joint motors + encoders]
  ESR -- 24 V --> EEA[End-effector actuator driver]
  PSU -- always-on --> DCDC5[5 V DC-DC] --> SBC[Main computer]
  PSU --> DCDC3[3.3 V / 5 V logic] --> MCU[Real-time MCU]
  MCU <--> DRV
  MCU <-- limit switches, encoders, current sense, load cell --> SENS[Sensors]
  MCU <-- USB / UART or CAN, framed + CRC --> SBC
  SBC <-- USB 3 --> CAM[RGB-D camera]
  ESR -- e-stop state --> MCU
```

Principles: logic power stays up when motor power is cut so the fault can be reported; the
E-stop chain is hard-wired and never depends on software; cutting-actuator power sits behind
both the safety relay and a separate software arming signal. Component selection and PCB
decisions are Phase 4 work.

## 4. Software architecture

```mermaid
flowchart TB
  subgraph hw["Hardware abstraction (ros2_control)"]
    REAL[harvest_x_hardware<br/>serial/CAN to MCU]
    SIM[harvest_x_simulation<br/>Gazebo system plugin]
  end
  DESC[harvest_x_description<br/>URDF/Xacro, frames]
  IF[harvest_x_interfaces<br/>msgs / srvs / actions]
  PERC[harvest_x_perception<br/>wraps harvestx_perception *implemented as library*]
  MAT[harvest_x_maturity]
  LOC[harvest_x_localization]
  MP[harvest_x_motion_planning<br/>MoveIt 2]
  EE[harvest_x_end_effector]
  HV[harvest_x_harvesting<br/>state machine + decision]
  EXP[harvest_x_experiment_manager<br/>plant registry, rosbag, SQLite]
  BR[harvest_x_bringup]
  DASH[dashboard<br/>web UI via rosbridge / Foxglove]

  DESC --> MP
  PERC --> MAT & LOC --> HV
  HV --> MP --> hw
  HV --> EE --> hw
  hw --> HV
  HV --> EXP --> DASH
  IF -.-> PERC & HV & MP & EE & EXP
  BR -.-> hw
```

The high-level nodes talk only to `ros2_control` interfaces and `harvest_x_interfaces`, so
simulated and real hardware are interchangeable. The Python library `harvestx_perception` is
ROS-independent by design so that it can be tested and benchmarked without a ROS installation.

## 5. Data flow

```mermaid
flowchart LR
  RGBD[RGB + depth frame] --> PLANE[Tray-plane fit]
  PLANE --> SEG[Semantic + instance segmentation]
  REG[(Plant registry<br/>site occupancy, age, cultivar)] --> SEG
  SEG --> FEAT[Per-plant features]
  FEAT --> MATM[Maturity model] --> OBS
  SEG --> STEM[Stem estimators + fixture prior] --> FUS[Fusion + sigma model] --> OBS[PlantObservation<br/>bbox, mask, centre, cut target, covariance,<br/>confidence, status]
  CAL[(Calibration<br/>intrinsics, T_base_cam, rack pose)] --> PLANE & STEM
  OBS --> DECI[Decision: HARVEST / DEFER / RESCAN / REJECT]
  DECI --> SMACH[State machine] --> TRAJ[Trajectory] --> ACT[Actuators]
  ACT --> VER[Verification view + load cell] --> OUT[(Harvest record)]
  OBS --> OUT
```

## 6. Control flow (harvest state machine)

```mermaid
stateDiagram-v2
  [*] --> IDLE
  IDLE --> SCAN: start / arm enabled
  SCAN --> DETECT
  DETECT --> CLASSIFY: plants found
  DETECT --> IDLE: none
  CLASSIFY --> LOCALIZE: ready candidate
  CLASSIFY --> NEXT_PLANT: defer / reject
  LOCALIZE --> PLAN: confidence ok
  LOCALIZE --> RESCAN: low confidence
  RESCAN --> LOCALIZE: new view (max N)
  RESCAN --> NEXT_PLANT: still uncertain -> refuse
  PLAN --> APPROACH: collision-free path
  PLAN --> NEXT_PLANT: unreachable
  APPROACH --> VERIFY_TARGET: wrist view
  VERIFY_TARGET --> STABILIZE: stem confirmed
  VERIFY_TARGET --> RETREAT: mismatch
  STABILIZE --> CUT: interlocks ok + cut armed
  CUT --> VERIFY
  VERIFY --> COLLECT: detached
  VERIFY --> RETRY: not detached (max M)
  RETRY --> CUT
  RETRY --> RETREAT: exhausted
  COLLECT --> LOG
  RETREAT --> LOG
  LOG --> NEXT_PLANT
  NEXT_PLANT --> CLASSIFY: more plants
  NEXT_PLANT --> IDLE: done
  state FAULT {
    [*] --> SAFE_STOP
    SAFE_STOP --> MANUAL_RECOVERY: operator ack
  }
  IDLE --> FAULT: e-stop / watchdog / limit
  APPROACH --> FAULT: e-stop / stall / timeout
  CUT --> FAULT: e-stop / over-current
  FAULT --> IDLE: cleared + re-homed
```

Every state has a timeout. `CUT` is reachable only when the hardware safety chain is closed,
the guard is closed and a separate "cut armed" flag has been set by the operator; that flag is
off by default and stays off during commissioning.

## 7. Coordinate frames

```mermaid
flowchart TB
  W[world / rack_frame] -->|rail_joint: fixed in A, prismatic in C| B[base_link]
  B --> J[... arm joints ...] --> F[tool_flange] --> TCP[blade_tcp]
  F --> WC[wrist_camera_optical]
  W --> C[overhead_camera_link] --> CO[overhead_camera_optical]
  W --> CHn["channel_k (k = 0..K-1)"] --> Sn["site_k_i  (net-pot hole centre, z up)"]
  W --> TR[collection_tray]
```

Conventions: SI units; REP-103 axes (x forward, y left, z up) for body frames; optical frames
x right, y down, z forward; `T_a_b` maps coordinates from `b` to `a`. The cutting plane is
`site z = cut_height` above the channel surface. Calibration products: camera intrinsics,
`T_rack_camera`, `T_rack_base`, hand-eye `T_flange_wristcam`.

## 8. Sensor and actuator interfaces (preliminary)

| Device | Measures / does | Why needed | Interface (planned) | Rate |
|---|---|---|---|---|
| Overhead RGB-D camera | Colour + depth of the rack section | Detection, maturity, coarse target | USB 3 → ROS 2 image topics | 5–30 Hz |
| Wrist RGB camera | Close view under the canopy | Verify stem before cutting (RQ-B/D) | USB → ROS 2 | 15–30 Hz |
| Joint encoders | Joint position | Closed-loop motion, repeatability | MCU timers / driver feedback | ≥ 1 kHz |
| Limit / home switches | End of travel | Homing and hard limits | MCU GPIO, NC wiring | event |
| Motor current sense | Phase/bus current | Stall and collision detection, energy per harvest | MCU ADC or driver telemetry | ≥ 1 kHz |
| Blade actuator current / force | Cutting effort | Cut detection, blade wear, RQ-C | MCU ADC | ≥ 1 kHz |
| Load cell (tray) | Harvested mass | Verification + ground truth for RQ-A | HX711-class ADC → MCU | 10–80 Hz |
| E-stop + guard interlock | Operator safety | Removes motor/blade power | Hard-wired safety relay; status to MCU | event |
| Environment sensors | Air T/RH, solution T/pH/EC, light | Growing-condition covariates | I²C/1-Wire → logger | ≤ 1 Hz |
| Joint motors + drivers | Motion | – | Step/dir or CAN (Phase 4 decision) | – |
| Blade + stabiliser actuators | Cut and hold | – | PWM/servo or DC driver via MCU | – |

Message-level definitions (`harvest_x_interfaces`) will mirror
`harvestx_perception.pipeline.PlantObservation`.
