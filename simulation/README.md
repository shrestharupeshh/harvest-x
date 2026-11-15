# Simulation

| What | Status | Where |
|---|---|---|
| Perception-level RGB-D scene generator | Tested | `perception/harvestx_perception/synthetic/` |
| Kinematic harvest simulation (gantry timing, geometric stem capture, state machine) | Tested in simulation | `harvesting/harvestx_harvest/`, results in `results/harvest_sim_v0/` |
| Robot digital twin (URDF/Xacro, Gazebo, MoveIt 2) | Not started | Phase 3 |

The harvest simulation does not model cutting forces, leaf deflection or damage; lettuce is
represented by a hidden stem position and the rosette geometry of the scene generator. Those
effects can only be measured on plants.
