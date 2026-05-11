"""
VisionErgo — Durus Analizi
Haar Cascade tabanli yuz tespiti ile dikey koordinat takibi yapar,
sapmayi 0-100 puan skalasina donusturur ve uc farkli durum bildirir.
"""

import cv2
import logging
from typing import Tuple, Dict, Any, Optional
import numpy as np

from utils.config import (
    DEVIATION_THRESHOLD,
    DEVIATION_UP_THRESHOLD,
    COLOR_OK, COLOR_WARN, COLOR_BAD, COLOR_INFO,
)

logger = logging.getLogger(__name__)


class PostureAnalyzer:
    """
    Yuz merkezi Y koordinatini referans degerle karsilastirir.

    Durum seviyeleri:
        Good    — referans civarinda, iyi durus.
        Warning — hafif sapma, uyari.
        Bad     — kritik sapma, kirmizi uyari.
        Up      — ekrana yaklasma (yukari egrilme).
        No Ref  — referans henuz belirlenmedi.
        No Face — yuz tespit edilemedi.
    """

    # Durus puani hesaplama icin maksimum sapma pikseli
    _MAX_DEVIATION = 80

    def __init__(self) -> None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            logger.error(f"Yuz Haar Cascade yuklenemedi: {cascade_path}")

        self.reference_y: Optional[int] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_reference(self, y_coordinate: int) -> None:
        """Iyi durus icin dikey referans noktasini ayarlar."""
        self.reference_y = y_coordinate
        logger.info(f"Durus referansi ayarlandi: Y={self.reference_y}")

    def analyze(
        self, frame: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Karedeki en buyuk yuzu tespit eder ve durus metriklerini hesaplar.

        Returns:
            annotated_frame: Kutucuk ve merkez noktalari cizilmis kare.
            metrics: {face_detected, current_y, face_rect, status,
                      warning, posture_score, deviation}
        """
        metrics: Dict[str, Any] = {
            "face_detected": False,
            "current_y": None,
            "face_rect": None,
            "status": "No Face",
            "warning": False,
            "posture_score": 100,     # 0–100 arasi puan
            "deviation": 0,
        }

        annotated_frame = frame.copy()
        gray = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
        )

        if len(faces) == 0:
            return annotated_frame, metrics

        # En buyuk yuz
        faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, w, h = faces_sorted[0]

        center_y = y + h // 2
        center_x = x + w // 2

        metrics["face_detected"] = True
        metrics["current_y"] = center_y
        metrics["face_rect"] = (x, y, w, h)

        if self.reference_y is None:
            metrics["status"] = "No Ref"
            box_color = COLOR_INFO
            cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), box_color, 2)
            cv2.circle(annotated_frame, (center_x, center_y), 5, COLOR_INFO, -1)
            return annotated_frame, metrics

        deviation = center_y - self.reference_y
        metrics["deviation"] = deviation

        # Puan: sapma ne kadar buyukse puan o kadar dusuk
        score = max(0, 100 - int(abs(deviation) / self._MAX_DEVIATION * 100))
        metrics["posture_score"] = score

        if deviation > DEVIATION_THRESHOLD:
            # Asagi sapma — kotu durus
            metrics["status"] = "Bad"
            metrics["warning"] = True
            box_color = COLOR_BAD
        elif deviation < -DEVIATION_UP_THRESHOLD:
            # Yukari sapma — ekrana yaklasma
            metrics["status"] = "Up"
            metrics["warning"] = True
            box_color = COLOR_WARN
        elif abs(deviation) > DEVIATION_THRESHOLD // 2:
            metrics["status"] = "Warning"
            box_color = COLOR_WARN
        else:
            metrics["status"] = "Good"
            box_color = COLOR_OK

        # Yuz cercevesi
        cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), box_color, 2)
        cv2.circle(annotated_frame, (center_x, center_y), 5, box_color, -1)

        # Referans cizgisi
        cv2.line(
            annotated_frame,
            (0, self.reference_y),
            (annotated_frame.shape[1], self.reference_y),
            (80, 80, 200),
            1,
            cv2.LINE_AA,
        )
        # Mevcut konum cizgisi
        cv2.line(
            annotated_frame,
            (0, center_y),
            (annotated_frame.shape[1], center_y),
            box_color,
            1,
            cv2.LINE_AA,
        )

        return annotated_frame, metrics
