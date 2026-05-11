"""
VisionErgo — Oturum Kaydedici
Her N saniyede bir oturum metriklerini CSV dosyasina kaydeder.
"""

import csv
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

from utils.config import SESSION_LOG_ENABLED, SESSION_LOG_DIR, SESSION_LOG_INTERVAL

logger = logging.getLogger(__name__)

_CSV_FIELDS = [
    "timestamp",
    "elapsed_sec",
    "posture_status",
    "posture_score",
    "deviation_px",
    "bpm",
    "alert_level",
    "total_blinks",
]


class SessionLogger:
    """
    Oturum verilerini zamanlayici baz alarak CSV dosyasina kaydeder.

    Kullanim:
        logger = SessionLogger()
        logger.start()
        ...
        logger.record(posture_metrics, blink_metrics, stats)
        ...
        logger.stop()  # Dosyayi kapatir
    """

    def __init__(self) -> None:
        self.enabled      = SESSION_LOG_ENABLED
        self._file        = None
        self._writer      = None
        self._last_write  = 0.0
        self._filepath    = ""

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def start(self) -> None:
        """Log dosyasini olusturur ve CSV basligini yazar."""
        if not self.enabled:
            return

        os.makedirs(SESSION_LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._filepath = os.path.join(SESSION_LOG_DIR, f"session_{ts}.csv")

        self._file   = open(self._filepath, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=_CSV_FIELDS)
        self._writer.writeheader()
        self._file.flush()

        logger.info(f"Oturum log dosyasi olusturuldu: {self._filepath}")

    def record(
        self,
        posture: Dict[str, Any],
        blink:   Dict[str, Any],
        stats:   Dict[str, Any],
    ) -> None:
        """
        Belirli aralikta (SESSION_LOG_INTERVAL) CSV'ye yeni satir ekler.
        Ana dongudan her kare icin cagrilabilir; gereksiz yazim yapmaz.
        """
        if not self.enabled or self._writer is None:
            return

        now = time.time()
        if now - self._last_write < SESSION_LOG_INTERVAL:
            return

        self._last_write = now
        row = {
            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_sec":    round(stats.get("elapsed_seconds", 0), 1),
            "posture_status": posture.get("status", "Unknown"),
            "posture_score":  posture.get("posture_score", 100),
            "deviation_px":   posture.get("deviation", 0),
            "bpm":            blink.get("bpm", 0),
            "alert_level":    blink.get("alert_level", "ok"),
            "total_blinks":   blink.get("total_blinks", 0),
        }
        self._writer.writerow(row)
        self._file.flush()

    def stop(self) -> None:
        """CSV dosyasini kapatir."""
        if self._file is not None:
            self._file.close()
            self._file   = None
            self._writer = None
            logger.info(f"Oturum log dosyasi kapatildi: {self._filepath}")

    @property
    def filepath(self) -> str:
        return self._filepath
