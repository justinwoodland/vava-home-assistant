from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class VolumeInfo:
    ok: bool
    current: int = 0
    max: int = 100
    mute: bool = False

_KV = re.compile(r"(['\"]?)(\w+)\1\s*:\s*(['\"]?)([^,'\"}]+)\3")

def parse_volume_response(text: str) -> VolumeInfo:
    if not text or not text.strip():
        return VolumeInfo(ok=False)
    fields = {m.group(2): m.group(4).strip() for m in _KV.finditer(text)}
    if "currentVolume" not in fields:
        return VolumeInfo(ok=False)
    try:
        current = int(fields["currentVolume"])
        maximum = int(fields.get("maxVolume", "100"))
        mute = fields.get("mute", "false").lower() == "true"
    except ValueError:
        return VolumeInfo(ok=False)
    return VolumeInfo(ok=True, current=current, max=maximum, mute=mute)
