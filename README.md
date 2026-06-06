# Griffin PowerMate — Windows 11 Controller

A modern, fully‑customizable Windows 11 application for the **Griffin PowerMate** USB
knob (the original 2001 multifunction controller, discontinued in 2018). Turn, press,
double/triple‑press, long‑press, and press‑while‑turning — every interaction is
mappable, per application, through a clean GUI. The blue LED is fully driven by the app
(solid, software pulse, flash, or volume‑tracking with fade).

This project is a from‑scratch Python reimplementation inspired by Nathan Sweet's
original Java utility ([EsotericSoftware/powermate](https://github.com/EsotericSoftware/powermate)),
rebuilt with native Windows audio, a full gesture engine, per‑app profiles, a
CustomTkinter UI, and a one‑file `.exe` build. It was reverse‑engineered and verified
against real PowerMate hardware on Windows 11.

---

## Table of Contents

1. [Features](#features)
2. [Hardware & Protocol](#hardware--protocol)
3. [Quick Start](#quick-start)
4. [USB Driver Setup (Zadig)](#usb-driver-setup-zadig)
5. [Using the App](#using-the-app)
6. [Triggers](#triggers)
7. [Actions](#actions)
8. [LED Modes](#led-modes)
9. [Per‑App Profiles](#per-app-profiles)
10. [Configuration File](#configuration-file)
11. [Timing & Sensitivity](#timing--sensitivity)
12. [Building the EXE](#building-the-exe)
13. [Architecture](#architecture)
14. [Reverse‑Engineering Notes](#reverse-engineering-notes-windows--winusb)
15. [Security Considerations](#security-considerations)
16. [Testing](#testing)
17. [Troubleshooting](#troubleshooting)
18. [Project Layout](#project-layout)
19. [Changelog](#changelog)
20. [Credits & License](#credits--license)

---

## Features

- **Every knob interaction is mappable** — rotate left/right, single/double/triple
  press, long press, and press‑while‑rotating (both directions).
- **Per‑application profiles** — different bindings depending on the focused app, with
  inheritance from a `default` profile.
- **Rich action set** — system volume, mute, **microphone mute**, media transport
  (play/pause, next, previous), scroll, arbitrary **keyboard shortcuts**, **3‑step
  keyboard macros**, **launch** apps/files/URLs, and **run** shell commands.
- **Knob activity / debug panel** — a live, timestamped log of incoming knob events and
  the action each one triggers.
- **Start with Windows** — one‑click toggle to launch automatically at login.
- **Full LED control** — `off`, `solid`, software `pulse`, `flash`, and `volume`
  (brightness follows the system volume, then fades).
- **Modern GUI** (CustomTkinter) — profile sidebar with a running‑app picker, a
  trigger→action grid with a "record shortcut" capture field, an LED panel with a live
  test button, and a timing panel.
- **System tray** — runs quietly in the background; pause/resume; settings; quit.
- **Live config reload** — edit `config.json` by hand and changes apply within ~1s.
- **Single‑file executable** — `PowerMate.exe` bundles Python, all dependencies, and the
  native `libusb` DLL. No Python install required on the target machine.

---

## Hardware & Protocol

| Property | Value |
|---|---|
| USB Vendor ID | `0x077D` |
| USB Product ID | `0x0410` |
| Interface | 0 (HID class, but driven via libusb/WinUSB) |
| Input endpoint | `0x81` — 6‑byte interrupt reports |
| Output endpoint | `0x02` — 1‑byte interrupt (LED brightness) |

**Input report (endpoint `0x81`, 6 bytes):**

| Byte | Meaning |
|---|---|
| `0` | Button state — bit 0 set = pressed |
| `1` | Relative rotation delta, **signed** (`+` clockwise, `−` counter‑clockwise) |
| `2–5` | Status/reserved (unused by this app) |

**LED brightness (endpoint `0x02`):** a single interrupt‑OUT byte, `0`–`255`. This is the
method this app uses on Windows — see [Reverse‑Engineering Notes](#reverse-engineering-notes-windows--winusb)
for why the vendor *control* transfer is deliberately avoided there.

When polled slowly during a fast spin, the device coalesces rotation into a single larger
delta (e.g. `+15`), so the gesture engine accumulates deltas rather than assuming one
detent per packet.

---

## Quick Start

### Option A — Run the prebuilt EXE (end users)

1. Install the **WinUSB** driver on the PowerMate with Zadig — see
   [USB Driver Setup](#usb-driver-setup-zadig). *(One time.)*
2. Download / copy **`PowerMate.exe`** and double‑click it.
3. A tray icon appears. Turn the knob — your system volume changes. Right‑click the tray
   icon → **Settings** to customize.

### Option B — Run from source (developers)

```powershell
# 1. Python 3.11+ (64-bit). 3.14 is tested.
python --version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the WinUSB driver via Zadig (see below)

# 4. Run
python main.py
```

---

## USB Driver Setup (Zadig)

By default Windows binds the PowerMate to the generic **HID** driver, which does **not**
allow the low‑level USB access this app needs. You must rebind it to **WinUSB** once.

1. Download **Zadig**: <https://zadig.akeo.ie/> (portable, no install).
2. Plug in the PowerMate.
3. In Zadig: **Options → List All Devices**.
4. In the dropdown, select **Griffin PowerMate** (it shows `077D 0410`).
5. Choose **WinUSB** as the replacement driver (the box to the right of the green arrow).
6. Click **Replace Driver** and wait. A completion dialog — or a harmless error — is normal.

> **Reversible:** This dedicates the knob to this app (it stops acting as a generic HID
> device, so the old Griffin software won't see it). To undo: Device Manager → the
> PowerMate → **Driver → Roll Back Driver** (or uninstall the device and replug).

> **Why not libusb‑win32?** This app uses the modern **libusb‑1.0** backend, which works
> best with the **WinUSB** driver. `libusb-win32` (libusb0) may also work but WinUSB is
> recommended.

---

## Using the App

The app starts minimized to the **system tray**. Right‑click the tray icon for:

- **Settings** — open the configuration window.
- **Pause / Resume** — temporarily stop/restart responding to the knob.
- **Exit** — quit.

### Window controls (bottom bar)

- **Save** / **Reload** — persist or re‑read `config.json`.
- **Minimize to Tray** — hide the window but keep the app running in the background.
- **Quit** — fully exit the application.
- **Start with Windows** — checkbox that registers/unregisters the app in the
  per‑user startup (HKCU `…\Run`) so it launches automatically at login.
- Clicking the window's **X** also minimizes to the tray (it does **not** quit).

### Knob Activity panel

The panel above the bottom bar shows a live, timestamped log of every event received
from the knob — the trigger, the focused app, and the action taken
(e.g. `12:01:03 rotate_right +2 [chrome.exe] -> scroll_down`). Use it to confirm that
gestures like **triple‑press** and **long‑press** are firing and to debug bindings.
**Clear** empties the log.

### The Settings window

- **Profiles (left sidebar)** — `default` plus one entry per app. Click to select.
  - **+ Add Profile** opens a picker listing your **currently running apps**; click one to
    create a profile for it (e.g. `chrome.exe`).
  - **- Delete Profile** removes the selected profile (`default` cannot be deleted).
- **Bindings tab** — a row for each of the 8 triggers. Pick an **action** and fill in its
  parameters. The `key` action has a **Record** button: click it, press your shortcut, and
  it captures the combo (e.g. `ctrl+shift+n`).
- **LED tab** — choose the mode, brightness, pulse speed/waveform, flash timing, and
  volume‑fade timing. **Test LED** applies the settings to the device live.
- **Timing tab** — multi‑click window, long‑press threshold, rotation sensitivity.
- **Save** writes everything to `config.json`; **Reload** re‑reads it.

---

## Triggers

| Trigger | How to perform it |
|---|---|
| `rotate_right` | Turn clockwise |
| `rotate_left` | Turn counter‑clockwise |
| `press` | One click (fires after the multi‑click window elapses) |
| `double_press` | Two quick clicks |
| `triple_press` | Three quick clicks |
| `long_press` | Hold the button past the long‑press threshold (default 500 ms) |
| `press_rotate_right` | Hold the button **and** turn clockwise |
| `press_rotate_left` | Hold the button **and** turn counter‑clockwise |

A single press intentionally waits for the multi‑click window (default 250 ms) so it can be
distinguished from a double/triple press. Press‑while‑rotating suppresses the click so it
doesn't also register as a press.

---

## Actions

| Action | Parameters | Description |
|---|---|---|
| `volume_up` | `amount` (0.0–1.0) | Raise system volume |
| `volume_down` | `amount` (0.0–1.0) | Lower system volume |
| `mute` | — | Toggle system mute |
| `mic_mute_toggle` | — | Toggle microphone mute |
| `media_play_pause` | — | Media play/pause key |
| `media_next` | — | Next track |
| `media_prev` | — | Previous track |
| `scroll_up` | `amount` (lines) | Scroll up |
| `scroll_down` | `amount` (lines) | Scroll down |
| `key` | `keys` (e.g. `"ctrl+z"`) | Send a keyboard shortcut |
| `macro` | `sequence` (list, up to 3) | Send several key combos in order, e.g. `["ctrl+c","alt+tab","ctrl+v"]` |
| `launch` | `path` | Open a file, app, or URL |
| `run` | `command` | Run a shell command |
| `none` | — | Do nothing (also used to inherit from `default`) |

Volume and mic actions use **pycaw** (native Windows Core Audio) — no helper executables.
Keyboard and media actions use the **keyboard** library; shortcut syntax is
`modifier+modifier+key`, e.g. `alt+left`, `ctrl+shift+escape`, `f5`.

---

## LED Modes

| Mode | Behavior |
|---|---|
| `off` | LED off |
| `solid` | Constant brightness (set by `brightness`, 0.0–1.0) |
| `pulse` | Smooth software sine pulse; `pulse_speed` (0–510) sets the period |
| `flash` | On/off at `flash_on_ms` / `flash_off_ms` |
| `volume` | Brightness tracks the system volume, then fades after `fade_delay`/`fade_speed` |

> On Windows the LED is driven entirely via interrupt‑OUT writes, so **pulse and flash are
> implemented in software** (the device's hardware‑pulse command uses a control transfer
> that is incompatible with simultaneous reads on WinUSB — see notes below).

---

## Per‑App Profiles

Each profile maps triggers to actions. The **`default`** profile applies whenever the
focused app has no profile of its own. App profiles **inherit** from `default`: any trigger
you don't explicitly set falls back to the default binding.

The active app is detected from the foreground window's process name (e.g. `chrome.exe`,
`code.exe`, `vlc.exe`) via the Win32 API.

**Example:** make the knob scroll in Chrome but keep controlling volume everywhere else —
add a `chrome.exe` profile that overrides only `rotate_left`/`rotate_right`.

A ready-made **`spotify.exe`** profile ships in the defaults: it maps single-press to
play/pause (`space`), double/triple-press to next/previous track (`ctrl+right` /
`ctrl+left`), and inherits system-volume control on rotation. Because it sends Spotify's
own in-app shortcuts while Spotify is focused, play/pause toggles reliably (the global
media key can otherwise be routed to a different app by Windows).

---

## Configuration File

Settings live in **`config.json`** next to the app (created on first run from defaults; a
template is provided as `config.example.json`). It is human‑editable and **hot‑reloaded**
within ~1 second of saving.

```json
{
  "timing": { "multi_click_ms": 250, "long_press_ms": 500,
              "rotate_sensitivity": 1.0, "rotate_acceleration": 0.0 },
  "led": { "mode": "volume", "brightness": 1.0,
           "pulse_speed": 255, "pulse_table": 0,
           "flash_on_ms": 200, "flash_off_ms": 800,
           "fade_speed": 1.0, "fade_delay": 1.0 },
  "start_with_windows": false,
  "profiles": {
    "default": {
      "rotate_right":       { "action": "volume_up",   "amount": 0.04 },
      "rotate_left":        { "action": "volume_down",  "amount": 0.04 },
      "press":              { "action": "mute" },
      "double_press":       { "action": "media_play_pause" },
      "triple_press":       { "action": "media_next" },
      "long_press":         { "action": "mic_mute_toggle" },
      "press_rotate_right": { "action": "scroll_down",  "amount": 3 },
      "press_rotate_left":  { "action": "scroll_up",    "amount": 3 }
    },
    "chrome.exe": {
      "rotate_right": { "action": "scroll_down", "amount": 3 },
      "rotate_left":  { "action": "scroll_up",   "amount": 3 },
      "long_press":   { "action": "key", "keys": "f5" }
    }
  }
}
```

---

## Timing & Sensitivity

| Setting | Default | Meaning |
|---|---|---|
| `multi_click_ms` | 250 | Window to detect double/triple clicks; a single press fires after this |
| `long_press_ms` | 500 | Hold time required to trigger `long_press` |
| `rotate_sensitivity` | 1.0 | Multiplier applied to each rotation delta before accumulation |
| `rotate_acceleration` | 0.0 | Reserved for future acceleration curves |

Lower `multi_click_ms` for snappier single presses (at the cost of harder double/triple
detection); raise `rotate_sensitivity` to make a small turn do more.

---

## Building the EXE

Requires `pyinstaller` (`pip install pyinstaller`) and the `libusb` package (in
`requirements.txt`, which bundles the native DLL).

```powershell
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean build.spec
# Output: dist\PowerMate.exe  (one file, ~25 MB)
```

`build.spec` automatically:

- locates and bundles `libusb-1.0.dll` from the `libusb` package,
- collects CustomTkinter's theme/asset data files,
- bundles `assets/icon.ico`,
- adds the required hidden imports (`comtypes`, `pycaw`, `pystray._win32`, pywin32 modules).

At runtime the app finds the bundled DLL via `sys._MEIPASS`, so the EXE is fully
self‑contained — only the **WinUSB driver** (Zadig) is needed on the target machine.

---

## Architecture

```
main.py          App orchestration: worker thread, LED thread, GUI, tray, config wiring
device.py        USB layer: libusb backend discovery, find/claim, interrupt read, LED write
gesture.py       State machine: raw button/rotation -> high-level triggers (click timing)
led.py           LED controller thread: solid / software pulse / flash / volume-fade
audio.py         Native volume + mic control (pycaw), thread-safe across COM apartments
actions.py       Action executors (volume, media, scroll, keys, launch, run)
app_monitor.py   Foreground process detection for per-app profiles
config.py        Load/save/validate config.json with live file-watch reload
tray.py          System tray icon + menu (pystray)
ui/              CustomTkinter GUI (app_window, profile_view, action_editor,
                 led_panel, timing_panel)
```

**Threading model**

- A **worker thread** owns the USB device: it reconnects on unplug, reads endpoint `0x81`,
  feeds packets to the gesture engine, resolves the active‑app profile, and dispatches
  actions.
- A **LED thread** continuously applies the chosen LED mode.
- The **GUI** runs on the main thread; status updates from other threads are marshalled
  with `Tk.after()`.
- The **tray** runs its own thread.
- **COM** is initialized per‑thread (audio is called from both the worker and LED threads),
  using thread‑local endpoint interfaces.

---

## Reverse‑Engineering Notes (Windows / WinUSB)

These findings, discovered while validating against real hardware, are baked into the app:

1. **The device must be on the WinUSB driver.** With the default HID driver, libusb can
   enumerate the device and even fake `set_configuration`/`claim_interface`, but every real
   transfer fails with *"Operation not supported on this platform."* Zadig → WinUSB fixes it.

2. **Do not call `set_configuration()` on Windows.** WinUSB has already configured the
   device; calling it again invalidates the endpoint pipe handles, after which interrupt
   reads fail with *"Entity not found."* The app claims interface 0 and reads directly.

3. **Set the LED via interrupt‑OUT (endpoint `0x02`), not a vendor control transfer.** A
   vendor *control* transfer for brightness **permanently breaks the interrupt‑IN read
   pipe** on WinUSB ("Entity not found" on all subsequent reads) until the device is
   power‑cycled. The single‑byte interrupt‑OUT write — the method used by the original
   hardware — sets brightness reliably and does **not** disturb reads. Consequently the
   device's *hardware* pulse modes (also control transfers) are disabled on Windows, and
   pulse/flash are done in software.

4. **Rotation batches under slow polling.** A fast spin polled slowly arrives as one large
   signed delta, so the gesture engine accumulates deltas instead of counting packets.

5. **pyusb needs a native backend.** pyusb is bindings only; the `libusb` pip package
   supplies `libusb-1.0.dll`, which `device.py` locates automatically (bundle dir, then the
   installed package).

---

## Security Considerations

A high-level assessment of the threat model:

- **No remote attack surface.** The app opens no network sockets, servers, or ports. It
  talks only to a local USB device and the local Windows audio/input APIs.
- **Runs with normal user privileges.** No elevation is required or requested. The
  *Start with Windows* entry is written to the per-user `HKCU` Run key (not system-wide
  `HKLM`), and its command is built from the executable/script path — not from user input,
  so it isn't injectable.
- **Code-execution actions are user-defined and local.** The `run` (shell command),
  `launch` (open file/app/URL), `key`, and `macro` actions execute what *you* put in your
  own `config.json`. They run with your privileges — only bind commands you trust. The
  threat model is "the user configures their own knob"; there is no path for a remote party
  to inject actions.
  - `run` uses the shell (`shell=True`) so that shell features work; treat its value like a
    line you'd type into a terminal yourself.
- **Input is bounded and parsed safely.** USB reports are fixed-size 6-byte reads; the
  config is parsed with `json.load` (no `eval`/`pickle`), and a malformed config falls back
  to defaults rather than crashing.
- **Keyboard output only.** The app uses the `keyboard` library to *send* keystrokes for
  bindings; it does not install a global key logger/hook.

No high-severity issues were identified. If you distribute the EXE, dependencies are
sourced from PyPI and pinned in `requirements.txt`; rebuild from source if you require a
verified supply chain.

## Testing

Three test suites run **without** hardware:

```powershell
python _test_gesture.py     # gesture state machine: all 8 triggers + regressions
python _test_features.py    # macro action, startup module, debug panel, triple/long bindings
python _smoketest_gui.py    # builds the GUI, exercises profiles/panels/save, tears down
```

The gesture tests cover single/double/triple/long press, both rotations, press‑while‑rotate,
and regressions for "no spurious press after press+rotate" and "no long‑press while
rotating." The GUI smoke test verifies the window builds, the default profile auto‑loads all
8 trigger editors, bindings round‑trip through save, the LED/Timing tabs populate, and
profile inheritance works.

Hardware was validated end‑to‑end: rotation → volume, press → mute, button detection, and
LED control all confirmed on a real PowerMate over WinUSB.

---

## Troubleshooting

**"PowerMate not found" (red status / tray)**
- Confirm the **WinUSB** driver is installed via Zadig (this is the most common cause).
- Replug the device; check the status bar in **Settings**.
- Inspect `powermate.log` next to the app.

**Reads stop / LED works but knob does nothing**
- Almost always a stale driver state — unplug and replug to power‑cycle the device.
- Ensure no other program is holding the device (only one process can claim WinUSB).

**LED doesn't light**
- Make sure the LED mode isn't `off` and (for `solid`) brightness isn't 0.
- Switch to `flash` briefly to confirm the device responds.

**Keyboard shortcuts don't fire**
- The target app must have focus. Some apps capture keys differently.
- Verify the `keys` syntax (e.g. `ctrl+z`, `alt+tab`, `f5`).

**Config changes don't apply**
- The watcher reloads within ~1s; if your editor doesn't update the file's mtime, use
  **Reload** in Settings or restart.

**Run from source for verbose logs**
```powershell
python main.py debug
```

---

## Project Layout

```
powermate-app/
├── main.py                 # entry point / orchestration
├── device.py               # USB communication + libusb backend discovery
├── gesture.py              # gesture state machine
├── led.py                  # LED controller thread
├── audio.py                # volume / mic (pycaw, COM-thread-safe)
├── actions.py              # action executors
├── app_monitor.py          # active-app detection
├── config.py               # config load/save/watch
├── startup.py              # start-with-Windows (HKCU Run key)
├── tray.py                 # system tray
├── ui/
│   ├── app_window.py       # main settings window
│   ├── profile_view.py     # trigger→action grid
│   ├── action_editor.py    # action picker + key-capture
│   ├── led_panel.py        # LED settings + live test
│   └── timing_panel.py     # gesture timing
├── assets/icon.ico
├── config.example.json     # template (your config.json is git-ignored)
├── requirements.txt
├── build.spec              # PyInstaller one-file build
├── install.bat             # convenience installer (deps + driver guidance)
├── _test_gesture.py        # gesture unit tests
├── _test_features.py       # macro / startup / debug-panel tests
├── _smoketest_gui.py       # GUI smoke test
├── README.md
└── QUICKSTART.md
```

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the full version history. Highlights:

- **1.1.1** — security/memory hardening (config deepcopy, reload-spam fix, debug-panel
  idle optimization) and a documented vulnerability assessment.
- **1.1.0** — audio control fix (pycaw API change), 3-step macros, knob-activity debug
  panel, Start-with-Windows toggle, tray/quit controls, and a `spotify.exe` profile.
- **1.0.0** — initial release.

## Credits & License

- Original Java PowerMate utility: **Nathan Sweet / Esoteric Software** —
  <https://github.com/EsotericSoftware/powermate> (New BSD License).
- USB protocol reference: the Linux kernel **`drivers/input/misc/powermate.c`** driver.
- Built on [pyusb](https://github.com/pyusb/pyusb), [libusb](https://libusb.info/),
  [pycaw](https://github.com/AndreMiras/pycaw),
  [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter),
  [pystray](https://github.com/moses-palmer/pystray), and
  [pywin32](https://github.com/mhammond/pywin32).

Released under the **New BSD (3‑Clause) License**, consistent with the original project.
See [`LICENSE`](LICENSE).
