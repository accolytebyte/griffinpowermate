# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] — 2026-06-06

### Security
- **High-level vulnerability assessment performed** (see `README.md` →
  *Security Considerations*). Summary: no network listeners or remote attack surface;
  the app runs with normal user privileges; the only code-execution paths (`run`,
  `launch`, `macro`, `key`) are driven by the user's own local config by design.
  Documented the threat model and the `run` (shell) caveat.

### Fixed
- **Config shared-state aliasing:** `DEFAULT_CONFIG.copy()` was a shallow copy, so a
  fresh install that edited any nested setting (a profile, LED, timing) would mutate the
  module-level defaults. Now uses `copy.deepcopy`.
- **Config reload spam:** a malformed `config.json` left `_last_mtime` unset, causing the
  watcher to re-read the broken file every second (log/CPU churn). The mtime is now
  recorded even on parse error, so it only retries when the file actually changes.

### Changed / Performance
- **Knob Activity panel** no longer queues Tk callbacks while the window is hidden in the
  tray (where the app spends most of its life), reducing idle overhead during fast
  rotation.
- Removed an unused import (`pathlib.Path`) from `config.py`.

### Notes
- Cursory memory-leak review: GUI widgets are destroyed before being rebuilt (profile
  list, action-editor params, dialogs); USB resources are released via
  `release_interface` + `dispose_resources`; LED/worker/watch threads are bounded loops;
  the debug textbox is capped at 300 lines; per-thread COM interfaces are cached on
  long-lived threads. No unbounded growth found.

## [1.1.0] — 2026-06-06

### Fixed
- **Audio control restored.** pycaw 20251023 removed `AudioDevice.Activate()`, which the
  volume/mute/mic code relied on; every call failed silently and `get_volume` returned a
  fake `0.5`. Rewrote `audio.py` to use the low-level `MMDeviceEnumerator`, which works
  across pycaw versions. Verified setting/reading volume and toggling mute from both the
  worker and LED threads.
- **Volume/scroll math.** The rotation delta was used *as* the increment (`vol + 1` →
  instantly 100%/0%) instead of multiplying the configured step. A turn now steps smoothly
  (`delta × amount`).

### Added
- **3-step keyboard macro action** (`macro`): sends up to three key combos in sequence.
  The action editor gained a 3-field recorder (press the **●** button to capture each
  step).
- **Knob Activity / debug panel:** a live, timestamped log at the bottom of the window
  showing each incoming trigger, the focused app, and the action taken — wired
  thread-safely from the worker thread, capped and clearable.
- **Start with Windows** toggle: a checkbox that registers/unregisters the app in the
  per-user `HKCU\…\Run` key (`startup.py`).
- **Explicit window controls:** *Minimize to Tray* (keep running) and *Quit* buttons; the
  window's **X** continues to minimize to the tray.
- **`spotify.exe` profile** using Spotify's in-app shortcuts (`space`, `ctrl+right`,
  `ctrl+left`) to sidestep global media-key routing, so play/pause toggles reliably when
  Spotify is focused.
- `_test_features.py` covering the macro action, startup module, debug panel, and
  triple/long-press bindings.

### Packaging
- `build.spec` now bundles all `pycaw` submodules so the audio fix survives in the
  one-file EXE.

## [1.0.0] — 2026-06-06

### Added
- Initial release: a from-scratch Python (Windows 11) controller for the Griffin
  PowerMate USB knob.
- **Gesture engine:** rotate left/right, single/double/triple press, long press, and
  press-while-rotating, with configurable multi-click and long-press timing.
- **Per-application profiles** with inheritance from a `default` profile, using
  foreground-window process detection.
- **Actions:** system volume, mute, microphone mute, media transport, scroll, keyboard
  shortcuts, launch app/file/URL, and run shell command.
- **LED control:** off, solid, software pulse, flash, and volume-tracking with fade —
  driven via interrupt-OUT (WinUSB-safe).
- **CustomTkinter GUI** (profiles, bindings, LED, timing) and a **system tray** icon.
- **Native Windows audio** via pycaw; **libusb** backend bundled via the `libusb` package.
- **One-file PyInstaller build** (`build.spec`); verified end-to-end on real hardware.

### Reverse-engineering findings (Windows / WinUSB)
- The device must be on the **WinUSB** driver (Zadig); the default HID driver blocks
  low-level transfers.
- Do **not** call `set_configuration()` on Windows — it invalidates the endpoint pipes
  ("Entity not found").
- Set the LED via **interrupt-OUT** (endpoint `0x02`), not a vendor control transfer —
  the control transfer permanently breaks the interrupt-IN read pipe on WinUSB until a
  power cycle. Hardware pulse modes are therefore disabled on Windows; pulse/flash are
  done in software.

[1.1.1]: https://github.com/accolytebyte/griffinpowermate/releases/tag/v1.1.1
[1.1.0]: https://github.com/accolytebyte/griffinpowermate/releases/tag/v1.1.0
[1.0.0]: https://github.com/accolytebyte/griffinpowermate/releases/tag/v1.0.0
