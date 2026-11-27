# Desktop stand

**Status: rev 3 printed, fitted and tested 2026-11-27. Good to go.**

An adjustable tabletop stand for the CrowPanel Advance 2.8" (v1.2 housing). It holds the panel in landscape. The viewing angle can be set from 45° to 90° with a friction hinge, and the base has a pocket for a ~2000 mAh pouch LiPo behind the hinge.

The model is parametric CadQuery (`stand.py`). All dimensions come from Elecrow's own STEP model, [factory repo `3D file/advance-hmi2_8-20260126.stp`](https://github.com/Elecrow-RD/CrowPanel-Advance-2.8-HMI-ESP32-S3-AI-Powered-IPS-Touch-Screen-320x240). It was re-origined to `reference/crowpanel28_v1.2_normalized.step`, which is Elecrow's model. It's gitignored, so it won't be committed (14 MB, Elecrow's IP). Re-download it if needed.

## Panel facts pulled from the STEP

| | |
|---|---|
| Housing | 83.0 × 58.5 mm. 15.9 mm deep (glass front to back cover) + 1.0 mm screw heads on the back |
| Glass | protrudes 1.2 mm in front of the bezel. Visible bezel border ≈ 6.8 mm on the sides, ~4 mm top and bottom |
| USB-C | **2 ports, both on one short edge**. Centred 18.9 mm and 39.5 mm along the 58.5 mm edge, ~10.6 mm housing openings |
| Back connectors (all face out the back) | 2× HY2.0-4P (I2C, UART1), XH2.54-4P (UART0-IN/power), **PH2.0-2P BAT (onboard LiPo charger, 3.7–4.2 V)**, SPK, module slot |
| Corner screws | 75.0 × 48.0 mm pattern (centres at x 4/79, y 5.25/53.25). M3 heads on the front, M2.5 heads on the back |
| Other side openings | the opposite short edge y 8–46 mm, and one long edge x 6.8–27.7 mm (buttons/SD). The cradle leaves windows at all of these |
| Elecrow listing | "85.4×58.5×15.5 mm", 100 g (the STEP is what's used here) |

## Parts / hardware

- `out/cradle.(stl|3mf|step)`: print it **face-down** (face plate on the bed). No supports needed. The tops of the side windows are short 2 mm bridges.
- `out/base.(stl|3mf|step)`: print it flat. No supports.
- 4× M3×12 (the stock front screws work) + 4× M3 nuts behind the PCB.
- 2× M3×10 (or ×12) hinge bolt + 2× M3 hex nut, with a washer under each bolt head.
- Optional: 4× 10 mm rubber bumpons, and a velcro tie through the base floor slots for the battery.

## How it works

- **Cradle (rev 3, 2026-11-27, current)**: a **bare-board mount**. Elecrow's plastic housing is removed. A 1.0 mm face plate has a glass-sized window (69.2×50 + 0.25 mm per side), and four 5 mm spacers (Ø6.5, with a flat on the display side) sit at the corner holes, **75 × 48 mm c/c**. Face plus spacer is 6.0 mm, matching the caliper-measured PCB-to-glass-front distance. Elecrow's STEP says 6.3 mm, so if the glass sits ~0.3 mm proud, set `SPACER_H = 5.3`. Assembly: M3 screw from the front, through the face, spacer and PCB, with an M3 nut behind the PCB. The stock M3×12 works (1 + 5 + 1.6 PCB + 2.4 nut = 10 mm). Holes are plain Ø3.4. Slot travel was dropped because the spacers fix the position.
- **Cradle (rev 2, superseded)**: a 1.2 mm face plate with a glass-sized window (69.2×50 + 0.25 mm per side). The glass protrudes 1.2 mm past the bezel, so it sits **flush** with the face. Remove the panel's 4 front corner screws, drop the panel in from the back, and screw it to the face plate through M3 rounded-rect slots (±0.4 mm horizontal / ±0.6 mm vertical travel, **75 × 48 mm c/c**, verified against the STEP and calipers). Use button-head screws or M3 washers, because the opening is 4.2 × 4.6 mm. The back stays fully open toward the battery. The short-edge windows (USB-C ×2 on one end) and the long-edge windows are mirrored, so either long edge can be the bottom.
- **Rev 1 (superseded)**: a slide-in pocket with a front lip. In practice the panel got mounted glass-through-the-back, so rev 2 makes that face the real front. The hinge stop peg is effectively flipped, so the screen faces away from the battery pocket.
- **Hinge**: the cradle lugs (5.5 mm) sit inside the base cheeks with a 0.2 mm gap. Each bolt clamps cheek to lug, and that friction holds the angle.
- **Hard stops**: a peg on each lug (5 mm from the pivot) rides a 45° arc slot in the cheek, which stops it at exactly **45° and 90°**. Rev 2 changed the peg radius, so **reprint the base too**.
- **Battery**: an open pocket in the base behind the hinge, 63 × 53 × 11 mm, hidden behind the screen. There's a cable notch toward the panel's BAT jack and a finger notch at the back.

## Checks (`python stand.py`)

Every one of these was computed against the real Elecrow model:
- panel ∩ cradle = 0 mm³
- cradle ∩ base = 0 mm³ at 45/55/65/75/90°
- panel ∩ base = 0 mm³ at all of those angles
- the centre of gravity stays 15–33 mm behind the hinge, inside a footprint that runs 79 mm behind and 22 mm in front of it

## Status / history

- [x] Rev 1 printed 2026-11-27: the panel fit glass-through-the-back, and that back opening was too small (65 mm vs 69 mm glass).
- [x] Rev 3 printed 2026-11-27: the glass window, the 5 mm spacers (`SPACER_H = 5.0`) and the 75 × 48 mm holes all fit. Tested and good to go.

Notes:
- **Battery connector**: BAT is a **JST PH 2.0 mm 2-pin** (vertical). Check the pack's polarity against the board's +/− markings before plugging it in, because pouch-LiPo PH leads aren't consistent. If yours is reversed, swap the pins in the plug housing.
- Possible improvement: if hinge friction ever isn't enough for touch use, add detent teeth on the lug/cheek faces.

## Regenerating

```
uv venv cq-venv --python 3.12 && uv pip install --python cq-venv/Scripts/python.exe cadquery matplotlib
cq-venv/Scripts/python.exe stand.py --render     # -> out/, renders/
```
Every tunable is at the top of `stand.py`: clearances, battery pocket size, angle range, and so on.
