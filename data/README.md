# Data

Nothing in this directory tree except documentation is committed to Git.

| Path | Content | In Git? |
|---|---|---|
| `dataset_registry.csv` | Registry of external and internal datasets: source, licence, size, annotations, limits, how each fact was verified | yes |
| `data_collection_protocol.md` | How HARVEST-X's own plant images and measurements will be collected | yes |
| `raw/`, `processed/`, `annotations/` | Local copies of third-party data and our own captures | no (`.gitignore`) |
| `synthetic/` | Generated scenes | no; regenerate from seed |

## Rules

1. **Do not redistribute third-party datasets.** Download from the source listed in the
   registry and keep the licence file next to the data. Several entries have unverified or
   missing licences; those may be used for local experiments only after the terms are checked.
2. **Cite datasets** using the DOI/paper in the registry.
3. **Plant-level splits.** Any split file must list plant IDs (or coarser units such as
   sowing batch / tray), never individual images.
4. **Label every derived result** as simulated, estimated or measured.

## Public data: what exists and what is missing

The only sizeable, well-documented public RGB-D lettuce dataset with destructive ground truth
found so far is the 3rd Autonomous Greenhouse Challenge set (388 image pairs, CC BY 4.0). It
shows single isolated plants and has no stem or cutting-point labels. Field datasets
(LettuceMOTS) provide instance masks but no depth. No public dataset was found that shows
lettuce on a growing fixture with neighbouring plants **and** 3D stem ground truth, which is
what RQ-B needs. That is why the project (a) starts with a procedural simulator and (b) plans
its own data collection.

## Synthetic data

```bash
python -m harvestx_perception.benchmark --out perception/results/synthetic_v0
```

regenerates the scenes in memory (deterministic for a given `--seed`) and writes the report.
The generator is `perception/harvestx_perception/synthetic/`; its assumed parameters are listed
in `KNOWN_LIMITATIONS.md`. A Blender-based photorealistic generator is planned (ROADMAP,
Phase 1b) because the current renderer models geometry, not appearance.
