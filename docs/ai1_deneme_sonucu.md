# AI-1 fizibilite denemesi: sonuç olumsuz

Tarih: 24.11.2026 · Script: `prototip/ai1_deneme.py` · Ham sonuç: `prototip/cikti/ai1_deneme_sonuc.json`

## Soru
Bir ayın sonunda, o güne kadarki iklim verisine bakarak 1–3 ay sonrasının sulama ihtiyacını, basit kıyaslardan daha iyi tahmin edebilir miyiz?

## Kurulum
- **İller:** 10 il. Ankara, İzmir, İstanbul, Antalya, Konya, Adana, Diyarbakır, Erzurum, Kayseri, Bursa. Open-Meteo'nun saatlik sınırı nedeniyle planlanan 20 ilin yarısı kullanıldı.
- **Veri:** ERA5, 1981–2025/09.
- **Hedef:** Nisan–Ekim aylarının net sulama ihtiyacı, Kc = 1 için. Ortalama 122 mm/ay.
- **Model:** Tüm iller için tek bir LightGBM. Girdiler: son 3 ayın ET₀, yağış, sıcaklık ve ihtiyaç sapmaları; 3 ve 6 aylık yağış birikimi; ay; konum.
- **Eğitim ve test:** Eğitim 1991–2014, test 2015–2025. Toplam 760 test örneği. Güven aralığı test yıllarından bootstrap ile hesaplandı.

## Sonuç (ortalama mutlak hata, mm/ay; düşük olan iyi)
| Ufuk | Model | Son 10 yıl ortalaması | 1991–2014 ortalaması | "Sapma sürer" |
|---|---|---|---|---|
| 1 ay | 26,2 | **24,8** | 26,0 | 33,0 |
| 2 ay | 26,6 | **24,8** | 26,0 | 33,0 |
| 3 ay | 26,0 | **24,8** | 26,0 | 33,6 |

- **Model, son 10 yıl ortalamasını geçemiyor.** Skill −%5 ile −%7 arasında. %90 güven aralığı tamamen eksi tarafta: 1 ayda [−%9, −%2].
- **Sabit 1991–2014 ortalamasıyla başa baş.** Skill ≈ 0.
- **Yaz bütçesi testinde de aynı sonuç.** Mayıs sonunda Haziran–Ağustos toplamı tahmin edildi (ortalama 516 mm). Model 47,0 mm, son 10 yıl ortalaması 45,4 mm hata yaptı.
- **İl bazında yalnız Diyarbakır'da** çok küçük bir kazanç var (+%2,5). Diğer 9 ilde model kaybediyor.

## Yorum
1. **Yerel iklim geçmişinde 1–3 ay sonrasına dair sinyal yok.** Geçen ayın sıcak ya da kurak geçmesi önümüzdeki ayı öngörmüyor. "Sapma sürer" tahmini klimatolojiden %33 kötü.
2. **Isınma trendi gerçek ve önemli.** Son 10 yılın ortalaması, eski 1991–2014 normalinden %5 daha iyi tahmin ediyor. Eski normallerle yapılan planlama sulama ihtiyacını düşük gösteriyor.
3. **Bu sonuç literatürle uyumlu.** Türkiye'de mevsimsel tahminin klimatolojiyi geçtiğine dair bir kanıt bulamamıştık (Çamalan & Akıl 2025). Ancak bizim testimiz geçmiş iklim verisiyle sınırlı. ECMWF'nin mevsimsel tahminiyle (SEAS5) bir test yapamadık, çünkü Open-Meteo bu tahminlerin geçmişini 2025-09 öncesi için vermiyor.

## Ne değişiyor?
- **AI-1 bu haliyle bırakılmalı.** "Yapay zekâ gelecek sezonu tahmin ediyor" iddiası savunulamaz.
- **Panelde "önümüzdeki sezon" tahmini için son 10 yıl ortalaması kullanılmalı.** Test edilen yöntemler arasında en iyisi bu.
- **Jüriye bu sonuç olumsuz değil, dürüst bir bulgu olarak anlatılabilir:** "Denedik, ölçtük; basit son 10 yıl normali daha iyi. Bu yüzden onu kullanıyoruz. Eski normallerle plan yapan belediye ihtiyacı %5 düşük öngörüyor."
- **Projenin AI katkısı başka yerde aranmalı:**
  - Uydudan sulanan çim tespiti (AI-3): gerçek bir sınıflandırma görevi, literatürde %96 doğruluk var.
  - Kısıtlı bitki karışımı optimizasyonu (AI-2).

## Açık kalanlar
- Kalan 10 il eklenip test tekrarlanabilir. Sonucun değişmesi beklenmez, ama kapsamı genişletir.
- SEAS5 geçmiş tahminleri Copernicus CDS'de var (1993–2016), ama kayıt gerektiriyor. Bunlarla bir test, AI-1'i kurtarabilecek tek yol.
