"""
VisionErgo — Ana Kontrol Sinifi
Kamera akisini, durus analizini ve goz kirpma tespitini koordine eder.
Oturum istatistiklerini tutar.
"""

import time
import logging
from typing import Optional, Dict, Any
import numpy as np

from .camera import CameraStream
from .posture import PostureAnalyzer
from .blink import BlinkDetector
from utils.config import CAMERA_INDEX, CAMERA_RESOLUTION

logger = logging.getLogger(__name__)


class ErgoMonitor:
    """
    VisionErgo sisteminin ana kontrolcusu.

    Sorumluluklar:
        - Kamera akisini baslatmak / durdurmak.
        - Her kareyi PostureAnalyzer ve BlinkDetector'a gondermek.
        - Oturum istatistiklerini toplamak.
    """

    def __init__(self, camera_index: int = CAMERA_INDEX) -> None:
        self.camera_stream   = CameraStream(camera_index=camera_index,
                                            resolution=CAMERA_RESOLUTION)
        self.posture_analyzer = PostureAnalyzer()
        self.blink_detector   = BlinkDetector()

        self.is_monitoring: bool = False
        self._session_start: Optional[float] = None

        # Oturum istatistikleri
        self._bad_posture_frames: int = 0
        self._total_frames: int       = 0

        logger.info("ErgoMonitor baslatildi.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Sistemi baslatir."""
        if self.is_monitoring:
            logger.warning("ErgoMonitor zaten calisiyor.")
            return True

        if not self.camera_stream.start():
            logger.error("Kamera akisi baslatılamadi.")
            return False

        self.is_monitoring = True
        self._session_start = time.time()
        logger.info("Izleme baslatildi.")
        return True

    def stop(self) -> None:
        """Sistemi durdurur, kaynaklari serbest birakir."""
        self.camera_stream.stop()
        self.is_monitoring = False
        logger.info("ErgoMonitor durduruldu.")

    def process_frame(self) -> Optional[Dict[str, Any]]:
        """
        Kameradan son kareyi alir, analiz eder ve sonuclari donderir.

        Returns:
            None — kare yoksa.
            Dict — analiz sonuclari + annotated_frame.
        """
        if not self.is_monitoring:
            return None

        frame = self.camera_stream.read()
        if frame is None:
            return None

        self._total_frames += 1
        return self._analyze(frame)

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Mevcut oturum istatistiklerini donderir.

        Returns:
            {elapsed_seconds, elapsed_str, bad_posture_ratio,
             total_blinks, bpm}
        """
        elapsed = time.time() - self._session_start if self._session_start else 0
        mins, secs = divmod(int(elapsed), 60)
        bad_ratio = (
            self._bad_posture_frames / self._total_frames
            if self._total_frames > 0
            else 0.0
        )
        bpm = len(self.blink_detector.blink_timestamps)
        return {
            "elapsed_seconds": elapsed,
            "elapsed_str": f"{mins:02d}:{secs:02d}",
            "bad_posture_ratio": bad_ratio,
            "total_blinks": self.blink_detector.total_blinks,
            "bpm": bpm,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _analyze(self, frame: np.ndarray) -> Dict[str, Any]:
        annotated_frame, posture_metrics = self.posture_analyzer.analyze(frame)
        annotated_frame, blink_metrics  = self.blink_detector.analyze(
            annotated_frame, posture_metrics.get("face_rect")
        )

        if posture_metrics.get("warning"):
            self._bad_posture_frames += 1

        return {
            "posture": posture_metrics,
            "blink":   blink_metrics,
            "annotated_frame": annotated_frame,
        }
