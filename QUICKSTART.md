# PowerMate Quick Start Guide

## First-Time Setup (5 minutes)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or use the installer batch file:
```bash
install.bat
```

### 2. Install USB Driver (Zadig)

This is a one-time setup required for the PowerMate to work.

1. Download **Zadig** from https://zadig.akeo.ie/
2. **Plug in your PowerMate** USB knob
3. Run Zadig (no admin required)
4. Click **Options** → **List All Devices**
5. In the dropdown, select **Griffin PowerMate**
6. Verify the driver name is **libusb-win32** (not libusb)
7. Click **Replace Driver** and wait for completion
8. You may see an error — that's normal; the driver was still installed

**You only need to do this once.**

### 3. Run the Application

From the command line:
```bash
python main.py
```

Or build and run as a standalone EXE:
```bash
pyinstaller build.spec
```
Then run `dist/PowerMate.exe`

## What You'll See

1. **System Tray Icon** appears (blue, in the bottom-right corner)
2. **Settings Window** may open (depends on first run)
3. **Status Bar** shows "PowerMate connected" (green) if device found, or "PowerMate not found" (red) if not

## Basic Usage

### Rotate the Knob
- **Rotate clockwise** → increases system volume
- **Rotate counter-clockwise** → decreases system volume
- **LED brightness** follows volume, then fades after 1 second

### Press the Knob
- **Single click** → mute/unmute
- **Double click** → play/pause
- **Triple click** → next track
- **Long press** (hold 0.5 seconds) → toggle microphone mute

### Rotate While Pressing
- **Hold + rotate clockwise** → scroll down (web pages, etc.)
- **Hold + rotate counter-clockwise** → scroll up

## Customize Behavior

### Using the GUI
1. Right-click the tray icon and click **Settings**
2. **Profiles** tab on the left:
   - Default profile applies to all apps
   - **+ Add Profile** to create app-specific bindings
3. **Bindings** tab: edit trigger → action for each profile
4. **LED** tab: change LED mode (solid, pulse, flash, volume-track)
5. **Timing** tab: adjust gesture timing if needed
6. Click **Save** to persist

### Editing config.json by Hand
- Close the app
- Open `config.json` in a text editor
- Modify the profiles, actions, LED settings, timing
- Save the file
- Restart the app (or it auto-reloads in a few seconds)

## Common Customizations

### Make PowerMate control video playback in Chrome
1. Open Settings → click "+ Add Profile" → select `chrome.exe`
2. In the **Bindings** tab, for the Chrome profile:
   - `rotate_right`: `scroll_down`, amount=5
   - `rotate_left`: `scroll_up`, amount=5
   - `long_press`: `key`, keys="f5" (refresh)
   - `double_press`: `key`, keys="space" (play/pause)
3. Click **Save**

### Custom Keyboard Shortcut
1. In the Bindings tab, select a trigger
2. Choose action `key`
3. In the **Keys** field, enter the shortcut (e.g., `"ctrl+z"` for undo)
4. Click **Save**

### Launch an App
1. In the Bindings tab, select a trigger
2. Choose action `launch`
3. In the **Path** field, enter:
   - `"C:\Program Files\VLC\vlc.exe"` (full path to app)
   - `"https://www.youtube.com"` (URL)
   - `"C:\Users\YourName\Documents\file.pdf"` (file to open)
4. Click **Save**

## Troubleshooting

### "PowerMate not found" — red status
1. Check the USB cable is plugged in
2. Verify Zadig driver is installed (see **Install USB Driver** above)
3. Try unplugging and replugging the knob
4. Restart the app

### Actions don't fire
1. Ensure the correct profile is active (status bar shows app name)
2. Click the profile in the Settings window to verify bindings
3. For keyboard shortcuts, ensure the target app has focus
4. Restart the app

### LED doesn't respond
1. Check LED mode is not `off` (LED tab)
2. If in `solid` mode, ensure brightness slider is not at 0
3. Try switching to `flash` mode to verify the device responds
4. Some v1 PowerMate devices may not support hardware pulse — the app falls back automatically

## Tips

- **Pause/Resume**: Right-click the tray icon and click **Pause** to temporarily disable the knob. Click **Resume** to re-enable.
- **Auto-reload**: Edit `config.json` by hand and save — the app auto-reloads within 1 second (you'll see "Status: Reloaded").
- **Per-app profiles**: Profiles inherit from `default`, so you only need to override the triggers you customize.
- **Multiple PowerMates**: The current version supports one PowerMate. Multiple support would require device selection in the GUI (future enhancement).

## Need Help?

1. Check `powermate.log` in the app directory for error messages
2. Open Settings and check the status bar for connection state
3. Run with debug logging:
   ```bash
   python main.py debug
   ```
   This prints detailed logs to the console

---

**Enjoy your PowerMate!** 🎛️
