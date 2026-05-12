<div align="center">
  <h1>🛡️ VisionErgo</h1>
  <h3>Bütünleşik Dijital Sağlık ve Ergonomi Takipçisi</h3>
  
  <p>
    Masa başı çalışanlar için "PostureGuard" (Duruş Takibi) ve "BlinkAlert" (Göz Kırpma Takibi) sistemlerini tek bir çatıda birleştiren, <b>Grounded (tamamen yerel çalışan)</b> bir dijital sağlık asistanıdır.
  </p>

  <p>
    <i>BTK Akademi & Samsun Teknopark işbirliğiyle gerçekleştirilen <b>Yapay Zekâ Destekli Görüntü İşleme Atölyesi</b> projesidir.</i>
  </p>

  <p>
    <a href="#problem-ve-ihtiyaç">Problem</a> •
    <a href="#özellikler-key-features">Özellikler</a> •
    <a href="#teknik-metodoloji">Metodoloji</a> •
    <a href="#kurulum-ve-kullanım">Kurulum</a> •
    <a href="#klasör-yapısı">Mimari</a>
  </p>
</div>

---

## 📌 Problem ve İhtiyaç

Günümüzde uzun süreli bilgisayar kullanımı, ciddi fiziksel ve görsel sağlık sorunlarına yol açmaktadır:
* **Slouching (Kötü Duruş):** Ekran başında farkında olmadan öne eğilmek veya kambur durmak, kronik bel ve boyun ağrılarına zemin hazırlar.
* **CVS (Computer Vision Syndrome - Dijital Göz Yorgunluğu):** Bilgisayar ekranına odaklanırken göz kırpma sayısının azalması, göz kuruluğu, tahriş ve uzun vadeli görme bozukluklarına (dijital göz yorgunluğu) neden olur.

**VisionErgo**, bu iki temel problemi bilgisayarlı görü (Computer Vision) teknikleriyle eşzamanlı olarak tespit etmek ve kullanıcıyı gerçek zamanlı olarak uyarmak amacıyla geliştirilmiştir.

## ✨ Özellikler (Key Features)

- 📐 **Gerçek Zamanlı Postür Analizi (PostureGuard):** Kullanıcının dikey eksendeki sapmalarını anlık olarak takip ederek ideal duruşun bozulduğu durumlarda algılar.
- 👁️ **Blink Rate / BPM Takibi (BlinkAlert):** Dakikadaki göz kırpma sayısını ölçer. Düşük kırpma frekanslarında kullanıcıyı uyararak göz sağlığını korur.
- 🔒 **Tamamen Yerel Çalışma (Grounded):** Hiçbir harici yapay zeka API'sine (OpenAI, Hugging Face vb.) veya bulut servisine ihtiyaç duymaz. Tüm görüntü işleme süreçleri kullanıcının cihazında (edge) çalışır ve veri gizliliğini (Privacy-First) maksimum seviyede tutar.
- 🔔 **Dinamik Görsel Geri Bildirim:** Hatalı duruş veya düşük göz kırpma oranlarında, ekran üzerinde (HUD) kesintisiz ve dinamik görsel uyarılar sağlar.

## 🔬 Teknik Metodoloji (Nasıl Çalışır?)

Proje, derin öğrenme (Deep Learning) modelleri yerine, performans ve gizlilik odaklı **saf görüntü işleme (Pure Image Processing)** algoritmaları üzerine inşa edilmiştir.

### Postür Mantığı (Posture Tracking)
Kullanıcının ideal oturma pozisyonundaki referans kafa yüksekliği ($H_{ref}$) sistem tarafından kaydedilir. Sonrasında, anlık kafa yüksekliği ($H_{current}$) sürekli olarak ölçülür. $|H_{ref} - H_{current}| > \text{Tolerans}$ durumunda postür ihlali tespit edilir.

### Göz Kırpma Mantığı (Blink Detection)
Göz bölgesi (ROI - Region of Interest) tespit edildikten sonra **Otsu Eşikleme (Otsu's Thresholding)** uygulanır. Ardışık kareler (frames) arasındaki piksellerin zamansal değişim varyansları analiz edilerek göz kapanma/açılma eylemleri matematiksel olarak belirlenir.

### 🛠️ Kullanılan Teknolojiler
- **Python:** Temel geliştirme dili.
- **OpenCV (Haar Cascades):** Görüntü yakalama, yüz/göz tespiti ve ROI işlemleri.
- **NumPy:** Matris operasyonları ve matematiksel hesaplamalar.
- **Matplotlib:** (Opsiyonel) Veri analizi ve performans takibi grafiklendirmeleri.

## 🚀 Kurulum ve Kullanım

Sistemi yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz.

### 1. Gereksinimleri Yükleyin
Proje dizininde bir terminal açın ve gerekli kütüphaneleri kurun:
```bash
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatın
Ana modülü çalıştırarak sistemi başlatın:
```bash
python main.py
```
*Sistem başlatıldığında ilk birkaç saniye dik durarak kameraya bakınız. Bu süre zarfında referans duruşunuz ($H_{ref}$) hesaplanacaktır.*

## 📂 Klasör Yapısı

Proje, modüler ve sürdürülebilir bir mimari ile tasarlanmıştır:

```text
VisionErgo/
│
├── core/         # Ana iş mantığı (Posture ve Blink algoritmaları, Kamera Capture)
├── utils/        # Yardımcı fonksiyonlar (Çizim, Metrik hesaplama vb.)
├── logs/         # Oturum verileri ve performans logları
├── assets/       # Cascade modelleri (haarcascade_frontalface.xml vb.), sesler ve görseller
├── main.py       # Uygulamanın giriş noktası
└── requirements.txt
```

## 🎓 Akademik Vurgu

Bu proje, **BTK Akademi & Samsun Teknopark** işbirliğiyle gerçekleştirilen **Yapay Zekâ Destekli Görüntü İşleme Atölyesi** kapsamında geliştirilmiştir. Çalışma, karmaşık siyah-kutu (black-box) yapay zeka modellerinden bağımsız olarak, literatürdeki temel ve sağlam (robust) görüntü işleme algoritmalarının pratik bir probleme uyarlanmasını hedefler. Proje mimarisi akademik titizlikle yapılandırılmış olup, deterministik ve analiz edilebilir metodolojilere dayanmaktadır.

---
<div align="center">
  <i>Sağlıklı günler ve iyi çalışmalar dileriz.</i>
</div>
