"""Windows audio control using pycaw.

COM interfaces have thread affinity, and this app calls audio from several
threads (worker thread for actions, LED thread for volume tracking). We therefore
initialise COM and create the endpoint interface lazily *per thread* using
thread-local storage.
"""
import logging
import threading
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

logger = logging.getLogger(__name__)


class AudioController:
    """Control system volume and microphone (thread-safe across COM apartments)."""

    def __init__(self):
        self._local = threading.local()

    def _ensure_com(self):
        """Initialise COM for the current thread (idempotent per thread)."""
        if getattr(self._local, "com_init", False):
            return
        try:
            comtypes.CoInitialize()
        except Exception:
            pass
        self._local.com_init = True

    def _speakers(self) -> object:
        """Get (and cache) the speaker volume interface for this thread."""
        iface = getattr(self._local, "speakers", None)
        if iface is None:
            self._ensure_com()
            try:
                devices = AudioUtilities.GetSpeakers()
                activated = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                iface = cast(activated, POINTER(IAudioEndpointVolume))
                self._local.speakers = iface
            except Exception as e:
                logger.debug(f"Failed to get speaker interface: {e}")
                return None
        return iface

    def _microphone(self) -> object:
        """Get (and cache) the microphone volume interface for this thread."""
        iface = getattr(self._local, "mic", None)
        if iface is None:
            self._ensure_com()
            try:
                devices = AudioUtilities.GetMicrophone()
                if not devices:
                    return None
                activated = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                iface = cast(activated, POINTER(IAudioEndpointVolume))
                self._local.mic = iface
            except Exception as e:
                logger.debug(f"Failed to get microphone interface: {e}")
                return None
        return iface

    def get_volume(self) -> float:
        """Get current system volume (0.0-1.0)."""
        iface = self._speakers()
        if iface:
            try:
                return iface.GetMasterVolumeLevelScalar()
            except Exception as e:
                logger.debug(f"Error getting volume: {e}")
        return 0.5

    def set_volume(self, level: float):
        """Set system volume (0.0-1.0)."""
        level = max(0.0, min(1.0, level))
        iface = self._speakers()
        if iface:
            try:
                iface.SetMasterVolumeLevelScalar(level, None)
            except Exception as e:
                logger.debug(f"Error setting volume: {e}")

    def is_muted(self) -> bool:
        """Check if system volume is muted."""
        iface = self._speakers()
        if iface:
            try:
                return bool(iface.GetMute())
            except Exception as e:
                logger.debug(f"Error checking mute: {e}")
        return False

    def set_mute(self, muted: bool):
        """Mute or unmute system volume."""
        iface = self._speakers()
        if iface:
            try:
                iface.SetMute(1 if muted else 0, None)
            except Exception as e:
                logger.debug(f"Error setting mute: {e}")

    def toggle_mute(self):
        """Toggle mute state."""
        self.set_mute(not self.is_muted())

    def get_mic_mute(self) -> bool:
        """Get microphone mute state (if available)."""
        iface = self._microphone()
        if iface:
            try:
                return bool(iface.GetMute())
            except Exception as e:
                logger.debug(f"Error getting mic mute state: {e}")
        return False

    def set_mic_mute(self, muted: bool):
        """Mute or unmute microphone."""
        iface = self._microphone()
        if iface:
            try:
                iface.SetMute(1 if muted else 0, None)
            except Exception as e:
                logger.debug(f"Error setting mic mute: {e}")

    def toggle_mic_mute(self):
        """Toggle microphone mute."""
        self.set_mic_mute(not self.get_mic_mute())
