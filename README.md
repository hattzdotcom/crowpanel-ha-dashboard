# CrowPanel HA Dashboard

ESPHome firmware for turning an [Elecrow CrowPanel Advance 2.8"](https://www.elecrow.com/crowpanel-advance-2-8-hmi-esp32-ai-display-320x240-artificial-ips-intelligent-touchscreen.html)
(ESP32-S3, 320x240 touch IPS) into a wall/desk dashboard for Home Assistant.
Three swipeable pages, a dark red/black theme, a clock, and an idle
screensaver that turns the backlight off and wakes on touch.

## Why this exists

The board is real and well documented by Elecrow, but the *ESPHome* config
for it is not — every source I could find disagreed with at least one other
source on pins, display driver, or color order, and getting it working
involved several rounds of "flash it, it's black, why." That process is
written up below so the next person doesn't have to repeat it blind.

## Hardware

- [CrowPanel Advance 2.8" HMI](https://www.elecrow.com/crowpanel-advance-2-8-hmi-esp32-ai-display-320x240-artificial-ips-intelligent-touchscreen.html) — ESP32-S3, 8MB embedded PSRAM, 16MB flash, ST7789 display, FT6336 capacitive touch, 320x240 IPS

## What's actually correct (the hard-won part)

Two commonly-found sources for this board's ESPHome pinout are **wrong**:

- A GitHub example repo built for what turned out to be a different
  hardware revision (resistive XPT2046 touch, ILI9341 display) — its
  backlight pin conflicted with this board's PSRAM pins outright.
- Elecrow's own wiki page for this exact model, which has some correct
  info (I2C touch, backlight pin) mixed with some pins that directly
  conflict with values from Elecrow's own **factory source code** for the
  same board.

The pins and driver settings in `crowpanel-dashboard.yaml` come from
Elecrow's [factory_sourcecode/HMI2-8](https://github.com/Elecrow-RD/CrowPanel-Advance-2.8-HMI-ESP32-S3-AI-Powered-IPS-Touch-Screen-320x240)
(`LovyanGFX_Driver.h`), which is the ground truth — an Arduino/LovyanGFX
sketch Elecrow ships for this board, not a wiki page or a third party's
repo for a similar-but-different unit. Where this config still had to
diverge from that source (see below), it was solved empirically against
real hardware, not guessed.

| Thing | Value | Notes |
|---|---|---|
| Display driver | ST7789 (via `mipi_spi`, not the deprecated `ili9xxx`/`st7789v`) | Not ILI9341 - a nearby community repo assumed the wrong driver entirely |
| SPI pins | SCLK=42, MOSI=39, no MISO | Panel is write-only |
| Display CS / DC | 40 / 41 | No reset pin - not wired on this board |
| Backlight | GPIO38, PWM (`ledc`) | **Not hardwired** - it happened to be lit in every early test only because a `ledc` output was already driving it; removing that output for a "hardwired backlight" theory turned the backlight off |
| Touch chip | FT6336 (I2C, address `0x38`), via the `ft63x6` platform, not `ft5x06` | `ft5x06`'s vendor-ID register read comes back `0x0` on this chip and the driver hard-fails; `ft63x6` reads a different ID register and doesn't hard-fail even on a `0x0` read |
| Touch I2C pins | SDA=15, SCL=16, INT=47 | |
| Color order | `BGR` | LovyanGFX's `rgb_order: false` suggests RGB: it's actually BGR on real hardware - swapping red/blue if you see the wrong theme color |
| Display transform | `swap_xy: true, mirror_x: true, mirror_y: false` | Solved by photographing the screen and iterating - see below |
| Touch transform | `swap_xy: true, mirror_x: true, mirror_y: true` | Same as the display except **`mirror_y` is flipped** - confirmed by logging raw touch coordinates while tapping known screen locations; top-of-screen taps were landing on bottom-row widgets until this was corrected |

### How the transforms were actually solved

Rather than guess-and-check blind: the ESP32-S3 exposes ESPHome logs two
ways once wifi is up - `esphome logs --device <ip>` (native API, rich
component-level detail) and `esphome logs --device <serial-port>` (raw
UART, catches early boot / panics the network log can't). For the
**display** orientation, the fastest path was flashing a config with a
single static label, photographing the result, and reasoning back from
"which way is it flipped" to the transform flags. For **touch**, the fix
came from turning on `VERY_VERBOSE` logging scoped to the touch component
(`logger: logs: {FT63X6: VERY_VERBOSE}` - note: `level:` must be at least
that verbose globally too, ESPHome won't let a component log more
verbosely than the global level) and reading raw touch coordinates while
tapping specific known screen locations live.

### The other failure mode worth knowing about

Getting the *wrong* display driver (ILI9341 instead of ST7789) didn't
just fail to render - it caused ESPHome's safe-mode OTA rollback to kick
in: the device would boot, fail within ESPHome's 60-second "mark this
boot successful" window, and the bootloader would silently roll back to
the *previous* firmware on the next boot. This looked exactly like "the
new firmware never took" when actually every attempt WAS being flashed
correctly and then rolled back. If `esphome logs` shows
`OTA rollback detected!`, that's what's happening - the newly flashed
build is crashing before the 60s mark, not failing to flash.

## Setup

1. **Home Assistant**: this expects it to run natively over the ESPHome
   native API. Home Assistant needs to have added this device via
   Settings → Devices & Services → Add Integration → ESPHome (or it'll
   auto-discover it once the device is on your network and broadcasting
   via mDNS). Until HA adds it, `platform: homeassistant` entities on the
   device will just sit at their placeholder text - the device pulls
   state through HA's connection *to* it, not the other way around.

2. **Point it at your own entities.** Every entity this dashboard reads
   is a substitution at the top of `crowpanel-dashboard.yaml` - nothing
   is hardcoded past that block. Three example pages are included:
   - **Weather**: outdoor temp, precipitation, two indoor temps
   - **Device**: a mix of numeric sensors and switch on/off status
     (built against a solar charge controller, but any sensor/switch
     entities work)
   - **Custom**: two percentage sensors plus two timestamp sensors
     (built against the "Claude Usage" HACS integration, but works for
     any similar pair)

   Swap the `_entity` substitution values for your own `sensor.*` /
   `switch.*` entity IDs. Page titles, label prefixes, and units are
   plain text in the `lvgl:` section and in the `lambda:` format strings
   under `sensor:`/`binary_sensor:` - edit those directly to match
   whatever you point at.

3. **Secrets**: copy `secrets.yaml.example` to `secrets.yaml` and fill in
   your wifi credentials. `api_key` should be a random 32-byte base64
   string (`python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"`)
   and `ota_password` any random string - both are freshly generated
   per-device values, not existing secrets you need to look up.

4. **Flash**:
   ```
   pip install esphome
   esphome run crowpanel-dashboard.yaml --device COMx   # first flash, over USB
   esphome run crowpanel-dashboard.yaml --device <device-ip>  # later updates, OTA
   ```

## Customizing

- **Colors**: every `bg_color`/`text_color` in the `lvgl:` section is a
  plain hex value - the red/black theme is just `0x0D0000` background,
  `0xFF3333`/`0xE05050`/`0x803030` for primary/body/dim red text. Swap
  the palette for whatever you want.
- **Screensaver timeout**: `screensaver_idle_minutes` substitution at the
  top of the file (default 5).
- **Clock**: format string is in the `time:` component's `on_time:`
  trigger (`strftime` format, currently `"%a %m/%d  %I:%M %p"`). Timezone
  is *not* hardcoded - it's pulled from whatever timezone Home Assistant
  itself is configured with.
- **More/fewer pages**: each page is a self-contained block under
  `lvgl: pages:` with its own nav buttons; duplicate a page block to add
  one, using new `id:`s for its widgets and new `entity_id:`
  substitutions to feed it.

## License

MIT - use it, fork it, wire it to whatever board you've got.
