# Contributing

## Ground rules

1. **No fabricated evidence.** Never commit invented measurements, citations, part numbers,
   prices or test results. Label every number as *simulated*, *estimated* or *measured*.
2. **Reproducible artefacts.** Generated files (reports, CAD exports, figures) must be
   regenerable from a committed script and configuration. Say which command produced them.
3. **Status honesty.** Use the subsystem status vocabulary in `PROJECT_STATUS.md`
   (Not started → In progress → Implemented → Tested in simulation → Tested on hardware →
   Experimentally validated) and do not skip levels.
4. **Decisions are recorded.** Any choice that constrains later work gets an entry in
   `DECISIONS.md` (decision, alternatives, reasoning, consequences, date).
5. **Safety first.** Changes that touch motion, the cutting actuator, interlocks or the
   e-stop chain need a second reviewer and an update to the safety documentation.

## Development setup

```bash
python -m venv .venv
```

```bash
. .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

```bash
ruff check perception tools tests
```

```bash
pytest
```

`pytest -m "not slow"` skips the end-to-end benchmark smoke test.

## Conventions

- SI units in code (metres, radians, seconds, kilograms); millimetres/grams only in
  human-facing reports. Frame naming `T_a_b` maps coordinates from frame `b` to frame `a`.
- Python ≥ 3.10, `ruff` clean, type hints on public functions, tests beside every new module.
- ML evaluation: split by plant or coarser unit; report cluster-bootstrap confidence intervals.
- References go into `research/bibliography.bib` with a verification flag (see file header).
- Commit messages: imperative summary line, body explaining why.

## Pull requests

Describe what changed, how it was tested (paste the command and result), which status table
rows change, and any new assumptions.
