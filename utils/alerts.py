"""
VisionErgo — Ses Uyari Sistemi
Windows dahili winsound kutuphanesi ile kotu durus ve kuru goz uyarilari calinir.
Cooldown mekanizmasi uyari spam'ini onler.
"""

import time
import logging
import threading
from typing import Optional

from utils.config import (
    ALERT_ENABLED,
    ALERT_BAD_POSTURE_COOLDOWN,
    ALERT_DRY_EYE_COOLDOWN,
)

logger = logging.getLogger(__name__)

# Windows disinda winsound yoktur; sessizce devre disi birakilir.
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False
    logger.warning("winsound bulunamadi; ses uyarilari devre disi.")


def _beep_async(freq: int, duration_ms: int) -> None:
    """Ana donguyu bloke etmeden ses calar."""
    if not _HAS_WINSOUND:
        return
    threading.Thread(
        target=winsound.Beep, args=(freq, duration_ms), daemon=True
    ).start()


class AlertManager:
    """
    Kotu durus ve kuru goz icin sesli uyari verir.

    Cooldown mekanizmasi:
        - Ayni tip uyari art arda calınmaz; aralarinda en az
          konfigurasyon dosyasinda belirtilen sure gecmesi gerekir.
    """

    def __init__(self) -> None:
        self._last_posture_alert: Optional[float] = None
        self._last_eye_alert: Optional[float] = None
        self.enabled = ALERT_ENABLED and _HAS_WINSOUND

        if not _HAS_WINSOUND:
            self.enabled = False

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def check_posture(self, status: str) -> None:
        """
        Durus durumu 'Bad' veya 'Up' ise cooldown dolmusssa sesli uyari verir.

        Ses: 2 kisa bip (800 Hz)
        """
        if not self.enabled:
            return
        if status not in ("Bad", "Up"):
            return

        now = time.time()
        if self._last_posture_alert is None or (now - self._last_posture_alert) >= ALERT_BAD_POSTURE_COOLDOWN:
            self._last_posture_alert = now
            logger.info(f"[ALERT] Durus uyarisi: {status}")
            _beep_async(800, 150)
            time.sleep(0.02)   # Kisa bekleme (thread baslangic gecikmesi)
            _beep_async(800, 150)

    def check_blink(self, alert_level: str) -> None:
        """
        BPM kritik/dusuk ise cooldown dolmussa sesli uyari verir.

        Ses:
            critical — 3 uzun bip (500 Hz)
            low      — 1 kisa bip (600 Hz)
        """
        if not self.enabled:
            return
        if alert_level == "ok":
            return

        now = time.time()
        if self._last_eye_alert is None or (now - self._last_eye_alert) >= ALERT_DRY_EYE_COOLDOWN:
            self._last_eye_alert = now
            logger.info(f"[ALERT] Goz uyarisi: {alert_level}")
            if alert_level == "critical":
                for _ in range(3):
                    _beep_async(500, 300)
                    time.sleep(0.05)
            else:
                _beep_async(600, 200)
