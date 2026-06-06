"""Manage 'start with Windows' via the per-user registry Run key (HKCU)."""
import os
import sys
import logging

logger = logging.getLogger(__name__)

try:
    import winreg
except ImportError:  # non-Windows
    winreg = None

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "GriffinPowerMate"


def _launch_command() -> str:
    """Build the command Windows should run at login."""
    if getattr(sys, "frozen", False):
        # Packaged EXE: run it directly.
        return f'"{sys.executable}"'
    # Running from source: prefer pythonw.exe (no console window).
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    pyw = sys.executable
    cand = os.path.join(os.path.dirname(pyw), "pythonw.exe")
    if os.path.exists(cand):
        pyw = cand
    return f'"{pyw}" "{script}"'


def is_enabled() -> bool:
    """Return True if the Run-key entry exists."""
    if not winreg:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError as e:
        logger.debug(f"is_enabled check failed: {e}")
        return False


def set_enabled(enabled: bool) -> bool:
    """Enable/disable launching at login. Returns True on success."""
    if not winreg:
        return False
    try:
        if enabled:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _launch_command())
            logger.info("Enabled start with Windows")
        else:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                    winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, APP_NAME)
                logger.info("Disabled start with Windows")
            except FileNotFoundError:
                pass
        return True
    except OSError as e:
        logger.warning(f"Failed to set start with Windows: {e}")
        return False
