# VAVA Projector for Home Assistant

Local control of the original **VAVA 4K projector (VA-LT002)** (eShare firmware) from Home Assistant. No cloud required.

## Important limitations

- **The projector cannot be powered on over the network.** In standby the network stack is off, so there is nothing to send a command to. Turn it on with the physical remote or the power button. Turning on from Home Assistant is a no-op.
- **Power-off may take ~10–15 seconds** before the entity shows as off. After you send the power key, the integration waits for the projector to stop responding (shutdown grace period, default 15 s) before it reports `off`.
- There is no absolute volume control, only volume up / down steps.

## Supported devices

- VAVA 4K projector (VA-LT002) and other eShare-based devices exposing the same control ports.

## Entities

- `media_player`: power off, volume up / down, availability (on/off).
- `remote`: send navigation keys (`UP`, `DOWN`, `LEFT`, `RIGHT`, `OK`, `BACK`, `HOME`, `MENU`, `VOLUME_UP`, `VOLUME_DOWN`, `POWER`).

## Installation (HACS custom repository)

1. In Home Assistant, open **HACS**.
2. Menu (⋮) → **Custom repositories**.
3. Add this repository's URL, with category **Integration**.
4. Search for **VAVA Projector** in HACS, install it, and restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → VAVA Projector**.

### Manual install

Copy `custom_components/vava_projector` into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

Setup is through the UI. The integration can discover projectors on your LAN or you can enter the IP address manually.

Options:

| Option | Default | Description |
|---|---|---|
| HTTP port | 8000 | eShare HTTP API port |
| TCP port | 8121 | eShare control port (key events) |
| Poll interval | 10 s | How often to check the projector |
| Shutdown grace | 15 s | How long to wait after power-off before reporting `off` |

## Network ports

| Purpose | Protocol / port |
|---|---|
| Discovery | UDP **48689** |
| Control (key events) | TCP (default 8121) |
| Status / volume / HTTP key fallback | HTTP **8000** |

Home Assistant and the projector must be on the same network (UDP discovery is broadcast-based). If discovery does not find the projector, add it manually by IP.

## Troubleshooting

- **Entity is unavailable**: the projector is in standby or off. It must be powered on physically before Home Assistant can reach it.
- **Power-off seems slow**: expected, see above.
- **Discovery finds nothing**: check that UDP 48689 is not blocked and that HA is on the same VLAN, or enter the host manually.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest tests/ -v
```
