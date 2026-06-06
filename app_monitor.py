"""Monitor active application/process."""
import logging
from typing import Optional
import psutil

try:
    import win32gui
    import win32process
    WINAPI_AVAILABLE = True
except ImportError:
    WINAPI_AVAILABLE = False
    logging.warning("pywin32 not available, app monitoring limited")

logger = logging.getLogger(__name__)


def get_active_process_name() -> Optional[str]:
    """
    Get the executable name of the currently active foreground window.
    Returns lowercase exe name (e.g. "chrome.exe") or None if not available.
    """
    if not WINAPI_AVAILABLE:
        return None

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None

        try:
            proc = psutil.Process(pid)
            name = proc.name().lower()
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    except Exception as e:
        logger.debug(f"Error getting active process: {e}")
        return None


def get_running_processes() -> list:
    """Get list of running process exe names (lowercase)."""
    seen = set()
    procs = []

    try:
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if name and name not in seen:
                    seen.add(name)
                    procs.append(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.debug(f"Error enumerating processes: {e}")

    return sorted(procs)
