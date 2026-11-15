# Licensing

HARVEST-X contains software, hardware designs and documentation, which are best served by
different licences (decision D-002 in `DECISIONS.md`).

| Material | Location | Licence | SPDX identifier |
|---|---|---|---|
| Software, firmware, scripts, CI | `perception/`, `tools/`, `tests/`, `firmware/`, `ros2_ws/`, `dashboard/`, `simulation/`, `.github/` | Apache License 2.0 (full text in `LICENSE`) | `Apache-2.0` |
| Hardware designs: CAD, drawings, schematics, PCB layouts | `cad/`, `electronics/` | CERN Open Hardware Licence v2, Permissive | `CERN-OHL-P-2.0` |
| Documentation, research text, figures | `docs/`, `research/`, `data/*.md`, top-level `*.md` | Creative Commons Attribution 4.0 International | `CC-BY-4.0` |

Licence texts: Apache-2.0 is included as `LICENSE`. The CERN-OHL-P v2 text
(<https://ohwr.org/cern_ohl_p_v2.txt>) and the CC BY 4.0 legal code
(<https://creativecommons.org/licenses/by/4.0/legalcode>) are referenced by URL; their full
texts will be added under `LICENSES/` when the first hardware files are committed (tracked in
`TASKS.md`).

Third-party datasets are **not** covered by these licences and are not redistributed; see
`data/dataset_registry.csv`.

Why permissive: the goal is maximum reuse by other labs and growers, and Apache-2.0 /
CERN-OHL-P both include an explicit patent grant. A reciprocal alternative (GPL /
CERN-OHL-S) was considered and rejected because it discourages adoption by commercial growers
who might otherwise contribute data.

Nothing in this repository is certified for food contact, machinery safety or any regulatory
purpose.
