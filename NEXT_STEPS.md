# Next steps

Updated 2026-11-15 (session 2). Ordered by value; IDs refer to `TASKS.md`.

## Software and design work that needs no hardware

1. **Gantry detail design (T-040)** from catalogue data: linear modules, guides, closed-loop
   drives, Z brake, cable chain, guarding; then the full fixture CAD and a BOM.
2. **Wire the stem-seated sensor into the software contract (T-044)** and write the harvest
   state machine against a simulated gantry (pure Python first, ROS 2 wrapper after D-011).
3. **Head-retention and boom-stiffening design iteration (T-042)**; drawings (T-043).
4. **Experimental protocol and research proposal (T-016)**, centred on two bench experiments:
   stem scatter in the net pot, and fork-and-blade trials.
5. **Electronics architecture and firmware skeleton** with host-side tests (Phase 4).
6. **Real-data check (T-012)** as soon as the dataset can be reached.

## Physical work that only the project owner can do

Decisions have been delegated, so nothing below needs approval; it needs hands.

| # | Item | Why it matters |
|---|---|---|
| 1 | Grow one batch of butterhead in 50 mm net pots on a 100 mm NFT channel and measure stem position relative to the pot centre, stem diameter and net-pot lip height | Replaces the three assumptions that drive the end-effector geometry |
| 2 | Have the fork plate, blade and skids cut from `cad/exports/` (STEP/STL) and try them by hand on those plants | Tests the six open mechanical risks for the price of a few laser-cut parts |
| 3 | Capture overhead RGB-D images through the growth cycle | First real data for perception |
| 4 | Provide a way to reach the public lettuce dataset (allow the host in the environment, or place a copy in the repository's ignored `data/raw/`) | Unblocks T-012 |
| 5 | Provide literature database access or exported search results | Systematic review and reference verification |

## Working assumptions

Butterhead on 100 x 50 mm NFT channels, 50 mm net pots, 220 x 240 mm pitch, 300 mm clear
flank beside each channel, overhead RGB-D camera at about 0.75 m, cut plane 11 mm above the
channel, 20 mm maximum stem diameter, 0.35 MPa stem shear strength (placeholder).
