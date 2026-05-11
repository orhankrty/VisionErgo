"""
VisionErgo v2.1 — Ana Uygulama
Premium HUD | Ses Uyarilari | CSV Oturum Kaydı | FPS Gostergesi
"""

import sys
import os
import logging
import cv2
import numpy as np

from core.monitor import ErgoMonitor
from utils.config import (
    APP_NAME, VERSION,
    COLOR_OK, COLOR_WARN, COLOR_BAD, COLOR_INFO,
    COLOR_WHITE, COLOR_BLACK,
)
from utils.draw import (
    draw_text_outlined,
    draw_panel,
    draw_separator,
    draw_progress_bar,
    draw_dot,
)
from utils.alerts import AlertManager
from utils.session_logger import SessionLogger

# ---------------------------------------------------------------------------
# Loglama
# ---------------------------------------------------------------------------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/visionergo.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

WINDOW_TITLE = f"{APP_NAME}  v{VERSION}"

# ---------------------------------------------------------------------------
# Terminal banner
# ---------------------------------------------------------------------------
BANNER = r"""
 ____   ____.__      .__               ___________                  
 \   \ /   /|__| ____|__| ____   ____\_   _____/______  ____  ____  
  \   Y   / |  |/  ___/  |/  _ \ /    \|    __)_\_  __ \/ ___\/  _ \ 
   \     /  |  |\___ \|  (  <_> )   |  \        \|  | \/  \__(  <_> )
    \___/   |__/____  >__|\____/|___|  /_______  /|__|  \___  >____/ 
                    \/               \/        \/            \/       
"""

# ---------------------------------------------------------------------------
# HUD yardimci fonksiyonlari
# ---------------------------------------------------------------------------

def _sc(status: str) -> tuple:
    """Durus durumuna gore BGR renk donderir."""
    return {
        "Good":    COLOR_OK,
        "Warning": COLOR_WARN,
        "Bad":     COLOR_BAD,
        "Up":      COLOR_WARN,
        "No Ref":  COLOR_INFO,
        "No Face": (100, 100, 100),
    }.get(status, COLOR_WHITE)


def _bc(alert: str) -> tuple:
    return {"ok": COLOR_OK, "low": COLOR_WARN, "critical": COLOR_BAD}.get(alert, COLOR_WHITE)


# ---------------------------------------------------------------------------
# HUD panelleri
# ---------------------------------------------------------------------------

def _draw_left_panel(frame: np.ndarray, posture: dict, stats: dict) -> None:
    """Sol ust: Durus paneli."""
    pw, ph = 310, 230
    px, py = 12, 12
    draw_panel(frame, px, py, pw, ph, alpha=0.70)

    # Baslik
    draw_text_outlined(frame, APP_NAME,      (px+12, py+28), 0.82, COLOR_INFO, 2)
    draw_text_outlined(frame, f"v{VERSION}", (px+168, py+28), 0.50, (120,120,120), 1)
    draw_separator(frame, px+8, py+38, pw-16)

    status = posture.get("status", "No Face")
    sc     = _sc(status)
    score  = posture.get("posture_score", 100)
    dev    = posture.get("deviation", 0)

    draw_dot(frame, px+20, py+62, sc)
    draw_text_outlined(frame, "DURUS DURUMU",   (px+32, py+67), 0.52, (180,180,180), 1)
    draw_text_outlined(frame, status.upper(),   (px+12, py+94), 0.82, sc, 2)

    draw_text_outlined(frame, f"Puan: {score}/100", (px+12, py+118), 0.50, (160,160,160), 1)
    draw_progress_bar(frame, px+12, py+124, pw-24, 8,
                      score/100, color_fg=sc)

    draw_separator(frame, px+8, py+145, pw-16)

    draw_text_outlined(frame, f"Sapma       : {dev:+d} px",        (px+12, py+165), 0.50, (160,160,160), 1)
    draw_text_outlined(frame, f"Sure        : {stats.get('elapsed_str','00:00')}", (px+12, py+185), 0.50, (160,160,160), 1)

    bad = int(stats.get("bad_posture_ratio", 0) * 100)
    bc  = COLOR_BAD if bad > 30 else (160,160,160)
    draw_text_outlined(frame, f"Kotu Durus  : %{bad}", (px+12, py+205), 0.50, bc, 1)


