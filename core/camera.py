"""
VisionErgo — Kamera Akisi (v2.1)
Thread tabanli kamera okuma, FPS takibi ve kamera isi baslatma destekler.
"""

import cv2
import threading
import time
import logging
from collections import deque
from typing import Optional, Tuple
import numpy as np

from utils.config import CAMERA_WARMUP_FRAMES

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Ayri bir thread'de kamera karelerini okur.

    Iyilestirmeler:
        - Kamera acildiktan sonra CAMERA_WARMUP_FRAMES kadar kare atlanir
          (otomatik pozlama/beyaz denge oturmasi beklenir).
        - Son 30 karenin suresiyle yuvarlanan FPS hesaplanir.
        - Thread-safe okuma (Lock).
    """

    _FPS_WINDOW = 30   # Yuvarlanan FPS penceresi (kare sayisi)

    def __init__(
        self,
        camera_index: int = 0,
        resolution: Tuple[int, int] = (1280, 720),
    ) -> None:
        self.camera_index = camera_index
        self.resolution   = resolution

        self.capture: Optional[cv2.VideoCapture] = None
        self.is_running   = False
        self.current_frame: Optional[np.ndarray] = None

        self._lock   = threading.Lock()
        self._thread: Optional[threading.Thread] = None

        # FPS takibi
        self._frame_times: deque = deque(maxlen=self._FPS_WINDOW)
        self._warmup_done = False
        self._warmup_count = 0

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def start(self) -> bool:
        """Kamera ve arka plan thread'ini baslatir."""
        if self.is_running:
            logger.warning("Kamera zaten calisiyor.")
            return True

        self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.capture.isOpened():
            # CAP_DSHOW basarisiz olursa varsayilan backend dene
            self.capture = cv2.VideoCapture(self.camera_index)
            if not self.capture.isOpened():
                logger.error(f"Kamera acilamadi: index={self.camera_index}")
                return False

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH,  self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # Gecikmeyi azalt

        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="CameraThread")
        self._thread.start()

        logger.info(f"Kamera baslatildi: index={self.camera_index}, cozunurluk={self.resolution}")
        return True

    def read(self) -> Optional[np.ndarray]:
        """Son kareyi donderir (warmup bitmemisse None)."""
        if not self._warmup_done:
            return None
        with self._lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def get_fps(self) -> float:
        """Son N karenin ortalamasina dayali FPS degerini donderir."""
        if len(self._frame_times) < 2:
            return 0.0
        deltas = [
            self._frame_times[i] - self._frame_times[i - 1]
            for i in range(1, len(self._frame_times))
        ]
        avg_delta = sum(deltas) / len(deltas)
        return round(1.0 / avg_delta, 1) if avg_delta > 0 else 0.0

    def stop(self) -> None:
        """Kamerayi durdurur ve kaynaklari serbest birakir."""
        self.is_running = False
        if self._thread is not None:
            self._thread.join(timeout=3)

        if self.capture is not None:
            self.capture.release()
            self.capture = None

        logger.info("Kamera durduruldu ve kaynaklar serbest birakildi.")

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _loop(self) -> None:
        """Arka plan okuma dongusu."""
        while self.is_running:
            if self.capture is None or not self.capture.isOpened():
                time.sleep(0.01)
                continue

            ret, frame = self.capture.read()
            if not ret:
                logger.warning("Kare okunamadi.")
                time.sleep(0.01)
                continue

            # Ayna efekti
            frame = cv2.flip(frame, 1)

            # Warmup: ilk N kareyi atla
            if not self._warmup_done:
                self._warmup_count += 1
                if self._warmup_count >= CAMERA_WARMUP_FRAMES:
                    self._warmup_done = True
                    logger.info("Kamera isi tamamlandi, izleme aktif.")
                continue

            # FPS kaydi
            self._frame_times.append(time.time())

            with self._lock:
                self.current_frame = frame
