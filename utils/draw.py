"""
VisionErgo — HUD Cizim Yardimci Modulü
Ekran uzerine profesyonel, okunaklı metin ve panel cizimleri saglar.
"""

import cv2
import numpy as np
from typing import Tuple

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.config import (
    COLOR_BLACK, COLOR_WHITE, COLOR_PANEL, PANEL_ALPHA,
    FONT, FONT_BOLD
)


def draw_text_outlined(
    frame: np.ndarray,
    text: str,
    pos: Tuple[int, int],
    font_scale: float = 0.75,
    color: Tuple[int, int, int] = COLOR_WHITE,
    thickness: int = 2,
    outline_thickness: int = 4,
) -> None:
    """
    Siyah kontur uzerine renkli metin cizer.
    Tum arka planlarda okunabilir.
    """
    x, y = pos
    # Disard
    cv2.putText(frame, text, (x, y), FONT, font_scale, COLOR_BLACK, outline_thickness, cv2.LINE_AA)
    # Icerik
    cv2.putText(frame, text, (x, y), FONT, font_scale, color, thickness, cv2.LINE_AA)


def draw_panel(
    frame: np.ndarray,
    x: int, y: int,
    w: int, h: int,
    color: Tuple[int, int, int] = COLOR_PANEL,
    alpha: float = PANEL_ALPHA,
    radius: int = 8,
) -> None:
    """
    Yari saydam, yuvarlatilmis koseli bir dikdortgen panel cizer.
    """
    overlay = frame.copy()
    # Yuvarlatilmis dikdortgen
    cv2.rectangle(overlay, (x + radius, y), (x + w - radius, y + h), color, -1)
    cv2.rectangle(overlay, (x, y + radius), (x + w, y + h - radius), color, -1)
    cv2.circle(overlay, (x + radius,     y + radius),     radius, color, -1)
    cv2.circle(overlay, (x + w - radius, y + radius),     radius, color, -1)
    cv2.circle(overlay, (x + radius,     y + h - radius), radius, color, -1)
    cv2.circle(overlay, (x + w - radius, y + h - radius), radius, color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def draw_separator(
    frame: np.ndarray,
    x: int, y: int, w: int,
    color: Tuple[int, int, int] = (80, 80, 80),
) -> None:
    """Panelin icinde yatay ayirici cizgi cizer."""
    cv2.line(frame, (x, y), (x + w, y), color, 1, cv2.LINE_AA)


def draw_progress_bar(
    frame: np.ndarray,
    x: int, y: int,
    w: int, h: int,
    value: float,           # 0.0 — 1.0
    color_fg: Tuple[int, int, int] = (80, 220, 80),
    color_bg: Tuple[int, int, int] = (50, 50, 50),
    radius: int = 4,
) -> None:
    """
    Yatay ilerleme cubugu cizer.

    Args:
        value: 0.0 (bos) ile 1.0 (dolu) arasinda deger.
    """
    value = max(0.0, min(1.0, value))
    # Arka plan
    cv2.rectangle(frame, (x, y), (x + w, y + h), color_bg, -1)
    # On plan (doluluk)
    fill_w = int(w * value)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x + fill_w, y + h), color_fg, -1)
    # Cerceve
    cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 100, 100), 1)


def draw_dot(
    frame: np.ndarray,
    x: int, y: int,
    color: Tuple[int, int, int],
    radius: int = 5,
) -> None:
    """Kucuk durum noktasi (status dot) cizer."""
    cv2.circle(frame, (x, y), radius, COLOR_BLACK, -1)
    cv2.circle(frame, (x, y), radius - 1, color, -1)