def _draw_right_panel(frame: np.ndarray, blink: dict, stats: dict) -> None:
    """Sag ust: Goz kirpma paneli."""
    pw, ph = 275, 195
    px = frame.shape[1] - pw - 12
    py = 12
    draw_panel(frame, px, py, pw, ph, alpha=0.70)

    draw_text_outlined(frame, "GOZ KIRPMA", (px+12, py+28), 0.72, COLOR_INFO, 2)
    draw_separator(frame, px+8, py+38, pw-16)

    bpm   = blink.get("bpm", 0)
    alert = blink.get("alert_level", "ok")
    bc    = _bc(alert)
    total = stats.get("total_blinks", 0)

    draw_dot(frame, px+20, py+62, bc)
    draw_text_outlined(frame, "BPM (son 60 sn)", (px+32, py+67), 0.50, (180,180,180), 1)

    # Buyuk BPM sayisi
    draw_text_outlined(frame, str(bpm), (px+12, py+106), 1.50, bc, 3)

    # Hedef: 15-20 BPM normal
    draw_progress_bar(frame, px+12, py+118, pw-24, 8, min(bpm/20, 1.0), color_fg=bc)
    draw_separator(frame, px+8, py+138, pw-16)

    draw_text_outlined(frame, f"Toplam Kirpma: {total}", (px+12, py+158), 0.52, (160,160,160), 1)

    if alert == "critical":
        draw_text_outlined(frame, "! KRU GOZ — CIDDI UYARI !", (px+12, py+180), 0.50, COLOR_BAD, 1)
    elif alert == "low":
        draw_text_outlined(frame, "Daha Sik Kirpin!", (px+12, py+180), 0.50, COLOR_WARN, 1)
    else:
        draw_text_outlined(frame, "Kirpma Normal", (px+12, py+180), 0.50, COLOR_OK, 1)


def _draw_fps(frame: np.ndarray, fps: float) -> None:
    """Sag alt kosede FPS gosterir."""
    h, w = frame.shape[:2]
    color = COLOR_OK if fps >= 20 else (COLOR_WARN if fps >= 10 else COLOR_BAD)
    draw_text_outlined(frame, f"FPS: {fps:.0f}", (w-110, h-42), 0.52, color, 1)


