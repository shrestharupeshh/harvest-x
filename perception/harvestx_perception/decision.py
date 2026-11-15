"""Rule-based harvest decision baseline with explicit refusal.

This is the measurable baseline for RQ-D. A learned/adaptive policy must be compared
against it; it is not meant to be the final decision logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from .pipeline import PlantObservation

HARVEST = "HARVEST"
DEFER = "DEFER"  # not mature yet, revisit later
RESCAN = "RESCAN"  # target too uncertain, acquire another view before deciding
REJECT = "REJECT"  # unsuitable (overgrown / no usable target)


@dataclass
class DecisionConfig:
    p_ready_min: float = 0.6
    confidence_min: float = 0.7
    allow_truncated: bool = False


@dataclass
class Decision:
    action: str
    reasons: list[str]


def decide(obs: PlantObservation, cfg: DecisionConfig | None = None) -> Decision:
    cfg = cfg or DecisionConfig()
    reasons: list[str] = []
    if obs.maturity_probs is None:
        return Decision(RESCAN, ["no maturity estimate"])
    p_ready = obs.maturity_probs.get("harvest_ready", 0.0)
    if obs.maturity == "overgrown":
        return Decision(REJECT, ["classified overgrown/unsuitable"])
    if p_ready < cfg.p_ready_min:
        return Decision(DEFER, [f"P(harvest_ready)={p_ready:.2f} < {cfg.p_ready_min}"])
    if obs.cut_target_base is None:
        return Decision(RESCAN, ["no cutting target"])
    if obs.features.get("truncated", 0.0) > 0.5 and not cfg.allow_truncated:
        reasons.append("plant truncated by image border")
    if obs.confidence < cfg.confidence_min:
        reasons.append(f"target confidence {obs.confidence:.2f} < {cfg.confidence_min}")
    if reasons:
        return Decision(RESCAN, reasons)
    return Decision(HARVEST, [f"P(ready)={p_ready:.2f}", f"confidence={obs.confidence:.2f}"])
