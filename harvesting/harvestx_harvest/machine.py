"""Harvest state machine with a kinematic gantry model and a geometric tool model.

The machine is written against two small interfaces (``Gantry`` and ``Tool``) so the
same sequencing code can later drive real hardware through ROS 2. The simulated
implementations here model timing and stem capture only:

* ``SimGantry``: rest-to-rest trapezoidal moves with travel limits (no dynamics).
* ``SimTool``: the V-throat seats a stem if its lateral offset from the commanded
  target is within the usable half-width and the fork reaches it within its
  over-travel; the stem-seated sensor reports that. Cutting itself is NOT simulated:
  a seated, armed cut is assumed to succeed. Damage is not modelled.

Safety behaviour encoded here (requirements S-01, S-03, S-06):
* an e-stop request aborts from any state into FAULT;
* the blade never fires unless the operator-set ``cut_armed`` flag is true
  (default false -> dry run);
* with ``sensor_gate`` enabled the blade never fires unless the stem is seated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from harvestx_mech.calcs import trapezoid_time


class State(str, Enum):
    IDLE = "IDLE"
    PLAN = "PLAN"
    APPROACH = "APPROACH"
    SEAT = "SEAT"
    VERIFY_TARGET = "VERIFY_TARGET"
    CUT = "CUT"
    VERIFY = "VERIFY"
    COLLECT = "COLLECT"
    RETREAT = "RETREAT"
    LOG = "LOG"
    FAULT = "FAULT"


class Outcome(str, Enum):
    HARVESTED = "HARVESTED"
    MISSED = "MISSED"  # stem never seated; tool withdrew without cutting
    BLIND_CUT = "BLIND_CUT"  # blade fired without a seated stem (only possible without gate)
    DRY_RUN = "DRY_RUN"  # cut not armed
    UNREACHABLE = "UNREACHABLE"
    FAULT = "FAULT"


@dataclass
class HarvestConfig:
    usable_half_width: float = 0.025  # throat entry half-width minus stem radius [m]
    overtravel: float = 0.030  # how far past the commanded target the fork may advance [m]
    sensor_gate: bool = True
    max_seat_attempts: int = 3
    retry_offset: float = 0.020  # lateral shift between seat attempts [m]
    cut_armed: bool = False
    flank_standoff: float = 0.30  # descent point distance from the channel centre line [m]
    slow_zone: float = 0.15  # under-canopy distance driven at approach speed [m]
    approach_speed: float = 0.08
    clear_height: float = 0.30  # travel height above the channel [m]
    cut_time: float = 1.0
    deposit_time: float = 1.0
    tray_xy: tuple[float, float] = (0.05, 0.0)
    v_max: tuple[float, float, float] = (0.5, 0.5, 0.25)
    a_max: tuple[float, float, float] = (2.0, 2.0, 1.5)
    limits: tuple[tuple[float, float], ...] = ((-0.1, 0.9), (-0.6, 0.6), (0.0, 0.45))


class SimGantry:
    """Kinematic X-Y-Z gantry. ``move`` returns the duration of a coordinated move."""

    def __init__(self, cfg: HarvestConfig, start=(0.0, 0.0, 0.40)):
        self.cfg, self.pos, self.yaw = cfg, np.array(start, float), 0.0

    def reachable(self, p) -> bool:
        return all(lo <= v <= hi for v, (lo, hi) in zip(p, self.cfg.limits))

    def move(self, p, speed: float | None = None) -> float:
        p = np.asarray(p, float)
        if not self.reachable(p):
            raise ValueError(f"target {p.round(3)} outside travel limits")
        d = np.abs(p - self.pos)
        t = max(trapezoid_time(d[i], min(self.cfg.v_max[i], speed or np.inf), self.cfg.a_max[i])
                for i in range(3))
        self.pos = p
        return t

    def set_yaw(self, yaw: float) -> float:
        t = 0.0 if np.isclose(yaw, self.yaw) else 0.8  # fixed allowance for a 180 deg turn
        self.yaw = yaw
        return t


class SimTool:
    """Geometric capture model of the cradle fork. Knows the true stem position."""

    def __init__(self, cfg: HarvestConfig):
        self.cfg, self.seated, self.holding = cfg, False, False

    def advance(self, target_xy, true_stem_xy, approach_sign: float) -> bool:
        lateral = true_stem_xy[0] - target_xy[0]
        along = (true_stem_xy[1] - target_xy[1]) * approach_sign  # > 0: stem is further in
        self.seated = bool(abs(lateral) <= self.cfg.usable_half_width
                           and along <= self.cfg.overtravel)
        return self.seated

    def stem_seated(self) -> bool:
        return self.seated

    def cut(self) -> bool:
        self.holding = self.seated
        return self.seated

    def release(self) -> None:
        self.seated = self.holding = False


@dataclass
class HarvestRecord:
    plant_id: str
    outcome: Outcome
    states: list[str] = field(default_factory=list)
    seat_attempts: int = 0
    duration_s: float = 0.0
    verified: bool = False
    note: str = ""

    def to_dict(self) -> dict:
        return dict(plant_id=self.plant_id, outcome=self.outcome.value, states=self.states,
                    seat_attempts=self.seat_attempts, duration_s=round(self.duration_s, 3),
                    verified=self.verified, note=self.note)


class HarvestMachine:
    def __init__(self, cfg: HarvestConfig, gantry: SimGantry, tool: SimTool):
        self.cfg, self.gantry, self.tool = cfg, gantry, tool
        self.estop = False

    def harvest(self, plant_id: str, target_base, true_stem_base, channel_y: float,
                plane_z: float) -> HarvestRecord:
        """Run one harvest attempt on the plant whose cut target is ``target_base``."""
        c, rec = self.cfg, HarvestRecord(plant_id, Outcome.FAULT)
        t = 0.0

        def enter(s: State) -> bool:
            rec.states.append(s.value)
            if self.estop:
                rec.states.append(State.FAULT.value)
                rec.outcome, rec.note = Outcome.FAULT, f"e-stop in {s.value}"
                return False
            return True

        if not enter(State.PLAN):
            return rec
        sign = 1.0 if channel_y <= 0 else -1.0  # approach from the outer flank of the channel
        z_cut = plane_z  # skids ride on the channel: Z only has to touch down
        tx, ty = float(target_base[0]), float(target_base[1])
        descent = np.array([tx, channel_y - sign * c.flank_standoff, plane_z + c.clear_height])
        if not (self.gantry.reachable(descent) and self.gantry.reachable([tx, ty, z_cut])):
            rec.outcome, rec.note = Outcome.UNREACHABLE, "target outside gantry travel"
            rec.states.append(State.LOG.value)
            return rec

        try:
            if not enter(State.APPROACH):
                return rec
            t += self.gantry.set_yaw(0.0 if sign > 0 else np.pi)
            t += self.gantry.move(descent)
            t += self.gantry.move([tx, descent[1], z_cut])
            seated = False
            offsets = [0.0] + [s * k * c.retry_offset for k in range(1, c.max_seat_attempts)
                               for s in (1, -1)]
            for off in offsets[: c.max_seat_attempts]:
                if not enter(State.SEAT):
                    return rec
                rec.seat_attempts += 1
                cmd = (tx + off, ty)
                t += self.gantry.move([cmd[0], ty - sign * c.slow_zone, z_cut])
                t += self.gantry.move([cmd[0], ty, z_cut], speed=c.approach_speed)
                seated = self.tool.advance(cmd, true_stem_base[:2], sign)
                if not enter(State.VERIFY_TARGET):
                    return rec
                rec.verified = c.sensor_gate and self.tool.stem_seated()
                if seated or not c.sensor_gate:
                    break  # without a sensor the machine cannot know it missed
                t += self.gantry.move([cmd[0], ty - sign * c.slow_zone, z_cut],
                                      speed=c.approach_speed)

            if c.sensor_gate and not seated:
                rec.outcome, rec.note = Outcome.MISSED, "stem not seated; no cut"
            elif not c.cut_armed:
                rec.outcome, rec.note = Outcome.DRY_RUN, "cut not armed"
            else:
                if not enter(State.CUT):
                    return rec
                t += c.cut_time
                ok = self.tool.cut()
                if not enter(State.VERIFY):
                    return rec
                if ok:
                    if not enter(State.COLLECT):
                        return rec
                    t += self.gantry.move([self.gantry.pos[0], self.gantry.pos[1],
                                           plane_z + c.clear_height])
                    t += self.gantry.move([c.tray_xy[0], c.tray_xy[1], plane_z + c.clear_height])
                    t += c.deposit_time
                    rec.outcome = Outcome.HARVESTED
                else:
                    rec.outcome, rec.note = Outcome.BLIND_CUT, "blade fired without a seated stem"
            if rec.outcome is not Outcome.HARVESTED:
                rec.states.append(State.RETREAT.value)
                t += self.gantry.move([self.gantry.pos[0], descent[1], z_cut],
                                      speed=c.approach_speed)
                t += self.gantry.move(descent)
        except ValueError as e:  # travel-limit violation during the sequence
            rec.outcome, rec.note = Outcome.FAULT, str(e)
            rec.states.append(State.FAULT.value)
        finally:
            self.tool.release()
        rec.states.append(State.LOG.value)
        rec.duration_s = t
        return rec