def _draw_posture_alert(frame: np.ndarray, status: str) -> None:
    """Kotu durus / ekrana yaklasma — merkeze buyuk uyari overlays."""
    if status not in ("Bad", "Up"):
        return

    h, w = frame.shape[:2]
    msg   = "DURUSUNU DUZELT!" if status == "Bad" else "EKRANDAN UZAKLAS!"
    color = COLOR_BAD if status == "Bad" else COLOR_WARN

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h//2 - 38), (w, h//2 + 48), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.50, frame, 0.50, 0, frame)

    (tw, _), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.3, 3)
    tx = (w - tw) // 2
    draw_text_outlined(frame, msg, (tx, h//2+22), 1.3, color, 3, 7)


def _draw_bottom_bar(frame: np.ndarray, ref_set: bool, fps: float) -> None:
    """Alt bar: kisayollar + FPS + referans durumu."""
    h, w = frame.shape[:2]
    bh   = 34
    draw_panel(frame, 0, h-bh, w, bh, alpha=0.72, radius=0)

    ref_txt   = "[S] Referans Belirle" if not ref_set else "[S] Referansi Guncelle"
    ref_color = COLOR_INFO if not ref_set else COLOR_OK

    y = h - 9
    draw_text_outlined(frame, ref_txt,        (14, y),        0.48, ref_color,    1)
    draw_text_outlined(frame, "[R] Istatistik", (280, y),     0.48, (160,160,160), 1)
    draw_text_outlined(frame, "[Q] Cikis",      (w-130, y),   0.48, (160,160,160), 1)
    draw_text_outlined(frame, f"FPS: {fps:.0f}", (w-230, y),  0.48,
                       COLOR_OK if fps >= 20 else COLOR_WARN, 1)


# ---------------------------------------------------------------------------
# Oturum raporu
# ---------------------------------------------------------------------------

def _print_report(stats: dict, log_path: str = "") -> None:
    w = 54
    print("\n" + "=" * w)
    print(f"  {APP_NAME} — Oturum Ozeti".center(w))
    print("=" * w)
    print(f"  Toplam Sure        : {stats.get('elapsed_str','00:00')}")
    print(f"  Toplam Kirpma      : {stats.get('total_blinks', 0)}")
    print(f"  Son BPM            : {stats.get('bpm', 0)}")
    bad = int(stats.get("bad_posture_ratio", 0) * 100)
    print(f"  Kotu Durus Orani   : %{bad}")
    if log_path:
        print(f"  CSV Log Dosyasi    : {log_path}")
    print("=" * w + "\n")


# ---------------------------------------------------------------------------
# Ana dongu
# ---------------------------------------------------------------------------

def main() -> None:
    print(BANNER)
    print(f"  {APP_NAME} v{VERSION}  —  Baslatiliyor...\n")

    monitor        = ErgoMonitor()
    alert_manager  = AlertManager()
    session_logger = SessionLogger()

    if not monitor.start():
        logger.error("Kamera baslatilamadi. Program sonlandiriliyor.")
        sys.exit(1)

    session_logger.start()

    print("  Sistem hazir.  Kamera isi dolduruluyor...")
    print("  [S] Referans belirle  |  [R] Istatistik  |  [Q] Cikis\n")

    # Kamera isi bitmeden bekleme ekraniisim
    warming_up = True

    try:
        while monitor.is_monitoring:
            results = monitor.process_frame()

            # --- Kamera isi ekrani ---
            if results is None:
                blank = np.zeros((480, 720, 3), dtype=np.uint8)
                draw_text_outlined(blank, "Kamera isitiiliyor...",
                                   (160, 240), 1.0, COLOR_INFO, 2, 4)
                cv2.imshow(WINDOW_TITLE, blank)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            if warming_up:
                warming_up = False
                print("  Kamera hazir. Izleme basliyor.\n")

            frame   = results.get("annotated_frame")
            posture = results.get("posture", {})
            blink   = results.get("blink", {})

            if frame is None:
                continue

            stats   = monitor.get_session_stats()
            ref_set = monitor.posture_analyzer.reference_y is not None
            fps     = monitor.camera_stream.get_fps()

            # --- Uyarilar ---
            alert_manager.check_posture(posture.get("status", ""))
            alert_manager.check_blink(blink.get("alert_level", "ok"))

            # --- Session log ---
            session_logger.record(posture, blink, stats)

            # --- HUD ---
            _draw_left_panel(frame, posture, stats)
            _draw_right_panel(frame, blink, stats)
            _draw_posture_alert(frame, posture.get("status", ""))
            _draw_bottom_bar(frame, ref_set, fps)

            cv2.imshow(WINDOW_TITLE, frame)

            # --- Klavye ---
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("  Cikis yapiliyor...")
                break

            elif key == ord("s"):
                if posture.get("face_detected"):
                    y_val = posture.get("current_y")
                    monitor.posture_analyzer.set_reference(y_val)
                    print(f"  Referans kaydedildi: Y={y_val}")
                else:
                    print("  Yuz tespit edilemedi — referans kaydedilemedi.")

            elif key == ord("r"):
                _print_report(monitor.get_session_stats(), session_logger.filepath)

    except KeyboardInterrupt:
        print("\n  Kullanici tarafindan sonlandirildi.")

    finally:
        cv2.destroyAllWindows()
        session_logger.stop()
        monitor.stop()
        _print_report(monitor.get_session_stats(), session_logger.filepath)


if __name__ == "__main__":
    main()
