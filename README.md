# NIGHT DRIVE

An endless neon racer that runs in your terminal. One Python file, no installs.

```bash
python3 nightdrive.py
```

Needs Python 3 and a terminal of at least 80×24 (256 colours look best). macOS and Linux work out of the box; on Windows use WSL or `pip install windows-curses`.

## Controls

| Key | Action |
|---|---|
| ← → / A D | steer |
| ↑ / W | throttle |
| ↓ / S | brake |
| Space | nitro |
| F / X | fire rocket |
| B | bomb (clears the road ahead) |
| H | horn (traffic ahead moves over) |
| T | next scenery theme |
| P / R / C | pause / restart / change car |
| M / Q | mute / quit |

## Cars

| Car | Top speed | Accel | Grip | Nitro tank | Shields |
|---|---|---|---|---|---|
| VIPER | 230 km/h | 55 | 1.00 | 100 | 3 |
| BULL | 205 km/h | 75 | 1.30 | 70 | 5 |
| GHOST | 265 km/h | 42 | 0.80 | 140 | 2 |

## Pick-ups

`N` nitro · `+` shield · `R` 3 rockets · `B` bomb · `★` invincible (ram everything) · `2` double score · `Z` slow motion

## Features

- Five stages that change every 1.5 km: Neon Night, Dawn, Desert, Storm (rain and lightning), Cyber City
- Pseudo-3D road with curves, guard rails, roadside palms, pines, cacti, lamps and neon signs
- Traffic that changes lanes, trucks, near-miss combos, particles and screen shake
- Best distance saved to `~/.nightdrive_best`

Run `python3 nightdrive.py --selftest` for a headless test drive.

## License

MIT
