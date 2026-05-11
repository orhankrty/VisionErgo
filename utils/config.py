"""
VisionErgo — Merkezi Yapilandirma Modulü
Tum uygulama parametrelerini tek bir yerden yonetin.
"""

# -----------------------------------------------------------------------
# Uygulama Bilgileri
# -----------------------------------------------------------------------
APP_NAME = "VisionErgo"
VERSION  = "2.1.0"

# -----------------------------------------------------------------------
# Kamera Ayarlari
# -----------------------------------------------------------------------
CAMERA_INDEX      = 0
CAMERA_RESOLUTION = (1280, 720)   # (genislik, yukseklik)
CAMERA_WARMUP_FRAMES = 20         # Baslangicta atlanan kare sayisi (otomatik pozlama)

# -----------------------------------------------------------------------
# Durus Analizi
# -----------------------------------------------------------------------
DEVIATION_THRESHOLD    = 30   # piksel — asagi sapma siniri (kotu durus)
DEVIATION_UP_THRESHOLD = 25   # piksel — yukari sapma siniri (ekrana yaklasma)

# -----------------------------------------------------------------------
# Goz Kirpma Tespiti
# -----------------------------------------------------------------------
BLINK_HISTORY_DURATION   = 60.0   # saniye — BPM hesaplama penceresi
LOW_BLINK_THRESHOLD      = 12     # BPM — kuru goz uyarisi
CRITICAL_BLINK_THRESHOLD = 8      # BPM — ciddi kuru goz uyarisi

# -----------------------------------------------------------------------
# Ses Uyari Sistemi
# -----------------------------------------------------------------------
ALERT_ENABLED            = True
ALERT_BAD_POSTURE_COOLDOWN = 30.0   # saniye — kotu durus uyarilari arasi minimum sure
ALERT_DRY_EYE_COOLDOWN    = 60.0   # saniye — kuru goz uyarilari arasi minimum sure

# -----------------------------------------------------------------------
# Oturum Kaydedici
# -----------------------------------------------------------------------
SESSION_LOG_ENABLED  = True
SESSION_LOG_DIR      = "logs"
SESSION_LOG_INTERVAL = 5.0   # saniye — CSV'ye yazma sikligi

# -----------------------------------------------------------------------
# HUD Tasarimi  (BGR renk paleti)
# -----------------------------------------------------------------------
COLOR_OK    = (80,  220,  80)    # Yesil
COLOR_WARN  = (0,   210, 255)    # Amber/Sari
COLOR_BAD   = (60,   60, 230)    # Kirmizi
COLOR_INFO  = (255, 200,  40)    # Mavi-Sari
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0,     0,   0)
COLOR_PANEL = (18,   18,  18)    # Koyu arka plan

PANEL_ALPHA = 0.60
FONT        = 0    # cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD   = 2    # cv2.FONT_HERSHEY_DUPLEX
