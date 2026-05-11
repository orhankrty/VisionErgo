"""
VisionErgo — Goz Kirpma Tespiti  (v2.1)

Algoritma (kademeli):
    1. Haar Cascade (haarcascade_eye.xml) ile goz tespiti denenr.
    2. Cascade basarisiz olursa CLAHE + adaptif esikleme ile yuz ROI
       icerisindeki sol/sag goz bolgelerinde koyu piksel takibi yapilir
       (gozluk olsun ya da olmasin calisir).
    3. Her iki yontem de koyu piksel oranindaki ani dusumu kirpma olarak
       isaretler; hareketli ortalama (EMA) ile gercek kirpma / yanlisl
       alarm ayrilir.
"""

import cv2
import numpy as np
import time
import logging
from typing import Tuple, Dict, Any, Optional, List

from utils.config import (
    BLINK_HISTORY_DURATION,
    LOW_BLINK_THRESHOLD,
    CRITICAL_BLINK_THRESHOLD,
    COLOR_OK, COLOR_WARN, COLOR_BAD,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Yardimci: CLAHE nesnesi (paylasilir, tekrar olusturulmaz)
# ---------------------------------------------------------------------------
_CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


def _enhance(gray: np.ndarray) -> np.ndarray:
    """CLAHE ile goruntu kontrastini arttirir."""
    return _CLAHE.apply(gray)


class BlinkDetector:
    """
    Goz kirpma sayar ve BPM + uyari seviyesi uretir.

    Ozellikler:
        - Haar Cascade (birincil) + bolge tabanli koyu piksel analizi (yedek)
        - CLAHE on islemi: dim/aydinlik ortamda tutarli performans
        - Uzun donem EMA: aydinlatma degisimlerine uyum saglar
        - BPM hesabi: kayan 60 sn pencere
        - Toplam kirpma sayaci (oturum geneli)
    """

    # Cascade icin kullanilacak dosyalar (oncelik sirasi)
    _EYE_CASCADES = [
        "haarcascade_eye.xml",
        "haarcascade_eye_tree_eyeglasses.xml",
    ]

    def __init__(self) -> None:
        # --- Cascade yukle ---
        self.eye_cascade: Optional[cv2.CascadeClassifier] = None
        for fname in self._EYE_CASCADES:
            path = cv2.data.haarcascades + fname
            clf = cv2.CascadeClassifier(path)
            if not clf.empty():
                self.eye_cascade = clf
                logger.info(f"Goz cascade yuklendi: {fname}")
                break

        if self.eye_cascade is None:
            logger.warning("Hic goz cascade yuklenemedi; yalnizca bolge tabanli mod kullanilacak.")

        # --- Durum degiskenleri ---
        self.blink_timestamps: List[float] = []
        self.is_closed: bool = False
        self.ema_ratio: Optional[float] = None          # Uzun donem EMA
        self.baseline_ratio: Optional[float] = None      # Acik goz referansi
        self.total_blinks: int = 0

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def analyze(
        self,
        frame: np.ndarray,
        face_rect: Optional[Tuple[int, int, int, int]],
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Kare uzerinde goz kirpma analizi yapar.

        Returns:
            annotated_frame, metrics
            metrics keys: bpm, blink_detected, eyes_closed, alert_level, total_blinks
        """
        metrics: Dict[str, Any] = {
            "bpm": 0,
            "blink_detected": False,
            "eyes_closed": False,
            "alert_level": "ok",
            "total_blinks": self.total_blinks,
        }

        annotated = frame.copy()
        now = time.time()

        # BPM penceresi guncelle
        self.blink_timestamps = [t for t in self.blink_timestamps if now - t <= BLINK_HISTORY_DURATION]
        bpm = len(self.blink_timestamps)
        metrics["bpm"] = bpm
        metrics["alert_level"] = self._alert_level(bpm)

        if face_rect is None:
            return annotated, metrics

        x, y, w, h = face_rect
        # Goz bolgesini al: yuzun ust %10-%55'i (kaslar dahil degil)
        ey_start = y + int(h * 0.10)
        ey_end   = y + int(h * 0.55)
        eye_band = frame[ey_start:ey_end, x: x + w]

        if eye_band.size == 0:
            return annotated, metrics

        gray_band = cv2.cvtColor(eye_band, cv2.COLOR_BGR2GRAY)
        enhanced  = _enhance(gray_band)

        ratio, eye_rects = self._extract_ratio(enhanced, x, ey_start)

        # Goz kutucuklarini ciz
        box_color = {"ok": COLOR_OK, "low": COLOR_WARN, "critical": COLOR_BAD}.get(
            metrics["alert_level"], COLOR_OK
        )
        for (rx, ry, rw, rh) in eye_rects:
            cv2.rectangle(annotated, (rx, ry), (rx + rw, ry + rh), box_color, 2)

        if ratio is None:
            return annotated, metrics

        # EMA guncelle
        if self.ema_ratio is None:
            self.ema_ratio = ratio
            self.baseline_ratio = ratio
        else:
            if ratio >= self.ema_ratio * 0.75:          # goz acik ya da yari acik
                self.ema_ratio = 0.92 * self.ema_ratio + 0.08 * ratio
                # Baseline: yalnizca acik gozde guncelle
                if self.baseline_ratio is None:
                    self.baseline_ratio = self.ema_ratio
                else:
                    self.baseline_ratio = 0.98 * self.baseline_ratio + 0.02 * self.ema_ratio

        # Kirpma kararı: orani baslang icin %65'in altina dustuyse
        threshold = (self.baseline_ratio or self.ema_ratio) * 0.65
        if ratio < threshold:
            metrics["eyes_closed"] = True
            if not self.is_closed:
                self.is_closed = True
                self.blink_timestamps.append(now)
                self.total_blinks += 1
                metrics["blink_detected"] = True
                metrics["total_blinks"] = self.total_blinks
                logger.info(f"Kirpma | BPM={bpm+1} | Toplam={self.total_blinks}")
        else:
            self.is_closed = False

        return annotated, metrics

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _extract_ratio(
        self,
        enhanced: np.ndarray,
        frame_x: int,
        frame_y: int,
    ) -> Tuple[Optional[float], list]:
        """
        Haar Cascade ile goz tespit eder; basarisiz olursa
        yuz bandini sol/sag yari olarak boler ve her birinde
        en koyu bolgede koyu piksel oranini hesaplar.

        Returns:
            ratio (float | None): Ortalama koyu piksel orani.
            eye_rects (list): Gercek koordinatlarda goz kutucuklari.
        """
        eye_rects: list = []
        dark_ratios: List[float] = []

        # ---------- Birincil: Haar Cascade ----------
        if self.eye_cascade is not None:
            eyes = self.eye_cascade.detectMultiScale(
                enhanced, scaleFactor=1.08, minNeighbors=4, minSize=(20, 20)
            )
            if len(eyes) > 0:
                # En fazla 2 goz al (sol + sag)
                eyes_sorted = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
                for ex, ey, ew, eh in eyes_sorted:
                    roi = enhanced[ey: ey + eh, ex: ex + ew]
                    _, thr = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    dark_ratios.append(cv2.countNonZero(thr) / (ew * eh))
                    eye_rects.append((frame_x + ex, frame_y + ey, ew, eh))

                if dark_ratios:
                    return sum(dark_ratios) / len(dark_ratios), eye_rects

        # ---------- Yedek: Bolge tabanli koyu piksel takibi ----------
        bh, bw = enhanced.shape[:2]
        # Sol ve sag yarida birer kucuk merkez bolge al
        zones = [
            enhanced[bh // 4: 3 * bh // 4, bw // 8:     bw // 2 - bw // 8],   # sol goz
            enhanced[bh // 4: 3 * bh // 4, bw // 2 + bw // 8: 7 * bw // 8],   # sag goz
        ]
        for zone in zones:
            if zone.size == 0:
                continue
            _, thr = cv2.threshold(zone, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            dark_ratios.append(cv2.countNonZero(thr) / zone.size)

        ratio = sum(dark_ratios) / len(dark_ratios) if dark_ratios else None
        return ratio, eye_rects

    @staticmethod
    def _alert_level(bpm: int) -> str:
        if bpm < CRITICAL_BLINK_THRESHOLD:
            return "critical"
        if bpm < LOW_BLINK_THRESHOLD:
            return "low"
        return "ok"
