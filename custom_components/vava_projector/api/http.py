from __future__ import annotations

from dataclasses import dataclass
import re

from custom_components.vava_projector.const import DEFAULT_HTTP_PORT

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


class VavaHttpClient:
    def __init__(self, session, host: str, port: int = DEFAULT_HTTP_PORT):
        self._session = session
        self._base = f"http://{host}:{port}"

    async def async_get_volume(self) -> VolumeInfo:
        async with self._session.get(
            f"{self._base}/remote/get_volume", timeout=5
        ) as resp:
            text = await resp.text()
            if resp.status != 200:
                return VolumeInfo(ok=False)
            return parse_volume_response(text)

    async def async_send_keycode(self, keycode: int) -> None:
        async with self._session.get(
            f"{self._base}/remote/keycode_control",
            params={"keycode": str(keycode)},
            timeout=5,
        ) as resp:
            resp.raise_for_status()
