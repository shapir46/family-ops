"""Family facts from data/family.yaml."""
from functools import lru_cache

import yaml

from . import ROOT


@lru_cache
def load() -> dict:
    return yaml.safe_load((ROOT / "data/family.yaml").read_text())


def kids() -> dict:
    return load()["kids"]


def kids_for(audience: str, half_day: bool = False) -> list[str]:
    """Kids a district entry for `audience` applies to. Half days skip kids with half_days_apply: false (Lila's GSRP)."""
    out = []
    for name, k in kids().items():
        if audience not in k.get("audiences", []):
            continue
        if half_day and k.get("half_days_apply", True) is False:
            continue
        out.append(name)
    return out
